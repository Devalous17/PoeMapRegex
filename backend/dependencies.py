"""Skill metadata and inspectable dependencies; never a combat simulator."""
from functools import lru_cache
import json
from pathlib import Path
import re

@lru_cache(maxsize=1)
def skill_metadata():
    data = json.loads((Path(__file__).parent / 'skill_metadata.json').read_text(encoding='utf-8'))
    return data['skills'], {row['name'].lower(): row for row in data['skills'].values()}, data['revision']

def enrich_profile(profile, root, stats, main_group, groups, item_text, main_item_text):
    by_id, by_name, revision = skill_metadata()
    enabled_groups = [g for g in groups if g.get('enabled') != 'false']
    gems = [g for group in enabled_groups for g in group.findall('Gem') if g.get('enabled') != 'false']
    main_gems = [g for g in main_group.findall('Gem') if g.get('enabled') != 'false'] if main_group is not None and main_group.get('enabled') != 'false' else []
    chosen = next((g for g in main_gems if g.get('nameSpec') == profile['main_skill']), None)
    meta = (by_id.get(chosen.get('skillId')) if chosen is not None else None) or by_name.get(profile['main_skill'].lower())
    tags = set(meta['tags']) if meta else set()
    supports = {g.get('nameSpec', '').lower().removesuffix(' support') for g in main_gems if 'Support' in g.get('gemId', '') or g is not chosen}
    unknown_skills = sorted({g.get('nameSpec', 'Unnamed skill') for g in gems if 'Support' not in g.get('gemId', '') and not by_id.get(g.get('skillId')) and g.get('nameSpec', '').lower() not in by_name and not g.get('nameSpec', '').lower().endswith(' support')})
    profile.update(skill_metadata_known=bool(meta), skill_metadata_revision=revision,
                   main_skill_tags=sorted(tags), unrecognized_skills=unknown_skills)
    profile['uses_totems'] = profile.get('uses_totems', False) or 'SummonsTotem' in tags or bool(supports & {'spell totem', 'ballista totem', 'ranged attack totem'})
    profile['uses_mines'] = profile.get('uses_mines', False) or bool(supports & {'blastchain mine', 'high-impact mine', 'locus mine', 'remote mine'})
    if meta:
        profile['main_skill_kind'] = 'attack' if 'Attack' in tags else 'non_attack' if 'Spell' in tags else 'unknown'
        profile['main_uses_channeling'] = 'Channel' in tags
        profile['uses_mines'] = profile.get('uses_mines', False) or 'RemoteMined' in tags
        profile['uses_traps'] = 'Trapped' in tags or 'trap' in supports or 'advanced traps' in supports
        profile['uses_brands'] = 'Brand' in tags
        # Minion buffs are not proof that minions are the main damage source.
        profile['minion_damage_primary'] = 'CreatesMinion' in tags or 'Minion' in tags and 'Attack' not in tags and 'Damage' not in tags
        # A saved global Cooldown stat can belong to a utility guard/movement
        # skill. For recognized skills, use the selected skill's metadata.
        profile['main_skill_has_cooldown'] = 'Cooldown' in tags
        if profile['damage_type'] == 'unknown' and 'DamageOverTime' in tags and 'Damage' not in tags:
            element = next((e.lower() for e in ['Chaos', 'Fire', 'Cold', 'Physical'] if e in tags), None)
            if element:
                profile['damage_type'] = element + ' dot'
        profile['main_damage_is_pure_dot'] = 'DamageOverTime' in tags and 'Damage' not in tags and not profile['minion_damage_primary']
        if profile['main_skill'].lower() in {'righteous fire', 'vaal righteous fire'}:
            # The Vaal activation's cooldown does not gate the continuing RF burn.
            profile['main_skill_has_cooldown'] = False
    core_coc = any('cast on critical strike' in s for s in supports)
    profile['uses_cast_on_crit'] = core_coc
    accuracy_sources = [line.strip() for line in item_text.splitlines()
                        if re.search(r'per \d+ accuracy rating', line)
                        and re.search(r'damage|attack speed|critical strike', line)]
    profile['accuracy_scaling_sources'] = accuracy_sources if profile['main_skill_kind'] == 'attack' else []
    profile['accuracy_scales_offence'] = bool(profile['accuracy_scaling_sources'])
    profile['main_accuracy'] = max((stats.get(key) or 0 for key in ('Accuracy', 'MainHandAccuracy', 'OffHandAccuracy')), default=0) or None
    linked_trigger = any('cast when damage taken' in s or 'cast while channelling' in s for s in supports)
    item_trigger = bool(re.search(r'trigger[^\n]*socketed[^\n]*(?:spell|skill)', main_item_text) and 'cooldown' in main_item_text)
    profile['main_trigger_detected'] = core_coc or linked_trigger or item_trigger
    profile['core_trigger_cooldown'] = core_coc or item_trigger
    # CwC uses a fixed trigger interval, not a CDR-scaled trigger cooldown.
    # An independently cooldown-based selected spell remains relevant.
    if any('cast when damage taken' in s for s in supports):
        profile['main_skill_has_cooldown'] = True
    profile['core_hex_trigger'] = 'Hex' in tags and any('impending doom' in s for s in supports)
    enabled_meta = [(by_id.get(g.get('skillId')) or by_name.get(g.get('nameSpec', '').lower())) for g in gems]
    profile['uses_auras'] = profile.get('uses_auras', False) or any(m and 'Aura' in m['tags'] and 'Hex' not in m['tags'] and 'Curse' not in m['tags'] for m in enabled_meta)
    profile['uses_hexes'] = profile.get('uses_hexes', False) or any(m and 'Hex' in m['tags'] for m in enabled_meta)
    # Damage shares are evidence only when the denominator is saved and positive.
    # CombinedDPS may be capped while ailment DPS is uncapped. Compare like
    # quantities using the corresponding hit-plus-ailment total when available.
    total = max((stats.get(key) or 0 for key in ('CombinedDPS', 'TotalDPS', 'WithPoisonDPS', 'WithBleedDPS', 'WithIgniteDPS')), default=0)
    ailment_shares = {kind: (stats.get(key) or 0) / total for kind, key in [('ignite', 'IgniteDPS'), ('poison', 'PoisonDPS'), ('bleed', 'BleedDPS')] if total > 0 and (stats.get(key) or 0) > 0}
    profile['primary_ailments'] = [kind for kind, share in ailment_shares.items() if share >= .5]
    if profile['primary_ailments']:
        profile['ailment_damage_primary'] = True
    profile['single_poison_main_skill'] = profile['main_skill'].lower() == 'viper strike of the mamba'
    profile['impale_damage_primary'] = total > 0 and (stats.get('ImpaleDPS') or 0) >= total * .5
    # These hints preserve Review for an unmeasured specialized ailment setup.
    # Ordinary elemental damage and chance to shock/chill are not reliance.
    profile['ailment_scaling_hints'] = {
        kind: any(word in ' '.join(supports) for word in words)
              or bool(re.search(item_pattern, item_text))
              or any(word in profile['main_skill'].lower() for word in skill_words)
        for kind, words, item_pattern, skill_words in [
            ('poison', ('poison', 'deadly ailments', 'unbound ailments'), r'poison damage|damage with poison|poison duration', ('viper strike', 'cobra lash', 'pestilent strike')),
            ('bleed', ('bleed', 'deadly ailments', 'unbound ailments'), r'bleeding damage|damage with bleeding', ('puncture', 'lacerate of haemorrhage')),
            ('ignite', ('ignite', 'deadly ailments', 'unbound ailments'), r'ignite damage|damage with ignites', ('burning arrow',)),
            ('impale', ('impale',), r'impale effect|impale damage', ()),
        ]}
    profile['saved_non_elemental_ailment_dps'] = {kind: stats.get(key) for kind, key in [('poison', 'PoisonDPS'), ('bleed', 'BleedDPS'), ('impale', 'ImpaleDPS')]}
    # Selected supports and equipped conditional modifiers establish a dependency,
    # not its contribution. Utility gems and unequipped items do not count.
    conditional = []
    if 'hypothermia' in supports and not profile.get('main_damage_is_pure_dot'):
        conditional.append(dict(ailments=['chill'], source='Linked Hypothermia',
                                evidence='The main skill links Hypothermia: its hit/ailment damage bonus requires a chilled enemy. Its cold DoT bonus is separate.'))
    for line in item_text.splitlines():
        if not re.search(r'(?:damage|critical strike)[^\n]*(?:chill|frozen|shock)|(?:chill|frozen|shock)[^\n]*(?:damage|critical strike)', line):
            continue
        if not re.search(r'against (?:chilled|frozen|shocked) enemies|(?:chill|shock) effect on enemy', line):
            continue
        ailments = [kind for word,kind in [('chill','chill'),('frozen','freeze'),('shock','shock')] if word in line]
        conditional.append(dict(ailments=ailments, source='Equipped conditional damage', evidence=line.strip()))
    profile['conditional_ailment_scaling'] = conditional
    dependencies = []
    def add(key, axis, label, status, evidence):
        dependencies.append(dict(id=key, axis=axis, label=label, status=status, evidence=evidence))
    delivery = ('minions' if profile.get('minion_damage_primary') else 'totems' if profile.get('uses_totems') else 'mines' if profile.get('uses_mines') else 'traps' if profile.get('uses_traps') else 'brands' if profile.get('uses_brands') else 'player')
    profile['damage_delivery'] = delivery
    add('delivery', 'delivery', delivery.title(), 'detected' if meta or profile.get('uses_totems') else 'uncertain', f"Selected main skill: {profile['main_skill']}; {delivery} delivery. A utility minion/totem does not determine this.")
    for key, enabled, label in [('primary_damage_aura', profile.get('primary_damage_aura'), 'Primary damage aura'), ('stun', profile.get('stun_dependent'), 'Stun-dependent clear'), ('cooldown', profile.get('core_trigger_cooldown') or profile.get('wardloop_detected') or profile.get('automated_mine_detonation'), 'Cooldown-based activation'), ('hex', profile.get('core_hex_trigger'), 'Hex-triggered damage'), ('armour_scaling', profile.get('armour_scales_attack_damage'), 'Armour scales attack damage')]:
        if enabled:
            add(key, 'activation' if key in {'cooldown', 'hex'} else 'scaling', label, 'detected', label + ' is established by the selected skill, linked supports or equipped modifiers.')
    for kind in profile['primary_ailments']:
        add(kind, 'scaling', kind.title() + ' damage', 'detected', f'Saved {kind} DPS is {ailment_shares[kind]:.0%} of saved total DPS; conditional damage is not recalculated.')
    if profile['impale_damage_primary']:
        add('impale', 'scaling', 'Impale damage', 'detected', 'Saved Impale DPS is at least half of the damage reference total.')
    if profile['single_poison_main_skill'] and 'poison' in profile['primary_ailments']:
        add('single_poison', 'activation', 'Single-poison application', 'detected', 'Viper Strike of the Mamba cannot inflict Poison on already-Poisoned enemies; failed initial applications interrupt normal damage delivery.')
    for i, condition in enumerate(conditional):
        add('conditional_ailment_' + str(i), 'scaling', condition['source'], 'detected', condition['evidence'] + ' Its share of total damage is not recalculated.')
    for attribute in sorted(set(re.findall(r'per \d+ (strength|dexterity|intelligence|maximum mana|maximum energy shield|armour|evasion)', item_text))):
        add('stack_' + attribute.replace(' ', '_'), 'scaling', attribute.title() + ' scaling', 'detected', 'Equipped modifier explicitly scales per ' + attribute + '; the size of this contribution is not recalculated.')
    if profile.get('accuracy_scales_offence'):
        add('stack_accuracy', 'scaling', 'Accuracy damage/speed scaling', 'detected',
            'Equipped offensive scaling per Accuracy: ' + '; '.join(profile['accuracy_scaling_sources'])
            + '. Saved Accuracy: ' + str(profile.get('main_accuracy') or 'not saved')
            + '; total damage contribution is not recalculated.')
    for row in profile.get('recovery_channels', []):
        if (row.get('value') or 0) > 0:
            add(row['pool'] + '_' + row['channel'], 'sustain', f"{row['pool']} {row['channel'].replace('_', ' ')}", 'detected', f"{row['value']:g} {row['unit']}; {row['condition']}")
    for signal in profile.get('signals', []):
        if signal['category'] in {'avoidance', 'mitigation'}:
            add(signal['id'], 'defence', signal['id'].replace('_', ' ').title(), 'detected', signal['evidence'])
    issues = []
    if not meta:
        issues.append('The main skill is not in the bundled skill metadata. Its offensive interactions need review.')
    if unknown_skills:
        issues.append('Unrecognized enabled skills: ' + ', '.join(unknown_skills[:5]) + '. Their extra dependencies have not been established.')
    if profile.get('uses_auras') and not profile.get('primary_damage_aura') and profile.get('assumptions', {}).get('aura_role', 'unknown') == 'unknown':
        issues.append('Supporting aura contribution is unmeasured; confirm whether it is essential.')
    if profile.get('uses_hexes') and not profile.get('core_hex_trigger') and profile.get('assumptions', {}).get('curse_role', 'unknown') == 'unknown':
        issues.append('Hex contribution is unmeasured; confirm whether it is essential.')
    if profile.get('minion_damage_primary') or profile.get('uses_totems'):
        issues.append('The saved player defences do not establish minion or totem durability.')
    profile['dependencies'] = dependencies
    profile['coverage'] = {'issues': issues, 'metadata_revision': revision, 'main_skill_recognized': bool(meta)}
    return profile

def dependency_assessment(profile, rule, value=None):
    """Only intervene where evidence is stronger than generic presence rules."""
    if rule == 'less_accuracy' and profile.get('accuracy_scales_offence'):
        penalty = min(100, max(0, 25 * (1 + profile.get('assumptions', {}).get('map_effect_increased', 0) / 100) if value is None else value))
        if penalty == 0:
            return 'free', 'This roll does not reduce Accuracy.'
        return 'dangerous', (f'{penalty:g}% less Accuracy also reduces the Accuracy-scaled offensive component, even if hit chance stays capped or hits cannot be evaded. '
                             + 'Equipped scaling: ' + '; '.join(profile.get('accuracy_scaling_sources', []))
                             + '. Balanced excludes this explicit offensive dependency; total DPS loss and attack-speed breakpoints are not recalculated, so a Brick is not asserted.')
    if rule == 'hexproof' and profile.get('core_hex_trigger') and not profile.get('assumptions', {}).get('hexproof_bypass', profile.get('hexproof_bypass_detected')):
        return 'brick', 'Impending Doom is linked to the selected main Hex. Hexproof prevents the required Hex without bypass; the core trigger cannot work normally.'
    if rule == 'reduced_cooldown' and profile.get('core_trigger_cooldown'):
        source = 'Cast on Critical Strike' if profile.get('uses_cast_on_crit') else 'a socketed item trigger'
        return 'brick', f'The selected main skill uses {source} with a cooldown. Reduced cooldown recovery disrupts normal activation; excluded by the core-trigger policy. Exact trigger throughput is not recalculated.'
    if rule == 'reduced_cooldown' and profile.get('skill_metadata_known') and not any(profile.get(key) for key in ('core_trigger_cooldown', 'main_skill_has_cooldown', 'wardloop_detected', 'automated_mine_detonation', 'uses_mines')):
        return 'free', f"The recognized main skill ({profile.get('main_skill', 'main skill')}) has no established cooldown, core trigger loop or mine-detonation dependency. Cooldown recovery does not gate its normal damage delivery. Utility movement/guard cooldowns may be slower; their uptime is not simulated."
    if rule in {'avoid_poison_bleed_impale', 'avoid_ailments'} and profile.get('ailment_damage_primary') and not profile.get('primary_ailments'):
        return 'review', 'Primary ailment damage is detected but its ailment type is unconfirmed. Review the affected avoidance mechanic.'
    if rule == 'avoid_poison_bleed_impale':
        affected = [kind for kind in ('poison', 'bleed') if kind in profile.get('primary_ailments', [])]
        if profile.get('impale_damage_primary'):
            affected.append('impale')
        avoid = min(100, 50 * (1 + profile.get('assumptions', {}).get('map_effect_increased', 0) / 100)) if value is None else min(100, value)
        if affected:
            single_poison = 'poison' in affected and profile.get('single_poison_main_skill')
            rating = 'brick' if avoid >= 100 or any(kind in affected for kind in ('poison', 'bleed')) else 'dangerous'
            reason = f'The main damage depends on {", ".join(affected)}. Monsters have {avoid:g}% chance to avoid Poison, Impale and Bleeding.'
            if single_poison:
                reason += ' Mamba relies on landing its initial poison and cannot poison already-Poisoned targets. Failed applications disrupt usual mapping; Brick is a conservative core-application exclusion, not a claim that 50% avoidance makes poison impossible.'
            elif avoid >= 100:
                reason += ' At 100% avoidance the required damage mechanic cannot be applied normally.'
            elif any(kind in affected for kind in ('poison', 'bleed')):
                reason += ' The saved main damage is ailment-dependent. Brick conservatively excludes unreliable primary damage application from usual mapping; this does not mean 50% avoidance is immunity or proves the map impossible.'
            else:
                reason += ' Avoidance reduces the primary Impale contribution; it does not prevent the attack itself.'
            return rating, reason
        if profile.get('main_damage_is_pure_dot'):
            return 'free', 'The selected main skill deals direct damage over time, not hit-applied Poison, Bleeding or Impale. Secondary damage mechanics still need review.'
        saved = profile.get('saved_non_elemental_ailment_dps', {})
        if len(saved) == 3 and all(value is not None and value == 0 for value in saved.values()):
            return 'free', 'Saved main-skill Poison, Bleeding and Impale DPS are all zero; none is an established primary damage mechanic.'
        if (profile.get('skill_metadata_known') and not profile.get('minion_damage_primary')
                and not any(profile.get('ailment_scaling_hints', {}).get(kind) for kind in ('poison', 'bleed', 'impale'))):
            return 'free', 'Optional-mechanic allowance: the recognized main skill has no detected primary Poison, Bleeding or Impale damage or specialized scaling setup. Incidental applications are not an automatic exclusion; missing exact contribution is not proof of zero loss.'
        return 'review', 'Poison, Bleeding or Impale contribution is missing or secondary. Do not assume this avoidance modifier is Free from damage type or class alone.'
    if rule == 'avoid_ailments' and profile.get('primary_ailments') and 'ignite' not in profile['primary_ailments'] and not set(profile.get('main_skill_tags', [])) & {'Fire', 'Cold', 'Lightning'} and not profile.get('conditional_ailment_scaling'):
        return 'free', 'The established main damage ailment is Poison or Bleeding, not an elemental ailment. Elemental ailment avoidance does not prevent Poison/Bleeding; secondary elemental-ailment dependencies still need review.'
    if rule == 'avoid_ailments' and 'ignite' in profile.get('primary_ailments', []):
        avoid = min(100, 70 * (1 + profile.get('assumptions', {}).get('map_effect_increased', 0) / 100) if value is None else value)
        return 'brick', f'Saved Ignite supplies at least half of total damage. At {avoid:g}% elemental ailment avoidance, applying the main damage ailment is {"prevented" if avoid >= 100 else "unreliable"}. Brick conservatively excludes unreliable primary damage application from usual mapping; below 100% this is not immunity. Poison and bleed are not elemental ailments.'
    if rule == 'avoid_ailments' and profile.get('conditional_ailment_scaling'):
        avoid = min(100, 70 * (1 + profile.get('assumptions', {}).get('map_effect_increased', 0) / 100) if value is None else value)
        sources = '; '.join(row['evidence'] for row in profile['conditional_ailment_scaling'])
        return 'dangerous', f'{avoid:g}% elemental ailment avoidance can interrupt conditional main-skill damage: {sources}. The bonus contribution and alternate ailment sources are unmeasured. This is not proof that the main skill stops functioning; review before allowing it.'
    if rule == 'avoid_ailments' and profile.get('skill_metadata_known') and not profile.get('minion_damage_primary'):
        if not profile.get('ailment_scaling_hints', {}).get('ignite'):
            return 'free', 'Optional-mechanic allowance: no primary Ignite damage or required elemental-ailment scaling is detected. Incidental chill, shock or freeze does not make elemental ailment avoidance an automatic exclusion.'
        return 'review', 'An Ignite scaling setup is detected but its primary damage contribution is not saved; review rather than assuming it is Free.'
    if rule in {'monster_crit_reduction', 'less_accuracy'} and profile.get('main_damage_is_pure_dot'):
        return 'free', 'The recognized main skill deals damage over time without hits or critical strikes. Secondary hit skills still need review.'
    if rule == 'reduced_cooldown' and profile.get('main_skill_has_cooldown') and not (profile.get('uses_cast_on_crit') or profile.get('wardloop_detected') or profile.get('automated_mine_detonation')):
        return 'review', 'The selected skill has a cooldown. Charge storage, uptime and replacement are not recalculated; absence of a known trigger loop does not prove this is Free.'
    return None

RULE_AXES = {
    'elemental_thorns': ['delivery', 'defence', 'sustain'], 'physical_thorns': ['delivery', 'defence', 'sustain'], 'combined_thorns': ['delivery', 'defence', 'sustain'],
    'no_leech': ['sustain'], 'no_regen': ['activation', 'sustain'], 'reduced_recovery': ['sustain'], 'reduced_leech': ['sustain'],
    'minus_max_res': ['defence'], 'extra_chaos': ['defence'], 'hexproof': ['activation', 'scaling'], 'reduced_auras': ['scaling', 'defence', 'sustain'],
    'avoid_poison_bleed_impale': ['activation', 'scaling'], 'avoid_ailments': ['activation', 'scaling'], 'less_accuracy': ['delivery', 'activation'], 'reduced_cooldown': ['activation'],
    'reduced_block_and_armour': ['defence', 'scaling'], 'reduced_suppression_and_evasion': ['defence'], 'charge_theft': ['activation', 'scaling', 'defence'],
    'reduced_flask_charges': ['sustain', 'defence'], 'reduced_monster_curse_effect': ['scaling', 'defence'], 'monster_crit_reduction': ['scaling'],
    'less_accuracy': ['scaling', 'activation'], 'less_player_aoe': ['scaling'], 'unstunnable_monsters': ['activation'], 'extra_projectiles': ['defence'], 'monster_crit': ['defence'], 'monster_life': ['scaling'],
}

def annotate_assessment(profile, row, rule=None):
    rule = rule or row['id']
    axes = RULE_AXES.get(rule, [])
    row['dependency_axes'] = axes
    row['dependency_evidence'] = [d['evidence'] for d in profile.get('dependencies', []) if d['axis'] in axes]
    row['assessment_status'] = 'uncertain' if row['rating'] == 'review' else 'unaffected' if row['rating'] == 'free' else 'counter'
    row['strict_avoid'] = row['rating'] == 'uncomfortable' and (rule in {'charge_theft', 'less_player_aoe'} or row.get('nightmare_policy', False))
    # Missing evidence must not masquerade as an explicitly unaffected mechanic.
    if row['rating'] == 'free' and profile.get('skill_metadata_known') is False and rule in {'avoid_ailments', 'reduced_cooldown', 'unstunnable_monsters', 'less_player_aoe', 'reduced_auras'}:
        row.update(rating='review', confidence='low', assessment_status='uncertain', reason='Unrecognized main skill: a missing dependency is not proof that this modifier is safe. ' + row['reason'])
    if row['rating'] == 'free' and profile.get('unrecognized_skills') and rule in {'reduced_auras'}:
        row.update(rating='review', confidence='low', assessment_status='uncertain', reason='Some enabled skills are unrecognized; their aura or curse interactions need review. ' + row['reason'])
    return row
