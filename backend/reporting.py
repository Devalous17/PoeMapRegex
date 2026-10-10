"""Inspectable assessment basis and complete current-pool reports."""
import json
from pathlib import Path
from .measurements import estimate

ROOT = Path(__file__).parent


def assessment_basis(profile, row, rule, value=None):
    if row.get('reason', '').startswith('Optional-mechanic allowance:'):
        return 'policy_allowance'
    if row.get('assessment_status') == 'policy':
        return 'policy_allowance'
    if row['rating'] == 'review':
        return 'unknown'
    if row.get('nightmare_policy'):
        return 'policy_allowance' if row['rating'] == 'free' else 'conservative_policy'
    if rule == 'reduced_recovery' and 'Regeneration reliance policy:' in row.get('reason', ''):
        return 'conservative_policy'
    assumptions = profile.get('assumptions', {})
    if row['rating'] == 'brick':
        if rule in {'avoid_ailments', 'avoid_poison_bleed_impale'}:
            avoid = value if value is not None else (70 if rule == 'avoid_ailments' else 50) * (1 + assumptions.get('map_effect_increased', 0) / 100)
            return 'dependency_rule' if avoid >= 100 else 'conservative_policy'
        if rule in {'reduced_cooldown', 'reduced_flask_charges'}:
            return 'conservative_policy'
        if rule == 'reduced_auras' and profile.get('primary_damage_aura'):
            return 'conservative_policy'
        if rule == 'reduced_block_and_armour' and (profile.get('effective_attack_block') or 0) + (profile.get('effective_spell_block') or 0) >= 75:
            return 'conservative_policy'
    if rule == 'less_accuracy' and profile.get('accuracy_scales_offence'):
        return 'conservative_policy'
    if rule == 'hexproof' and assumptions.get('curse_role') == 'mechanic':
        return 'user_confirmation'
    if rule in {'reduced_auras', 'reduced_monster_curse_effect'} and assumptions.get('aura_role' if rule == 'reduced_auras' else 'curse_role', 'unknown') != 'unknown':
        return 'user_confirmation'
    return 'dependency_rule'


def enrich_assessments(profile, mods):
    mapping = json.loads((ROOT / 'modifier_rules.json').read_text(encoding='utf-8'))
    contexts = {row['id']: row for row in json.loads((ROOT / 'map_rule_values.json').read_text(encoding='utf-8'))}
    effect = 1 + profile.get('assumptions', {}).get('map_effect_increased', 0) / 100
    for row in mods:
        key = row['id'].removeprefix('map-')
        context = contexts.get(key)
        rule = context['rule'] if context else row.get('rule_id', mapping.get(key, row['id']))
        value = context['worst_roll'] * effect if context else None
        basis = assessment_basis(profile, row, rule, value)
        measurement = estimate(profile, rule, value)
        if basis == 'dependency_rule' and measurement['status'] in {'estimated', 'partial'} and row['rating'] != 'free':
            basis = 'snapshot_model'
        row.update(rule_id=rule, assessment_basis=basis, measurement=measurement,
                   conclusion='uncertain' if basis == 'unknown' else 'policy' if basis in {'policy_allowance', 'conservative_policy'} else 'unaffected' if row['rating'] == 'free' else 'risk')
        if basis in {'conservative_policy', 'policy_allowance', 'unknown'}:
            row['confidence'] = 'low'
    return mods


def assessment_report(profile, mods):
    from .rules import preset_blocks
    catalogue = json.loads((ROOT / 'normal_catalogue.json').read_text(encoding='utf-8')) + json.loads((ROOT / 'nightmare_catalogue.json').read_text(encoding='utf-8'))
    by_id = {row['id']: row for row in mods}
    entries = []
    for mod in catalogue:
        row = by_id['map-' + mod['id']]
        entries.append(dict(modifier_id=row['id'], modifier=mod['text'], pool='nightmare' if mod['nightmare'] else 'normal',
                            rating=row['rating'], basis=row['assessment_basis'], confidence=row.get('confidence', 'low'),
                            evidence=row.get('dependency_evidence', []), explanation=row['reason'],
                            measurement=row['measurement'], presets=[name for name in ('greedy', 'balanced', 'safe') if preset_blocks(row, name)]))
    counts = {basis: sum(row['basis'] == basis for row in entries) for basis in ('snapshot_model','dependency_rule','user_confirmation','conservative_policy','policy_allowance','unknown')}
    return dict(schema_version=1, main_skill=profile['main_skill'], dependencies=profile.get('dependencies', []), assumptions=profile.get('assumptions', {}),
                calculations=dict(engine='saved_snapshot', full_pob_recalculation=False,
                                  supported_models=['hit_critical_damage','maximum_resistance','measured_recovery','ailment_avoidance_check','nightmare_hit_penetration','nightmare_defence_stats'],
                                  limitations=['Supporting skill contributions, trigger timing, flask/charge uptime and entity durability are not fully recalculated.']),
                summary=dict(total=len(entries), by_basis=counts), modifiers=entries)
