from pathlib import Path
import unittest

from backend.analysis_service import analyze_request
from backend.assessment import assessed_rule
from backend.rules import make_regex
from test_core import export_code
from test_dependencies import build


class OptionalMechanicTests(unittest.TestCase):
    def test_accuracy_stacker_optional_ailments_and_flasks_are_free(self):
        xml = (Path(__file__).parent / 'fixtures/accuracy_stacker_reave.xml').read_text(encoding='utf-8')
        result = analyze_request({'source': export_code(xml)})
        for rule in ('avoid_ailments', 'avoid_poison_bleed_impale', 'reduced_flask_charges'):
            rows = [row for row in result['mods'] if row.get('rule_id') == rule]
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(row['rating'], 'free', row['reason'])
            for preset in result['presets'].values():
                self.assertNotIn(rule, preset['blocked_ids'])

    def test_known_ailment_builds_keep_their_primary_exclusions(self):
        for name, rule in [('viper_strike_mamba', 'avoid_poison_bleed_impale')]:
            xml = (Path(__file__).parent / 'fixtures' / (name + '.xml')).read_text(encoding='utf-8')
            result = analyze_request({'source': export_code(xml)})
            mod = next(row for row in result['mods'] if row['id'] == rule)
            self.assertEqual(mod['rating'], 'brick')
        self.assertEqual(assessed_rule({'primary_ailments': ['ignite'], 'skill_metadata_known': True}, 'avoid_ailments')[0], 'brick')

    def test_unmeasured_specialized_ailment_setup_stays_review(self):
        result = analyze_request({'source': export_code(build('Reave of Refraction', ['Chance to Poison']))})
        row = next(row for row in result['mods'] if row['id'] == 'avoid_poison_bleed_impale')
        self.assertEqual(row['rating'], 'review')

    def test_marginal_loss_alone_never_automatically_blocks(self):
        mods = [{'id': 'minor', 'rating': 'uncomfortable', 'pattern': 'minor'}]
        for preset in ('safe', 'balanced', 'greedy'):
            self.assertEqual(make_regex(mods, preset)['blocked_ids'], [])
        mods[0]['strict_avoid'] = True
        self.assertEqual(make_regex(mods, 'safe')['blocked_ids'], ['minor'])
        self.assertEqual(make_regex(mods, 'balanced')['blocked_ids'], [])
        self.assertEqual(make_regex(mods, 'safe', {'minor': 'allow'})['blocked_ids'], [])
        mods[0]['combination_avoid'] = True
        self.assertEqual(make_regex(mods, 'balanced')['blocked_ids'], ['minor'])

    def test_essential_flask_confirmation_still_blocks(self):
        self.assertEqual(assessed_rule({'assumptions': {'flask_essential': True}}, 'reduced_flask_charges')[0], 'brick')
        self.assertEqual(assessed_rule({'assumptions': {'flask_essential': False}}, 'reduced_flask_charges')[0], 'free')
