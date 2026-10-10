import unittest
from backend.analysis_service import analyze_request
from test_core import export_code
from test_dependencies import build


class TargetedExclusionsTests(unittest.TestCase):
    def analyze(self, xml, assumptions=None):
        return analyze_request({'source':export_code(xml),'assumptions':assumptions or {}})

    def assert_free_in_every_preset(self, result, rules):
        for row in result['mods']:
            if row.get('rule_id') in rules:
                self.assertEqual(row['rating'],'free',row)
        for preset in result['presets'].values():
            self.assertFalse(set(rules) & set(preset['blocked_ids']))

    def test_utility_cooldown_and_one_or_two_damage_curses_are_not_safe_exclusions(self):
        for curses in [('Frostbite',),('Frostbite','Elemental Weakness')]:
            for role in ('unknown','damage','utility'):
                with self.subTest(curses=curses,role=role):
                    result=self.analyze(build('Winter Orb',stats={'Cooldown':4},utility=[*curses,'Arcane Cloak']),{'curse_role':role})
                    self.assertFalse(result['profile']['main_skill_has_cooldown'])
                    self.assertFalse(result['profile']['curse_dependent'])
                    self.assert_free_in_every_preset(result,{'reduced_cooldown','hexproof','reduced_monster_curse_effect'})

    def test_unknown_utility_gem_does_not_block_ordinary_curse_modifiers(self):
        result=self.analyze(build('Arc',utility=['Frostbite','Unsupported Utility Skill']))
        self.assert_free_in_every_preset(result,{'hexproof','reduced_monster_curse_effect'})

    def test_confirmed_mechanic_and_core_trigger_remain_excluded(self):
        result=self.analyze(build('Arc',utility=['Frostbite']),{'curse_role':'mechanic'})
        rows={row['id']:row for row in result['mods']}
        self.assertEqual(rows['hexproof']['rating'],'brick')
        self.assertEqual(rows['reduced_monster_curse_effect']['rating'],'dangerous')
        result=self.analyze(build('Cyclone',['Cast On Critical Strike'],utility=['Arcane Cloak']))
        self.assertIn('reduced_cooldown',result['presets']['greedy']['blocked_ids'])

    def test_cwc_interval_alone_is_not_a_cdr_dependency(self):
        result=self.analyze(build('Arc',['Cast while Channelling'],utility=['Cyclone']))
        self.assertFalse(result['profile']['core_trigger_cooldown'])
        self.assert_free_in_every_preset(result,{'reduced_cooldown'})
        result=self.analyze(build('Frostblink',['Cast while Channelling'],utility=['Cyclone']))
        self.assertTrue(result['profile']['main_skill_has_cooldown'])
        self.assertNotIn('reduced_cooldown',result['presets']['safe']['blocked_ids'])
        self.assertEqual(next(row for row in result['mods'] if row['id']=='reduced_cooldown')['rating'],'review')

    def test_real_winter_orb_does_not_block_utility_curses_or_cooldowns(self):
        from pathlib import Path
        result=self.analyze((Path(__file__).parent/'fixtures/winter_orb.xml').read_text(encoding='utf-8'))
        self.assert_free_in_every_preset(result,{'reduced_cooldown','hexproof','reduced_monster_curse_effect'})
