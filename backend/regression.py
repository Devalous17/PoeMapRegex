"""Run labeled PoB cases; never equate model agreement with game accuracy."""
import base64
import hashlib
import json
from pathlib import Path
import zlib
from .analysis_service import analyze_request
from .policy_audit import policy_inventory


def run_suite(manifest_path):
    path = Path(manifest_path).resolve()
    manifest = json.loads(path.read_text(encoding='utf-8'))
    outcomes = []
    for case in manifest['builds']:
        fixture = (path.parent / case['fixture']).resolve()
        if not fixture.is_relative_to(path.parent):
            raise ValueError('Fixture must stay inside the regression directory.')
        raw = fixture.read_bytes()
        if hashlib.sha256(raw).hexdigest() != case['sha256']:
            outcomes.append(dict(build=case['id'], status='fixture_changed', checks=[]))
            continue
        result = analyze_request({'source': base64.urlsafe_b64encode(zlib.compress(raw)).decode(), 'assumptions':case.get('assumptions', {})})
        mods = {row['id']: row for row in result['mods']}
        checks = []
        for expected in case.get('expectations', []):
            row = mods.get(expected['modifier'])
            rating = row['rating'] if row else None
            passed = rating == expected['rating']
            checks.append(dict(modifier=expected['modifier'], expected=expected['rating'], actual=rating,
                               passed=passed, label_origin=expected['label_origin'], rationale=expected['rationale'],
                               missed_brick=expected['rating']=='brick' and rating!='brick',
                               unnecessary_exclusion=expected['rating']=='free' and rating in {'brick','dangerous','uncomfortable','review'}))
        outcomes.append(dict(build=case['id'], split=case['split'], main_skill=result['profile']['main_skill'],
                             status='pass' if all(row['passed'] for row in checks) else 'fail', checks=checks,
                             assessment=result['assessment_report']))
    checks = [row for build in outcomes for row in build['checks']]
    origins = sorted({row['label_origin'] for row in checks})
    return dict(schema_version=1, sample=manifest.get('sample', {}),
                metrics=dict(builds=len(outcomes), checks=len(checks), passed=sum(row['passed'] for row in checks),
                             missed_labeled_bricks=sum(row['missed_brick'] for row in checks),
                             unnecessary_labeled_exclusions=sum(row['unnecessary_exclusion'] for row in checks),
                             changed_fixtures=sum(row['status']=='fixture_changed' for row in outcomes),
                             held_out_builds=sum(row.get('split')=='holdout' for row in outcomes),
                             smoke_only_builds=sum(not row['checks'] for row in outcomes),
                             label_agreement={origin: dict(checks=sum(row['label_origin']==origin for row in checks), passed=sum(row['label_origin']==origin and row['passed'] for row in checks)) for origin in origins},
                             population_coverage_percent=None,
                             note='Regression agreement with labels is not measured in-game accuracy or public-player coverage.'),
                success=all(row['status']=='pass' for row in outcomes), builds=outcomes, policy_audit=policy_inventory())
