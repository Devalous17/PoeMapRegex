import base64
from pathlib import Path
import unittest
import zlib

from backend.analysis_service import analyze_request
from backend.assessment import assessed_rule
from backend.pob import build_profile, decode_build
from backend.rules import make_regex


def encoded(xml):
    return base64.urlsafe_b64encode(zlib.compress(xml.encode())).decode()


class PresetRelevanceTests(unittest.TestCase):
    def test_real_accuracy_stacker_has_offensive_dependency(self):
        xml = (Path(__file__).parent / 'fixtures/accuracy_stacker_reave.xml').read_text(encoding='utf-8')
        result = analyze_request({'source': encoded(xml)})
        profile = result['profile']
        self.assertEqual(profile['main_accuracy'], 129267)
        self.assertTrue(profile['accuracy_scales_offence'])
        self.assertTrue(any(d['id'] == 'stack_accuracy' for d in profile['dependencies']))
        mods = {row['id']: row for row in result['mods']}
        for key in ('less_accuracy', 'map--114660370', 'map--54649013', 'map--2050206104'):
            self.assertEqual(mods[key]['rating'], 'dangerous', mods[key]['reason'])
        self.assertEqual(mods['reduced_cooldown']['rating'], 'free')
        self.assertIn('less_accuracy', result['presets']['balanced']['blocked_ids'])
        self.assertNotIn('less_accuracy', result['presets']['greedy']['blocked_ids'])

    def test_accuracy_presence_and_unequipped_scaling_do_not_imply_stacking(self):
        template = '''<PathOfBuilding><Build mainSocketGroup="1"><PlayerStat stat="MainHandAccuracy" value="100000"/></Build>
        <Skills><Skill><Gem nameSpec="Reave of Refraction"/></Skill></Skills>
        <Items activeItemSet="1"><Item id="1">{equipped}</Item><Item id="2">1 to 6 Added Attack Lightning Damage per 200 Accuracy Rating</Item>
        <ItemSet id="1"><Slot name="Weapon 1" itemId="1"/></ItemSet></Items></PathOfBuilding>'''
        for text in ('+500 Accuracy Rating', '4% increased Accuracy Rating per 25 Intelligence'):
            profile = build_profile(decode_build(encoded(template.format(equipped=text))))
            self.assertFalse(profile['accuracy_scales_offence'])
        profile = build_profile(decode_build(encoded(template.format(equipped='1 to 6 Added Attack Lightning Damage per 200 Accuracy Rating\nHits cannot be Evaded'))))
        self.assertTrue(profile['accuracy_scales_offence'])
        self.assertEqual(assessed_rule(profile, 'less_accuracy')[0], 'dangerous')

    def test_unknowns_are_not_free_or_automatically_blocked(self):
        mods = [{'id': 'unknown', 'name': 'Unknown', 'pattern': 'unknown', 'rating': 'review'}]
        for preset in ('safe', 'balanced', 'greedy'):
            self.assertEqual(make_regex(mods, preset)['blocked_ids'], [])
            self.assertEqual(make_regex(mods, preset, {'unknown': 'avoid'})['blocked_ids'], ['unknown'])

    def test_balanced_critical_loss_policy_does_not_promote_minor_losses(self):
        profile = {'crit_chance': 80, 'crit_multiplier': 382}
        self.assertEqual(assessed_rule(profile, 'monster_crit_reduction', 40)[0], 'dangerous')
        self.assertEqual(assessed_rule(profile, 'monster_crit_reduction', 10)[0], 'free')
