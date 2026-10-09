"""Account for every current normal catalogue row without inventing safety."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
def audit_catalogue(analyzed):
    mapping = json.loads((ROOT / 'modifier_rules.json').read_text(encoding='utf-8'))
    policy = set(json.loads((ROOT / 'normal_free_policy.json').read_text(encoding='utf-8')))
    rows = json.loads((ROOT / 'normal_catalogue.json').read_text(encoding='utf-8'))
    by_id = {row['id']: row for row in analyzed}
    assessments = []
    summary = dict(total=0, counter=0, unaffected=0, uncertain=0, policy=0)
    for row in rows:
        if row['nightmare']:
            continue
        key = 'map-' + row['id']
        rule = by_id.get(key) or by_id.get(mapping.get(row['id']))
        if rule:
            assessed = {**rule, 'id': key, 'name': row['text'], 'pattern': row['pattern']}
        elif row['id'] in policy:
            assessed = dict(id=key, name=row['text'], pattern=row['pattern'], rating='free', confidence='low', assessment_status='policy', reason='Allowed by your reviewed normal-map Free policy; this is not a verified absence of every possible build interaction.', dependency_axes=[], dependency_evidence=[])
        else:
            assessed = dict(id=key, name=row['text'], pattern=row['pattern'], rating='review', confidence='low', assessment_status='uncertain', reason='No dependency assessment covers this catalogue modifier. Review it; missing coverage does not establish safety.', dependency_axes=[], dependency_evidence=[])
        assessments.append(assessed)
        summary['total'] += 1
        summary[assessed['assessment_status']] += 1
    return dict(summary=summary, assessments=assessments)
