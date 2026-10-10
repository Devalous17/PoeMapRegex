"""Bounded snapshot models, not a Path of Building recalculation engine."""
import math
from .assessment import critical_damage_factor


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def estimate(profile, rule, value=None):
    result = dict(engine='saved_snapshot', status='unsupported', quantities=[],
                  limitations=['The complete build is not recalculated under this modifier.'])
    def quantity(name, before, after, unit):
        result['quantities'].append(dict(name=name, before=before, after=after, unit=unit))
    if rule == 'nightmare_penetration':
        penetration=15*(1+profile.get('assumptions',{}).get('map_effect_increased',0)/100)
        for element,resistance in profile.get('elemental_resistances',{}).items():
            resistance=number(resistance)
            if resistance is not None and resistance<100:
                quantity(element+' resistance-only hit damage',1,(100-resistance+penetration)/(100-resistance),'relative')
        if result['quantities']: result.update(status='estimated')
        result['limitations'].append('Hits only; conversion, immunity and other mitigation are excluded. Penetration does not increase RF self-burning.')
    elif rule == 'nightmare_less_defences':
        factor=max(0,1-.3*(1+profile.get('assumptions',{}).get('map_effect_increased',0)/100))
        for key,label in [('armour','Armour'),('evasion','Evasion'),('energy_shield','Energy Shield'),('ward','Ward')]:
            before=number(profile.get(key))
            if before is not None and before>0: quantity(label,before,before*factor,'stat')
        if result['quantities']: result.update(status='estimated')
        result['limitations'].append('Direct saved-stat scaling only; downstream damage, recovery, resource routing and conditional uptime are not recalculated.')
    elif rule == 'monster_crit_reduction':
        chance, multi = number(profile.get('crit_chance')), number(profile.get('crit_multiplier'))
        if profile.get('minion_damage_primary') or profile.get('primary_ailments') or profile.get('main_damage_is_pure_dot'):
            result['limitations'].append('Player hit-critical stats do not establish total minion or ailment damage.')
            return result
        if chance is not None and multi is not None:
            quantity('Expected main hit damage', 1, critical_damage_factor(chance, multi, 40 if value is None else value), 'relative')
            result.update(status='estimated')
            result['limitations'].append('Hit-only expectation; enemy mitigation, secondary skills and encounter thresholds are excluded.')
    elif rule == 'minus_max_res':
        loss = 12 if value is None else value
        for element in ('Fire', 'Cold', 'Lightning'):
            actual = number(profile.get('elemental_resistances', {}).get(element))
            cap = number(profile.get('maximum_resistances', {}).get(element))
            if actual is not None and cap is not None and actual < 100:
                after = min(actual, cap - loss)
                quantity(element + ' resistance', actual, after, '%')
                quantity(element + ' damage taken', 1, (100 - after) / (100 - actual), 'relative')
        if result['quantities']:
            result.update(status='estimated')
        result['limitations'].append('Resistance-only model; conversion, penetration and other mitigation are excluded.')
    elif rule in {'avoid_poison_bleed_impale', 'avoid_ailments'}:
        primary = set(profile.get('primary_ailments', []))
        affected = (bool(primary & {'poison','bleed'}) or profile.get('impale_damage_primary')) if rule == 'avoid_poison_bleed_impale' else ('ignite' in primary or profile.get('conditional_ailment_scaling'))
        if affected:
            avoid = value if value is not None else (50 if rule == 'avoid_poison_bleed_impale' else 70) * (1 + profile.get('assumptions', {}).get('map_effect_increased', 0) / 100)
            quantity('Applications passing this avoidance check', 100, max(0, 100 - avoid), '%')
            result.update(status='estimated')
            result['limitations'].append('This is not final ailment chance or a DPS multiplier. Hit rate, duration, existing ailments and alternate sources are unmeasured.')
    elif rule in {'no_regen', 'no_leech', 'reduced_recovery', 'reduced_leech'}:
        channels = profile.get('recovery_channels', [])
        assumptions = profile.get('assumptions', {})
        complete = True
        for pool in ('Life', 'Mana', 'EnergyShield'):
            values = {row['channel']: number(row.get('value')) for row in channels if row['pool'] == pool}
            regen, leech = values.get('regeneration'), values.get('leech')
            if regen is None or leech is None:
                complete = False
                continue
            recharge = (values.get('recharge') or 0) if assumptions.get('recharge_sustainable') else 0
            before = max(0, regen) + max(0, leech) + max(0, recharge)
            if pool == 'Mana':
                before += assumptions.get('mana_alternative_per_second', 0)
            after = before
            if rule == 'no_regen': after -= max(0, regen)
            if rule == 'no_leech': after -= max(0, leech)
            if rule == 'reduced_leech': after -= max(0, leech) * min(1, max(0, (60 if value is None else value) / 100))
            if rule == 'reduced_recovery' and pool != 'Mana': after *= max(0, 1 - (60 if value is None else value) / 100)
            quantity(pool + ' measured recovery', before, max(0, after), '/s')
            cost = number(profile.get('saved_mana_cost_per_second'))
            if pool == 'Mana' and cost is not None:
                quantity('Mana surplus after main skill cost', before - cost, max(0, after) - cost, '/s')
        if result['quantities']:
            result.update(status='estimated' if complete else 'partial')
        result['limitations'].append('Leech requires targets; unconfirmed recharge, flasks, recoup and gains are not guaranteed continuous income. Missing channels are not treated as zero.')
    return result
