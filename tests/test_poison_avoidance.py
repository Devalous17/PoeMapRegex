from pathlib import Path
import unittest

from analysis_service import analyze_request
from assessment import assessed_rule
from pob import build_profile, decode_build
from rules import classify, make_regex
from test_core import export_code
from test_dependencies import build

class PoisonAvoidanceTests(unittest.TestCase):
    def test_real_mamba_build_blocks_correct_modifier_in_greedy(self):
        xml = (Path(__file__).parent/'fixtures/viper_strike_mamba.xml').read_text(encoding='utf-8')
        result = analyze_request({'source': export_code(xml)})
        p = result['profile']
        mods = {row['id']: row for row in result['mods']}
        self.assertEqual(p['main_skill'], 'Viper Strike of the Mamba')
        self.assertIn('poison', p['primary_ailments'])
        self.assertTrue(p['single_poison_main_skill'])
        self.assertEqual(mods['map--627831782']['rating'], 'brick')
        self.assertEqual(mods['map--627831782']['assessment_status'], 'counter')
        self.assertEqual(mods['avoid_ailments']['rating'], 'free')
        for preset in ['greedy', 'balanced', 'safe']:
            self.assertIn('avoid_poison_bleed_impale', result['presets'][preset]['blocked_ids'])
        self.assertIn('single_poison', {row['id'] for row in p['dependencies']})
        self.assertNotIn('176%', ' '.join(row['evidence'] for row in p['dependencies']))
        allowed = make_regex(result['mods'], 'greedy', {'avoid_poison_bleed_impale': 'allow'})
        self.assertNotIn('avoid_poison_bleed_impale', allowed['blocked_ids'])

    def test_primary_poison_and_bleed_are_conservatively_blocked_not_immunity(self):
        for skill, stat in [('Blade Vortex', 'PoisonDPS'), ('Lacerate of Haemorrhage', 'BleedDPS')]:
            with self.subTest(skill=skill):
                p = build_profile(decode_build(export_code(build(skill, stats={'TotalDPS': 1000, stat: 900}))))
                self.assertEqual(assessed_rule(p, 'avoid_poison_bleed_impale')[0], 'brick')
                p['assumptions'] = {'map_effect_increased': 100}
                self.assertEqual(assessed_rule(p, 'avoid_poison_bleed_impale')[0], 'brick')

    def test_impale_is_checked_separately_from_ailments(self):
        p = build_profile(decode_build(export_code(build('Cyclone', stats={'TotalDPS': 1000, 'ImpaleDPS': 700}))))
        self.assertTrue(p['impale_damage_primary'])
        self.assertNotIn('impale', p['primary_ailments'])
        self.assertEqual(assessed_rule(p, 'avoid_poison_bleed_impale')[0], 'dangerous')

    def test_missing_or_secondary_damage_is_not_a_proven_brick(self):
        for stats in [{}, {'TotalDPS': 1000, 'PoisonDPS': 1}]:
            p = build_profile(decode_build(export_code(build('Viper Strike of the Mamba', stats=stats))))
            self.assertEqual(assessed_rule(p, 'avoid_poison_bleed_impale')[0], 'review')
        p = build_profile(decode_build(export_code(build('Arc', stats={'PoisonDPS': 0, 'BleedDPS': 0, 'ImpaleDPS': 0}))))
        self.assertEqual(assessed_rule(p, 'avoid_poison_bleed_impale')[0], 'free')
        p = build_profile(decode_build(export_code(build('Death Aura'))))
        self.assertEqual(assessed_rule(p, 'avoid_poison_bleed_impale')[0], 'free')

    def test_scaled_roll_is_applied_once(self):
        p = build_profile(decode_build(export_code(build('Blade Vortex', stats={'TotalDPS': 1000, 'PoisonDPS': 900}))))
        p['assumptions'] = {'map_effect_increased': 50}
        mods = {row['id']: row for row in classify(p)}
        self.assertIn('75%', mods['map--627831782']['reason'])
        self.assertEqual(mods['map--627831782']['rating'], 'brick')

    def test_uncapped_poison_total_is_used_for_dependency_evidence(self):
        p = build_profile(decode_build(export_code(build('Viper Strike of the Mamba', stats={
            'TotalDPS': 20000, 'CombinedDPS': 39000000, 'PoisonDPS': 70000000, 'WithPoisonDPS': 70020000}))))
        evidence = next(row['evidence'] for row in p['dependencies'] if row['id'] == 'poison')
        self.assertIn('100%', evidence)
        self.assertNotIn('179%', evidence)
