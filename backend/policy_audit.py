"""Review inventory for policy allowances; these questions are not safety rules."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
GROUPS = {
    'MapPlayerBuffsExpireFaster': ('high', ['activation','sustain'], 'Does shorter buff uptime interrupt required charges, buffs, guard or recovery effects?'),
    'MapPlayerElementalEquilibrium': ('high', ['scaling'], 'How much main damage depends on Exposure, and can another damage source compensate?'),
    'MapMonstersChanceToSuppressSpells': ('high', ['delivery','scaling'], 'How much main damage is suppressible spell-hit damage, and what remains after suppression?'),
    'MapMonsterPhysicalResistance': ('high', ['scaling'], 'What physical hit damage remains after enemy reduction and the build\'s applicable bypass?'),
    'MapMonstersAllResistances': ('high', ['scaling'], 'What damage remains after enemy resistances, penetration, resistance reduction and applicable ignore effects?'),
    'MapMonstersBlindOnHit': ('high', ['delivery','activation'], 'Does Blind materially reduce main-attack hit chance or required on-hit effects?'),
    'MapMonsterPacks': ('lower', ['encounter'], 'Monster composition changes encounter pressure; no universal build-breaking interaction is established.'),
    'MapGroundEffect': ('medium', ['defence','sustain'], 'Does this ground effect bypass recovery or avoidance relied upon by the build? Check the exact ground type.'),
    'MapPlayerEnfeeblement': ('high', ['scaling','delivery'], 'What offensive contribution is lost after actual curse mitigation and enemy conditions?'),
    'MapPlayerVulnerability': ('high', ['defence','sustain'], 'Does remaining physical mitigation and recovery cover the applied curse?'),
    'MapPlayerTemporalChains': ('high', ['activation','scaling'], 'Does actual curse effect disrupt action speed, timed buffs or required sequencing?'),
    'MapPlayerElementalWeakness': ('high', ['defence'], 'Are resistances still capped after actual curse mitigation and overcap?'),
    'MapMonstersCantBeSlowedOrTaunted': ('high', ['activation','defence'], 'Are taunt or enemy slowing required for main damage or survival?'),
}


def policy_inventory():
    allowed = set(json.loads((ROOT / 'normal_free_policy.json').read_text(encoding='utf-8')))
    catalogue = json.loads((ROOT / 'normal_catalogue.json').read_text(encoding='utf-8'))
    result = []
    for row in catalogue:
        if row['id'] not in allowed:
            continue
        priority, axes, question = GROUPS.get(row.get('poedbGroup'), ('medium', ['encounter','defence'], 'Measure encounter damage, durability and recovery headroom before claiming this modifier is harmless for every build.'))
        result.append(dict(id='map-' + row['id'], modifier=row['text'], group=row.get('poedbGroup'),
                           priority=priority, axes=axes, question=question, status='policy_allowance_unvalidated'))
    return result
