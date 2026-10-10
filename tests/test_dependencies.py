import json
from pathlib import Path
import unittest

from backend.analysis_service import analyze_request
from backend.dependencies import skill_metadata
from backend.pob import build_profile, decode_build
from backend.rules import classify
from test_core import export_code

def build(skill, supports=(), stats=None, utility=()):
    numbers = ''.join(f'<PlayerStat stat="{key}" value="{value}"/>' for key, value in (stats or {}).items())
    gems = f'<Gem nameSpec="{skill}"/>' + ''.join(f'<Gem nameSpec="{s}" gemId="SupportGemTest"/>' for s in supports)
    extra = ''.join(f'<Skill><Gem nameSpec="{s}"/></Skill>' for s in utility)
    return f'<PathOfBuilding><Build mainSocketGroup="1">{numbers}</Build><Skills><Skill>{gems}</Skill>{extra}</Skills></PathOfBuilding>'

class DependencyTests(unittest.TestCase):
    def profile(self, *args, **kwargs):
        return build_profile(decode_build(export_code(build(*args, **kwargs))))

    def test_archetype_skill_metadata(self):
        # Recognition checks, not a claim these are independently verified builds.
        cases = [('Boneshatter', 'player', 'attack'), ('Lightning Strike', 'player', 'attack'),
            ('Tornado Shot', 'player', 'attack'), ('Ethereal Knives', 'player', 'non_attack'),
            ('Penance Brand', 'brands', 'non_attack'), ('Wintertide Brand', 'brands', 'non_attack'),
            ('Raise Spectre', 'minions', 'non_attack'), ('Summon Skeletons', 'minions', 'non_attack'),
            ('Holy Flame Totem', 'totems', 'non_attack'), ('Lightning Trap', 'traps', 'non_attack'),
            ('Righteous Fire', 'player', 'non_attack'), ('Death Aura', 'player', 'non_attack'),
            ('Winter Orb', 'player', 'non_attack'), ('Cyclone', 'player', 'attack')]
        for name, delivery, kind in cases:
            with self.subTest(name=name):
                p = self.profile(name)
                self.assertTrue(p['skill_metadata_known'])
                self.assertEqual(p['damage_delivery'], delivery)
                self.assertEqual(p['main_skill_kind'], kind)

    def test_unknown_skill_cannot_get_absence_based_free_offensive_rules(self):
        p = self.profile('Future Unsupported Skill')
        self.assertFalse(p['coverage']['main_skill_recognized'])
        mods = {m['id']: m for m in classify(p)}
        for key in ['reduced_auras', 'unstunnable_monsters', 'less_player_aoe']:
            self.assertEqual(mods[key]['rating'], 'review')
            self.assertEqual(mods[key]['assessment_status'], 'uncertain')

    def test_utility_skills_do_not_create_primary_dependencies(self):
        p = self.profile('Arc', utility=['Raise Spectre', 'Decoy Totem', 'Cyclone'])
        self.assertEqual(p['damage_delivery'], 'player')
        self.assertFalse(p['minion_damage_primary'])
        self.assertFalse(p['uses_cast_on_crit'])
        self.assertNotIn('cooldown', {d['id'] for d in p['dependencies']})

    def test_linked_trigger_and_native_cooldown_are_not_invisible(self):
        p = self.profile('Cyclone', ['Cast On Critical Strike'])
        self.assertTrue(p['uses_cast_on_crit'])
        self.assertEqual({m['id']: m for m in classify(p)}['reduced_cooldown']['rating'], 'brick')
        p = self.profile('Frostblink')
        self.assertTrue(p['main_skill_has_cooldown'])
        self.assertEqual({m['id']: m for m in classify(p)}['reduced_cooldown']['rating'], 'review')
        p = self.profile('Arc', ['Spell Totem'])
        self.assertEqual(p['damage_delivery'], 'totems')
        p = self.profile('Frostblink', ['High-Impact Mine'])
        self.assertEqual(p['damage_delivery'], 'mines')

    def test_core_hex_trigger_and_bypass(self):
        p = self.profile('Despair', ['Impending Doom'])
        self.assertEqual({m['id']: m for m in classify(p)}['hexproof']['rating'], 'brick')
        p['assumptions'] = {'hexproof_bypass': True}
        self.assertEqual({m['id']: m for m in classify(p)}['hexproof']['rating'], 'free')

    def test_ignite_dependency_is_not_poison_dependency(self):
        p = self.profile('Fireball', stats={'TotalDPS': 1000, 'IgniteDPS': 900})
        self.assertEqual({m['id']: m for m in classify(p)}['avoid_ailments']['rating'], 'brick')
        p['assumptions'] = {'map_effect_increased': 50}
        self.assertEqual({m['id']: m for m in classify(p)}['avoid_ailments']['rating'], 'brick')
        p = self.profile('Blade Vortex', stats={'TotalDPS': 1000, 'PoisonDPS': 900})
        self.assertEqual(p['primary_ailments'], ['poison'])
        self.assertNotEqual({m['id']: m for m in classify(p)}['avoid_ailments']['rating'], 'brick')

    def test_pure_dot_and_mixed_dot_are_distinct(self):
        p = self.profile('Wintertide Brand')
        self.assertTrue(p['main_damage_is_pure_dot'])
        self.assertEqual({m['id']: m for m in classify(p)}['less_accuracy']['rating'], 'free')
        self.assertEqual({m['id']: m for m in classify(p)}['physical_thorns']['rating'], 'free')
        self.assertFalse(self.profile('Toxic Rain')['main_damage_is_pure_dot'])
        p = self.profile('Essence Drain')
        self.assertFalse(p['main_damage_is_pure_dot'])
        self.assertEqual({m['id']: m for m in classify(p)}['physical_thorns']['rating'], 'review')

    def test_every_normal_catalogue_modifier_has_audited_status(self):
        result = analyze_request({'source': export_code(build('Arc'))})
        summary = result['profile']['coverage']['normal_modifiers']
        self.assertEqual(summary['total'], 78)
        self.assertEqual(summary['total'], sum(summary[key] for key in ['counter', 'unaffected', 'uncertain', 'policy']))
        rows = [m for m in result['mods'] if m['id'].startswith('map-') and 'assessment_status' in m]
        self.assertGreaterEqual(len(rows), 78)
        self.assertEqual(summary['policy'], 54)

    def test_confirmation_removes_resolved_coverage_issue(self):
        data = {'source': export_code(build('Arc', utility=['Malevolence']))}
        self.assertTrue(any('Supporting aura' in x for x in analyze_request(data)['profile']['coverage']['issues']))
        data['assumptions'] = {'aura_role': 'utility'}
        self.assertFalse(any('Supporting aura' in x for x in analyze_request(data)['profile']['coverage']['issues']))

    def test_metadata_provenance(self):
        by_id, _, revision = skill_metadata()
        self.assertGreater(len(by_id), 600)
        self.assertEqual(len(revision), 40)

    def test_offline_normal_snapshot_matches_frontend_catalogue(self):
        root = Path(__file__).resolve().parents[1]
        backend = json.loads((root / 'backend/normal_catalogue.json').read_text(encoding='utf-8'))
        frontend = json.loads((root / 'frontend/src/data/mapPool.json').read_text(encoding='utf-8'))
        self.assertEqual(backend, [row for row in frontend if not row['nightmare']])

    def test_item_trigger_requires_the_main_socketing_item(self):
        xml = '''<PathOfBuilding><Build mainSocketGroup="1"/><Skills><Skill slot="Weapon 1"><Gem nameSpec="Arc"/></Skill></Skills>
        <Items activeItemSet="1"><Item id="1">Trigger a Socketed Lightning Spell on Hit\nThis Spell has a 0.25 second Cooldown</Item>
        <ItemSet id="1"><Slot name="Weapon 1" itemId="1"/></ItemSet></Items></PathOfBuilding>'''
        p = build_profile(decode_build(export_code(xml)))
        self.assertTrue(p['core_trigger_cooldown'])
        self.assertEqual({m['id']: m for m in classify(p)}['reduced_cooldown']['rating'], 'brick')
        xml = xml.replace('Skill slot="Weapon 1"', 'Skill slot="Body Armour"')
        p = build_profile(decode_build(export_code(xml)))
        self.assertFalse(p['core_trigger_cooldown'])

    def test_explicit_stat_scaling_is_recorded_without_guessing_from_class(self):
        xml = '''<PathOfBuilding><Build mainSocketGroup="1"/><Skills><Skill><Gem nameSpec="Arc"/></Skill></Skills>
        <Items activeItemSet="1"><Item id="1">1% increased Spell Damage per 16 Intelligence</Item>
        <ItemSet id="1"><Slot name="Weapon 1" itemId="1"/></ItemSet></Items></PathOfBuilding>'''
        p = build_profile(decode_build(export_code(xml)))
        self.assertIn('stack_intelligence', {row['id'] for row in p['dependencies']})
        self.assertNotIn('stack_intelligence', {row['id'] for row in self.profile('Arc')['dependencies']})

    def test_non_cooldown_main_skill_is_not_blocked_by_safe(self):
        for skill in ['Kinetic Blast', 'Arc', 'Cyclone']:
            xml = build(skill, utility=['Frostblink', 'Molten Shell'])
            result = analyze_request({'source': export_code(xml)})
            mods = {row['id']: row for row in result['mods']}
            self.assertEqual(mods['reduced_cooldown']['rating'], 'free')
            for preset in ['safe','balanced','greedy']:
                self.assertNotIn('reduced_cooldown', result['presets'][preset]['blocked_ids'])

    def test_real_strength_kinetic_blast_cdr_not_core(self):
        xml=(Path(__file__).parent/'fixtures/kinetic_blast_strength.xml').read_text(encoding='utf-8')
        result=analyze_request({'source':export_code(xml)})
        self.assertEqual(result['profile']['main_skill'],'Kinetic Blast')
        self.assertFalse(result['profile']['main_skill_has_cooldown'])
        self.assertFalse(result['profile']['core_trigger_cooldown'])
        self.assertNotIn('reduced_cooldown',result['presets']['safe']['blocked_ids'])
        self.assertEqual(len([d for d in result['profile']['dependencies'] if d['id']=='stack_strength']),1)
        self.assertEqual(next(m for m in result['mods'] if m['id']=='reduced_cooldown')['rating'],'free')
