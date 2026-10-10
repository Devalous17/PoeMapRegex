"""User-reviewed Nightmare selection policy, separate from proof of safety."""
import json
from pathlib import Path
from .dependencies import annotate_assessment

ROOT=Path(__file__).parent


def reviewed_assessment(profile, decision):
    if decision=='always_brick':
        return 'brick','Always blocked by your Nightmare review, including Greedy. This is your exclusion policy, not a claim that every build necessarily fails.'
    if decision=='avoid':
        return 'dangerous','Avoid for smooth mapping under your Nightmare review. Blocked by Balanced and Safe; not automatically labeled a mechanical Brick.'
    if decision=='safe_only':
        return 'uncomfortable','Optional caution under your Nightmare review. Blocked only by Safe; allowed by Balanced and Greedy.'
    if decision=='attack_hits':
        if profile.get('main_skill_kind')=='attack' and not profile.get('main_damage_is_pure_dot'):
            return 'dangerous','The selected main damage uses attack hits. Monster attack block can deny the hit and its on-hit effects. Avoid under your Nightmare attack-hit policy.'
        return 'free','No player attack-hit main damage is established. Allowed by your Nightmare policy; utility attacks and unmeasured minion attack contributions are not treated as a primary dependency.'
    if decision=='flask_investment':
        invested=(profile.get('ascendancy','').lower()=='pathfinder' or profile.get('traitor_likely') or profile.get('wardloop_detected') or (profile.get('global_flask_effect_investment') or 0)>0 or (profile.get('flask_charge_investment') or 0)>0 or profile.get('assumptions',{}).get('flask_essential') is True)
        if invested:
            return 'dangerous','Pathfinder, Traitor, Wardloop, global flask effect/charge investment, or confirmed essential flasks are detected. Avoid less flask effect under your Nightmare investment policy. A single flask effect prefix alone does not establish global investment.'
        return 'free','No established flask investment or confirmed flask dependency meets your Nightmare rule. Merely equipping utility flasks does not automatically exclude this modifier.'
    if decision=='chaos_threshold':
        chaos=profile.get('chaos_resistance')
        if profile.get('chaos_immune') or chaos is not None and chaos>=70:
            return 'free','Allowed by your Nightmare threshold: Chaos immunity or at least 70% saved Chaos Resistance. Resistance at 70% is not damage immunity or necessarily the resistance cap.'
        return 'dangerous','Avoid under your Nightmare rule: Chaos immunity or at least 70% saved Chaos Resistance is not established. Missing resistance values do not meet the threshold.'
    if decision=='crit_immunity':
        reduction=profile.get('crit_extra_damage_reduction')
        if reduction is not None and reduction>=100:
            return 'free','Saved reduction of extra damage taken from critical strikes is at least 100%, meeting your Nightmare allowance. Saved conditional protections still depend on uptime.'
        return 'dangerous','Avoid under your Nightmare rule: 100% reduced extra damage taken from critical strikes is not established. Saved character crit chance/multiplier does not establish defensive crit protection.'
    if decision=='stun_dependency':
        if profile.get('stun_dependent'):
            return 'brick','The selected main damage/clear setup relies on stunning monsters. Cannot Stun blocks that established core interaction.'
        return 'free','No established stun-based main damage/clear dependency. Allowed under your Nightmare policy, including the affix’s separate slow restrictions.'
    if decision=='defences':
        if profile.get('armour_scales_attack_damage'):
            return 'brick','Armour scales both main damage and defence. Your existing armour-stacker Brick policy applies to less Defences.'
        return 'dangerous','Avoid less Defences for smooth Nightmare mapping under your review. Life and Mana are not directly reduced; a universal mechanical Brick is not asserted.'
    if decision=='free':
        return 'free','Allowed by your reviewed Nightmare policy. This is an explicit selection preference, not proof of zero risk or zero damage loss. You can still block it manually.'
    raise ValueError('Unknown Nightmare policy decision: '+decision)


def assess_nightmare(profile, mods):
    catalogue=json.loads((ROOT/'nightmare_catalogue.json').read_text(encoding='utf-8'))
    policy=json.loads((ROOT/'nightmare_policy.json').read_text(encoding='utf-8'))
    by_id={row['id']:row for row in policy}
    if len(by_id)!=47 or set(by_id)!={row['id'] for row in catalogue}:
        raise ValueError('Nightmare review must cover exactly the current 47 unique modifiers.')
    results=[]
    for mod in catalogue:
        reviewed=by_id[mod['id']]
        rating,reason=reviewed_assessment(profile,reviewed['decision'])
        rule='nightmare_policy_'+reviewed['decision']
        axes=['delivery','activation','scaling'] if reviewed['decision'] in {'attack_hits','stun_dependency'} else ['defence','sustain']
        row=dict(id='map-'+mod['id'],name=mod['text'],pattern=mod['pattern'],rating=rating,
                 reason=f"Nightmare review #{reviewed['number']}. "+reason,confidence='low',nightmare_policy=True,
                 nightmare_review_number=reviewed['number'],nightmare_decision=reviewed['decision'])
        annotate_assessment(profile,row,rule)
        row.update(rule_id=rule,dependency_axes=axes,dependency_evidence=[d['evidence'] for d in profile.get('dependencies',[]) if d['axis'] in axes])
        results.append(row)
    return results
