import unittest
from backend.assessment import assessed_rule
from backend.pob import build_profile, decode_build
from test_core import export_code
from test_dependencies import build

class OffensiveDependenciesTests(unittest.TestCase):
    def profile(self, xml):
        return build_profile(decode_build(export_code(xml)))

    def test_main_hypothermia_is_conditional_but_utility_is_not(self):
        p = self.profile(build('Ice Nova', supports=['Hypothermia']))
        self.assertTrue(p['conditional_ailment_scaling'])
        self.assertEqual(assessed_rule(p, 'avoid_ailments')[0], 'dangerous')
        p = self.profile(build('Arc').replace('</Skills>', '<Skill><Gem nameSpec="Frostbolt"/><Gem nameSpec="Hypothermia" gemId="SupportGemTest"/></Skill></Skills>'))
        self.assertFalse(p['conditional_ailment_scaling'])

    def test_equipped_heatshiver_text_and_replica_shock_are_dependencies(self):
        for text in ['Gain 30% of Cold Damage as Extra Fire Damage against Frozen Enemies',
                     'Gain 1% of Cold Damage as Extra Fire Damage per 1% Chill Effect on Enemy',
                     'Gain 1% of Lightning Damage as Extra Cold Damage per 2% Shock Effect on Enemy']:
            xml = build('Ice Nova').replace('</PathOfBuilding>', f'<Items activeItemSet="1"><Item id="1">{text}</Item><ItemSet id="1"><Slot name="Helmet" itemId="1"/></ItemSet></Items></PathOfBuilding>')
            p = self.profile(xml)
            self.assertTrue(p['conditional_ailment_scaling'])
            self.assertEqual(assessed_rule(p, 'avoid_ailments')[0], 'dangerous')
            p = self.profile(xml.replace('itemId="1"', 'itemId="2"'))
            self.assertFalse(p['conditional_ailment_scaling'])

    def test_direct_cold_dot_hypothermia_bonus_is_not_conditional(self):
        p = self.profile(build('Wintertide Brand', supports=['Hypothermia']))
        self.assertTrue(p['main_damage_is_pure_dot'])
        self.assertFalse(p['conditional_ailment_scaling'])

    def test_elemental_roll_is_scaled_once(self):
        p = self.profile(build('Fireball', stats={'TotalDPS': 1000, 'IgniteDPS': 900}))
        p['assumptions'] = {'map_effect_increased': 50}
        rating, reason = assessed_rule(p, 'avoid_ailments', 70)
        self.assertEqual(rating, 'brick')
        self.assertIn('70%', reason)
        self.assertNotIn('prevented', reason)

    def test_no_extra_crit_damage_does_not_remove_hits_or_coc(self):
        p = self.profile(build('Cyclone', supports=['Cast On Critical Strike'], stats={'CritChance':100, 'CritMultiplier':670}))
        p.update(crit_chance=100,crit_multiplier=670)
        rating, reason = assessed_rule(p, 'monster_crit_reduction', 100)
        self.assertEqual(rating,'dangerous')
        self.assertIn('14.9%',reason)
        self.assertTrue(p['uses_cast_on_crit'])
