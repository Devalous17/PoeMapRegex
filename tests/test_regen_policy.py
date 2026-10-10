import unittest
from backend.assessment import recovery_assessment


class RegenPolicyTests(unittest.TestCase):
    def profile(self, **updates):
        result=dict(life=10000,energy_shield=0,life_regen=4306.1,life_leech=0,life_net_regen=2698.75526)
        result.update(updates)
        return result

    def test_substantial_regeneration_is_balanced_even_when_it_covers_drain(self):
        rating,reason=recovery_assessment(self.profile(),'reduced_recovery',60)
        self.assertEqual(rating,'dangerous')
        self.assertIn('Regeneration reliance policy:',reason)

    def test_insufficient_recovery_remains_brick(self):
        rating,_=recovery_assessment(self.profile(),'reduced_recovery',70)
        self.assertEqual(rating,'brick')

    def test_mana_only_and_incidental_regen_do_not_create_life_es_reliance(self):
        rating,_=recovery_assessment(self.profile(life_regen=0,life_net_regen=0,mana_regen=5000,mana_defence_detected=True),'reduced_recovery',60)
        self.assertEqual(rating,'free')
        rating,reason=recovery_assessment(self.profile(life_regen=50,life_net_regen=50),'reduced_recovery',60)
        self.assertNotIn('Regeneration reliance policy:',reason)

    def test_es_regeneration_on_mana_defence_build_is_balanced(self):
        rating,_=recovery_assessment(self.profile(life=1,energy_shield=10000,energy_shield_regen=1000,energy_shield_leech=0,energy_shield_net_regen=1000,mana_defence_detected=True),'reduced_recovery',60)
        self.assertEqual(rating,'dangerous')
