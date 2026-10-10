import json
from pathlib import Path
import unittest

from backend.assessment import assessed_rule, critical_damage_factor, recovery_conflicts, recovery_snapshot, validate_assumptions
from backend.analysis_service import analyze_request
from backend.pob import BuildInputError, build_profile, decode_build
from backend.rules import classify, make_regex
from test_core import export_code


class MeasuredAssessmentTests(unittest.TestCase):
    def test_death_aura_snapshot_primary_damage_and_greedy_exclusion(self):
        xml = (Path(__file__).parent / 'fixtures' / 'death_aura.xml').read_text(encoding='utf-8')
        result = analyze_request({'source': export_code(xml)})
        profile = result['profile']
        self.assertEqual(profile['main_skill'], 'Death Aura')
        self.assertEqual(profile['damage_type'], 'chaos dot')
        self.assertEqual(profile['main_skill_kind'], 'non_attack')
        self.assertEqual(profile['main_hit_types'], [])
        self.assertTrue(profile['uses_auras'])
        self.assertTrue(profile['primary_damage_aura'])
        self.assertTrue(any(s['id'] == 'primary_damage_aura' for s in profile['signals']))
        mods = {m['id']: m for m in result['mods']}
        self.assertEqual(mods['reduced_auras']['rating'], 'brick')
        self.assertIn('reduced effect.*auras', result['presets']['greedy']['query'])
        for key in ['monster_crit_reduction', 'physical_thorns', 'elemental_thorns', 'less_accuracy']:
            self.assertEqual(mods[key]['rating'], 'free', mods[key]['reason'])
        profile['assumptions'] = {'aura_role': 'utility'}
        self.assertEqual(assessed_rule(profile, 'reduced_auras')[0], 'brick')

    def test_aura_presence_does_not_imply_primary_damage_dependency(self):
        for name, enabled, expected in [('Death Aura', True, True), ('Malevolence', True, True),
                ('Vaal Discipline', True, True), ('Despair', True, False),
                ('Righteous Fire', True, False), ('Malevolence', False, False)]:
            with self.subTest(skill=name, enabled=enabled):
                xml = (f'<PathOfBuilding><Build mainSocketGroup="1"/><Skills>'
                    f'<Skill><Gem nameSpec="Arc"/></Skill><Skill enabled="{str(enabled).lower()}">'
                    f'<Gem nameSpec="{name}"/></Skill></Skills></PathOfBuilding>')
                profile = build_profile(decode_build(export_code(xml)))
                self.assertEqual(profile['uses_auras'], expected)
                self.assertFalse(profile['primary_damage_aura'])
                self.assertNotEqual(assessed_rule(profile, 'reduced_auras')[0], 'brick')

    def test_storm_burst_totem_snapshot(self):
        xml = (Path(__file__).parent / 'fixtures' / 'storm_burst_totems.xml').read_text(encoding='utf-8')
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile['uses_totems'])
        self.assertTrue(profile['ancestral_bond'])
        self.assertEqual(profile['attack_archetype'], 'Spell Totems')
        self.assertEqual(profile['main_skill_kind'], 'non_attack')
        self.assertTrue(profile['mana_defence_detected'])
        mods = {row['id']: row for row in classify(profile)}
        for key in ['no_regen', 'reduced_block_and_armour']:
            self.assertEqual(mods[key]['rating'], 'brick', mods[key]['reason'])
        for key in ['reduced_cooldown', 'less_accuracy', 'avoid_ailments', 'reduced_suppression_and_evasion']:
            self.assertEqual(mods[key]['rating'], 'free', mods[key]['reason'])
        profile['ailment_damage_primary'] = True
        self.assertNotEqual({row['id']: row for row in classify(profile)}['avoid_ailments']['rating'], 'free')
        profile['uses_mines'] = True
        self.assertNotEqual({row['id']: row for row in classify(profile)}['reduced_cooldown']['rating'], 'free')

    def test_combined_block_investment_policy_threshold(self):
        profile = build_profile(decode_build(export_code()))
        profile.update(armour=0, effective_attack_block=40, effective_spell_block=35)
        self.assertEqual({row['id']: row for row in classify(profile)}['reduced_block_and_armour']['rating'], 'brick')
        profile.update(effective_attack_block=0, effective_spell_block=75)
        self.assertEqual({row['id']: row for row in classify(profile)}['reduced_block_and_armour']['rating'], 'brick')
        profile.update(effective_attack_block=40, effective_spell_block=34)
        self.assertNotEqual({row['id']: row for row in classify(profile)}['reduced_block_and_armour']['rating'], 'brick')

    def test_mana_removal_on_life_flask_is_not_mana_recovery(self):
        rows = recovery_snapshot({}, '', ['rarity: rare\ndivine life flask\nunique id: x\nremoves life recovered from mana when used'])
        mana = next(row for row in rows if row['pool'] == 'Mana' and row['channel'] == 'flask')
        self.assertEqual(mana['source'], 'not saved')
        rows = recovery_snapshot({}, '', ['rarity: rare\neternal mana flask\nunique id: x'])
        self.assertEqual(next(row for row in rows if row['pool'] == 'Mana' and row['channel'] == 'flask')['source'], 'equipped flask')

    def test_utility_totem_does_not_reclassify_main_spell(self):
        xml = '<PathOfBuilding><Build mainSocketGroup="1"/><Skills><Skill><Gem nameSpec="Arc" gemId="SkillGemArc"/></Skill><Skill><Gem nameSpec="Decoy Totem" gemId="SkillGemDecoyTotem"/></Skill></Skills></PathOfBuilding>'
        profile = build_profile(decode_build(export_code(xml)))
        self.assertFalse(profile['uses_totems'])

    def test_vaal_righteous_fire_snapshot_and_maximum_hits(self):
        xml = (Path(__file__).parent / 'fixtures' / 'vaal_righteous_fire.xml').read_text(encoding='utf-8')
        profile = build_profile(decode_build(export_code(xml)))
        self.assertEqual(profile['main_skill'], 'Vaal Righteous Fire')
        self.assertEqual(profile['damage_type'], 'fire dot')
        self.assertEqual(profile['main_skill_kind'], 'non_attack')
        self.assertEqual(profile['main_hit_types'], [])
        self.assertEqual(profile['maximum_hit_taken']['Physical'], 35112)
        self.assertEqual(profile['maximum_hit_taken']['Fire'], 232489)
        mods = {row['id']: row for row in classify(profile)}
        self.assertEqual(mods['no_regen']['rating'], 'brick')
        self.assertEqual(mods['monster_crit_reduction']['rating'], 'free')

    def test_archetype_scenarios(self):
        cases = json.loads((Path(__file__).parent / 'fixtures' / 'archetype_cases.json').read_text(encoding='utf-8'))
        for case in cases:
            with self.subTest(case=case['name']):
                rating, reason = assessed_rule(case['profile'], case['mod'])
                self.assertEqual(rating, case['expected'])
                self.assertTrue(reason)

    def test_critical_formula_is_a_loss_instead_of_a_brick(self):
        self.assertAlmostEqual(critical_damage_factor(100, 670, 30), 4.99 / 6.7)
        self.assertAlmostEqual(critical_damage_factor(100, 670, 50), 3.85 / 6.7)
        self.assertEqual(critical_damage_factor(0, 670, 50), 1)

    def test_missing_channels_are_not_zero_and_recoup_is_not_mana_per_second(self):
        channels = recovery_snapshot({'ManaRecoup': 20, 'EnergyShieldRecharge': 2000}, '', [])
        mana_regen = next(row for row in channels if row['pool'] == 'Mana' and row['channel'] == 'regeneration')
        recoup = next(row for row in channels if row['pool'] == 'Mana' and row['channel'] == 'recoup')
        self.assertIsNone(mana_regen['value'])
        self.assertEqual(recoup['unit'], '% of damage')
        self.assertEqual(recoup['value'], 20)

    def test_pool_rolls_and_increased_map_effect(self):
        profile = build_profile(decode_build(export_code()))
        profile.update(crit_chance=100, crit_multiplier=670,
                       maximum_resistances={'Fire': 90}, elemental_resistances={'Fire': 90})
        mods = {row['id']: row for row in classify(profile)}
        self.assertIn('2.20x', mods['map--477049138']['reason'])
        self.assertIn('3.00x', mods['map--2038489408']['reason'])
        self.assertIn('40%', mods['map--54649013']['reason'])
        self.assertIn('45%', mods['map-poedb-MapMonstersBaseSelfCriticalMultiplier']['reason'])
        profile['assumptions'] = {'map_effect_increased': 100}
        mods = {row['id']: row for row in classify(profile)}
        self.assertIn('3.40x', mods['map--477049138']['reason'])

    def test_measured_recovery_pair_is_blocked_by_balanced(self):
        profile = build_profile(decode_build(export_code()))
        profile.pop('recovery_channels')
        profile.pop('saved_mana_cost_per_second')
        profile.update(life=5000, energy_shield=0, life_regen=0, life_leech=0,
                       mana_regen=100, mana_leech=100, mana_cost_per_second=80)
        conflicts = recovery_conflicts(profile)
        self.assertEqual(conflicts[0]['mods'], ['no_regen', 'no_leech'])
        mods = classify(profile)
        self.assertEqual(next(row for row in mods if row['id'] == 'no_regen')['rating'], 'free')
        self.assertIn('cannot regen', make_regex(mods, 'balanced')['query'])
        self.assertNotIn('cannot regen', make_regex(mods, 'greedy')['query'])

    def test_request_validates_confirmations_and_local_and_hosted_use_same_service(self):
        result = analyze_request({'source': export_code(), 'assumptions': {'hexproof_bypass': True}})
        self.assertEqual(next(row for row in result['mods'] if row['id'] == 'hexproof')['rating'], 'free')
        for assumptions in [{'mana_alternative_per_second': -1}, {'map_effect_increased': float('nan')},
                            {'curse_role': []}, {'flask_essential': 'yes'}, {'unknown': True}]:
            with self.subTest(assumptions=assumptions), self.assertRaises(BuildInputError):
                analyze_request({'source': export_code(), 'assumptions': assumptions})
        with self.assertRaises(BuildInputError):
            analyze_request([])

    def test_leech_cap_estimate_cannot_prove_a_brick(self):
        profile = {'life': 5000, 'life_regen': 0, 'life_leech': 1000,
                   'mana_regen': 0, 'mana_leech': 100, 'mana_cost_per_second': 80}
        rating, reason = assessed_rule(profile, 'reduced_leech')
        self.assertEqual(rating, 'dangerous')
        self.assertIn('additive cap modifiers', reason)

    def test_energy_shield_self_drain_pair_is_checked(self):
        profile = {'life': 1, 'energy_shield': 5000, 'energy_shield_regen': 100,
                   'energy_shield_leech': 100, 'energy_shield_net_regen': 20,
                   'mana_regen': 0, 'mana_leech': 0, 'mana_cost_per_second': 0}
        conflicts = recovery_conflicts(profile)
        self.assertEqual(conflicts[0]['mods'], ['no_regen', 'no_leech'])
        self.assertIn('EnergyShield', conflicts[0]['reason'])

    def test_resistance_cap_requires_evidence(self):
        profile = build_profile(decode_build(export_code()))
        self.assertIsNone(profile['maximum_resistances']['Fire'])
        self.assertEqual(assessed_rule(profile, 'minus_max_res')[0], 'review')
        xml = '<PathOfBuilding><Build><PlayerStat stat="FireResist" value="90"/><PlayerStat stat="FireResistOverCap" value="10"/></Build></PathOfBuilding>'
        profile = build_profile(decode_build(export_code(xml)))
        self.assertEqual(profile['maximum_resistances']['Fire'], 90)

    def test_saved_character_snapshots(self):
        for name, expected in [('winter_orb', {'no_regen': 'review', 'monster_crit_reduction': 'dangerous', 'extra_chaos': 'free'}),
                               ('armour_stacker', {'no_leech': 'brick', 'reduced_block_and_armour': 'brick'}),
                               ('righteous_fire', {'no_regen': 'brick', 'extra_chaos': 'free'})]:
            with self.subTest(build=name):
                xml = (Path(__file__).parent / 'fixtures' / (name + '.xml')).read_text(encoding='utf-8')
                profile = build_profile(decode_build(export_code(xml)))
                mods = {row['id']: row for row in classify(profile)}
                for mod, rating in expected.items():
                    self.assertEqual(mods[mod]['rating'], rating, mods[mod]['reason'])
