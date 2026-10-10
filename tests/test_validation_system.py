import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from backend.analysis_service import analyze_request
from backend.measurements import estimate
from backend.policy_audit import policy_inventory
from backend.regression import run_suite
from scripts.add_regression_build import sanitize_export
from test_core import export_code
from test_dependencies import build

ROOT=Path(__file__).resolve().parents[1]


class ValidationSystemTests(unittest.TestCase):
    def test_report_covers_both_pools_and_separates_policy(self):
        result=analyze_request({'source':export_code(build('Arc'))})
        report=result['assessment_report']
        self.assertEqual(report['summary']['total'],125)
        self.assertEqual(len({row['modifier_id'] for row in report['modifiers']}),125)
        self.assertEqual(sum(row['pool']=='nightmare' for row in report['modifiers']),47)
        self.assertEqual(sum(row['basis']=='policy_allowance' and row['pool']=='normal' for row in report['modifiers']),54)
        self.assertFalse(report['calculations']['full_pob_recalculation'])
        self.assertEqual(len({row['id'] for row in result['mods']}),len(result['mods']))
        self.assertTrue(all(row['basis'] in {'conservative_policy','policy_allowance'} for row in report['modifiers'] if row['pool']=='nightmare'))
        json.dumps(result,allow_nan=False)

    def test_conservative_avoidance_is_not_presented_as_proven_immunity(self):
        source=export_code(build('Viper Strike of the Mamba',stats={'TotalDPS':1000,'PoisonDPS':900}))
        result=analyze_request({'source':source})
        row=next(row for row in result['mods'] if row['id']=='map--627831782')
        self.assertEqual(row['assessment_basis'],'conservative_policy')
        self.assertEqual(row['confidence'],'low')
        self.assertEqual(row['measurement']['quantities'][0]['after'],50)
        result=analyze_request({'source':source,'assumptions':{'map_effect_increased':100}})
        row=next(row for row in result['mods'] if row['id']=='map--627831782')
        self.assertNotEqual(row['assessment_basis'],'conservative_policy')
        self.assertEqual(row['measurement']['quantities'][0]['after'],0)

    def test_models_do_not_turn_missing_or_unaffected_values_into_numbers(self):
        self.assertEqual(estimate({},'monster_crit_reduction')['status'],'unsupported')
        self.assertEqual(estimate({'crit_chance':float('nan'),'crit_multiplier':600},'monster_crit_reduction')['quantities'],[])
        self.assertEqual(estimate({'primary_ailments':['poison']},'avoid_ailments')['status'],'unsupported')
        self.assertEqual(estimate({'core_trigger_cooldown':True},'reduced_cooldown')['status'],'unsupported')
        model=estimate({'elemental_resistances':{'Fire':75},'maximum_resistances':{'Fire':75}},'minus_max_res',15)
        self.assertAlmostEqual(model['quantities'][1]['after'],1.6)

    def test_recovery_model_preserves_missing_channels_and_mana_scope(self):
        profile={'saved_mana_cost_per_second':80,'recovery_channels':[
            {'pool':'Mana','channel':'regeneration','value':100},
            {'pool':'Mana','channel':'leech','value':0}]}
        model=estimate(profile,'no_regen')
        self.assertEqual(model['status'],'partial')
        self.assertEqual(model['quantities'][1]['after'],-80)
        self.assertEqual(estimate(profile,'reduced_recovery')['quantities'][0]['after'],100)
        profile['recovery_channels'][1]['value']=50
        self.assertEqual(estimate(profile,'reduced_leech',120)['quantities'][0]['after'],100)

    def test_all_policy_allowances_have_review_questions(self):
        rows=policy_inventory()
        self.assertEqual(len(rows),54)
        self.assertEqual(len({row['id'] for row in rows}),54)
        self.assertTrue(all(row['question'] and row['status']=='policy_allowance_unvalidated' for row in rows))
        self.assertEqual(next(row for row in rows if row['group']=='MapPlayerBuffsExpireFaster')['priority'],'high')

    def test_real_regressions_and_coverage_claims(self):
        report=run_suite(ROOT/'tests/fixtures/regression_manifest.json')
        self.assertTrue(report['success'])
        self.assertEqual(report['metrics']['builds'],10)
        self.assertIsNone(report['metrics']['population_coverage_percent'])
        self.assertEqual(report['metrics']['held_out_builds'],0)
        self.assertIn('conservative_policy',report['metrics']['label_agreement'])

    def test_changed_fixture_and_wrong_labels_fail_the_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=build('Arc').encode();(root/'build.xml').write_bytes(raw)
            manifest={'builds':[{'id':'test','fixture':'build.xml','sha256':hashlib.sha256(raw).hexdigest(),'split':'development','expectations':[
                {'modifier':'reduced_cooldown','rating':'brick','label_origin':'reviewer_judgment','rationale':'Intentionally wrong expected result.'}]}]}
            path=root/'manifest.json';path.write_text(json.dumps(manifest))
            result=run_suite(path)
            self.assertFalse(result['success'])
            self.assertEqual(result['metrics']['missed_labeled_bricks'],1)
            (root/'build.xml').write_bytes(raw+b' ')
            result=run_suite(path)
            self.assertFalse(result['success'])
            self.assertEqual(result['metrics']['changed_fixtures'],1)

    def test_sanitizing_preserves_mechanic_attributes_and_removes_notes(self):
        xml=build('Arc').replace('</PathOfBuilding>','<Notes>private prose</Notes><Items><ItemSet id="1"><Slot name="Weapon 1" itemId="1"/></ItemSet></Items></PathOfBuilding>')
        sanitized=sanitize_export(xml).decode()
        self.assertNotIn('private prose',sanitized)
        self.assertIn('name="Weapon 1"',sanitized)
        self.assertIn('nameSpec="Arc"',sanitized)
        with self.assertRaises(ValueError): sanitize_export('https://pobb.in/example')
