import json
from pathlib import Path
import unittest
from backend.analysis_service import analyze_request
from backend.nightmare import reviewed_assessment
from test_core import export_code
from test_dependencies import build

ROOT=Path(__file__).resolve().parents[1]


class NightmareReviewTests(unittest.TestCase):
    def analyze(self, xml, assumptions=None):
        return analyze_request({'source':export_code(xml),'assumptions':assumptions or {}})

    def test_complete_stable_review_and_preset_ratings(self):
        policy=json.loads((ROOT/'backend/nightmare_policy.json').read_text())
        self.assertEqual([row['number'] for row in policy],list(range(1,48)))
        rows=json.loads((ROOT/'backend/nightmare_catalogue.json').read_text())
        self.assertEqual([row['id'] for row in policy],[row['id'] for row in rows])
        report=self.analyze(build('Arc'))['assessment_report']
        by_id={row['modifier_id']:row for row in report['modifiers']}
        expected={2:('brick',['greedy','balanced','safe']),6:('brick',['greedy','balanced','safe']),8:('dangerous',['balanced','safe']),11:('dangerous',['balanced','safe']),13:('dangerous',['balanced','safe']),14:('dangerous',['balanced','safe']),33:('dangerous',['balanced','safe']),34:('dangerous',['balanced','safe']),37:('dangerous',['balanced','safe']),43:('uncomfortable',['safe']),44:('uncomfortable',['safe'])}
        for number,(rating,presets) in expected.items():
            row=by_id['map-'+rows[number-1]['id']]
            self.assertEqual((row['rating'],row['presets']),(rating,presets),number)
            self.assertEqual(row['basis'],'conservative_policy')
        conditional={3,17,18,19,24}
        for number,mod in enumerate(rows,1):
            if number not in expected and number not in conditional:
                row=by_id['map-'+mod['id']]
                self.assertEqual(row['rating'],'free',number)
                self.assertEqual(row['presets'],[],number)
                self.assertEqual(row['basis'],'policy_allowance',number)

    def test_attack_block_only_for_attack_hits(self):
        for name,rating in [('Lightning Strike','dangerous'),('Viper Strike of the Mamba','dangerous'),('Arc','free'),('Vaal Righteous Fire','free')]:
            result=self.analyze(build(name))
            self.assertEqual(next(row for row in result['mods'] if row['id']=='map--1940135977')['rating'],rating)

    def test_flask_investment_is_distinct_from_utility_prefix(self):
        for profile in [{'ascendancy':'Pathfinder'},{'traitor_likely':True},{'wardloop_detected':True},{'global_flask_effect_investment':10},{'flask_charge_investment':10},{'assumptions':{'flask_essential':True}}]:
            self.assertEqual(reviewed_assessment(profile,'flask_investment')[0],'dangerous')
        self.assertEqual(reviewed_assessment({'filled_flasks':5,'flask_effect_investment':70},'flask_investment')[0],'free')

    def test_flask_investment_parser_reads_equipped_global_mods(self):
        xml=build('Arc').replace('</PathOfBuilding>','<Items activeItemSet="1"><Item id="1">20% increased Flask Charges gained\n15% increased Effect of Flasks</Item><ItemSet id="1"><Slot name="Belt" itemId="1"/></ItemSet></Items></PathOfBuilding>')
        result=self.analyze(xml)
        self.assertEqual(result['profile']['flask_charge_investment'],20)
        self.assertEqual(result['profile']['global_flask_effect_investment'],15)
        self.assertEqual(next(row for row in result['mods'] if row['id']=='map--105914721')['rating'],'dangerous')

    def test_chaos_threshold_is_exactly_70_or_immunity(self):
        for chaos,rating in [(69.9,'dangerous'),(70,'free'),(75,'free'),(None,'dangerous')]:
            self.assertEqual(reviewed_assessment({'chaos_resistance':chaos},'chaos_threshold')[0],rating)
        self.assertEqual(reviewed_assessment({'chaos_immune':True,'chaos_resistance':-60},'chaos_threshold')[0],'free')

    def test_defensive_crit_protection_requires_100_and_is_read_from_export(self):
        for value,rating in [(99.9,'dangerous'),(100,'free'),(None,'dangerous')]:
            result=self.analyze(build('Arc',stats={} if value is None else {'CritExtraDamageReduction':value}))
            self.assertEqual(next(row for row in result['mods'] if row['id']=='map-246480838')['rating'],rating)
        self.assertEqual(reviewed_assessment({'crit_chance':100,'crit_multiplier':600},'crit_immunity')[0],'dangerous')

    def test_stun_dependency_is_conditional(self):
        for name,rating in [('Boneshatter','brick'),('Arc','free')]:
            result=self.analyze(build(name))
            self.assertEqual(next(row for row in result['mods'] if row['id']=='map-670500310')['rating'],rating)

    def test_armour_stacker_retains_less_defences_brick(self):
        result=self.analyze((ROOT/'tests/fixtures/armour_stacker.xml').read_text())
        self.assertEqual(next(row for row in result['mods'] if row['id']=='map-1464066514')['rating'],'brick')

    def test_equipped_crit_protection_requires_unconditional_text(self):
        for line,rating in [('You take no Extra Damage from Critical Strikes','free'),('You take no Extra Damage from Critical Strikes while Elusive','dangerous')]:
            xml=build('Arc').replace('</PathOfBuilding>',f'<Items activeItemSet="1"><Item id="1">{line}</Item><ItemSet id="1"><Slot name="Body Armour" itemId="1"/></ItemSet></Items></PathOfBuilding>')
            result=self.analyze(xml)
            self.assertEqual(next(row for row in result['mods'] if row['id']=='map-246480838')['rating'],rating)

    def test_rf_uses_explicit_thorns_policy_and_safe_only_suppression(self):
        result=self.analyze((ROOT/'tests/fixtures/rf_chieftain_recovery.xml').read_text())
        rows={row['modifier_id']:row for row in result['assessment_report']['modifiers']}
        self.assertEqual(rows['map--1430865583']['rating'],'dangerous')
        self.assertEqual(rows['map-poedb-MapMonstersChanceToSuppressSpells']['presets'],['safe'])
        self.assertEqual(rows['map-127168403']['rating'],'free')
        self.assertEqual(rows['map-1117764869']['rating'],'free')
