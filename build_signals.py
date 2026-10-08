"""Conservative, inspectable signals inferred from one saved PoB snapshot.

Strength 1 means present, 2 means substantial, 3 means likely central to the
build. These are evidence levels, not a simulated post-map survival score.
"""

from __future__ import annotations


def _num(profile: dict, key: str) -> float:
    return float(profile.get(key) or 0)


def infer_build_signals(profile: dict) -> list[dict]:
    signals: list[dict] = []

    def add(key: str, category: str, strength: int, evidence: str) -> None:
        if strength:
            signals.append({"id": key, "category": category, "strength": strength, "evidence": evidence})

    attack_block = _num(profile, "effective_attack_block")
    spell_block = _num(profile, "effective_spell_block")
    block = max(attack_block, spell_block)
    add("block", "avoidance", 3 if block >= 85 else 2 if block >= 50 else 1 if block >= 20 else 0,
        f"{attack_block:g}% effective attack block / {spell_block:g}% effective spell block")

    for key, label, category in (("armour", "Armour", "mitigation"), ("evasion", "Evasion", "avoidance")):
        amount = _num(profile, key)
        add(key, category, 3 if amount >= 30_000 else 2 if amount >= 15_000 else 1 if amount >= 5_000 else 0,
            f"{amount:,.0f} {label}")

    suppression = _num(profile, "spell_suppression")
    add("suppression", "mitigation", 3 if suppression >= 90 else 2 if suppression >= 60 else 1 if suppression >= 30 else 0,
        f"{suppression:g}% effective spell suppression")
    if profile.get("armour_scales_attack_damage"):
        add("armour_damage", "offence", 3 if _num(profile, "armour") >= 15_000 else 2,
            f"equipped modifier grants Attack Damage per Armour; {_num(profile, 'armour'):,.0f} Armour currently contributes to damage")
    if profile.get("main_uses_channeling") and profile.get("main_hit_types"):
        add("channelled_hits", "offence", 2,
            f"{profile.get('main_skill', 'Main skill')} channels and produces player-owned hits")

    chaos = profile.get("chaos_resistance")
    if chaos is not None and not profile.get("chaos_immune") and not (_num(profile, "life") <= 1 and _num(profile, "energy_shield") > 0):
        add("chaos_exposure", "mitigation", 3 if chaos < 0 else 2 if chaos < 40 else 1 if chaos < 75 else 0,
            f"{chaos:g}% Chaos Resistance")

    life, es = _num(profile, "life"), _num(profile, "energy_shield")
    life_regen, es_regen = _num(profile, "life_regen"), _num(profile, "energy_shield_regen")
    life_leech, es_leech = _num(profile, "life_leech"), _num(profile, "energy_shield_leech")
    if life > 1 and life_leech > 0:
        rate = life_leech / life
        alternative = life_regen / life
        strength = 1 if alternative >= .04 else 2 if rate >= .03 else 1
        add("life_leech", "recovery", strength,
            f"{life_leech:,.0f} Life leech/s ({rate:.1%} of Life); {life_regen:,.0f} Life regeneration/s")
    if es > 0 and es_leech > 0:
        rate = es_leech / es
        alternative = es_regen / es
        strength = 3 if rate >= .1 and alternative < .02 else 2 if rate >= .03 else 1
        add("es_leech", "recovery", strength,
            f"{es_leech:,.0f} Energy Shield leech/s ({rate:.1%} of ES); {es_regen:,.0f} ES regeneration/s")

    mana_cost = _num(profile, "mana_cost_per_second")
    mana_regen, mana_leech = _num(profile, "mana_regen"), _num(profile, "mana_leech")
    mana_free = _num(profile, "mana_unreserved")
    mana_free_text = f"{mana_free:g}" if profile.get("mana_unreserved") is not None else "not saved"
    deficit_without_leech = max(0, mana_cost - mana_regen)
    deficit_without_regen = max(0, mana_cost - mana_leech)
    if mana_leech > 0:
        strength = 3 if deficit_without_leech >= 5 and mana_leech >= deficit_without_leech * .5 else 2 if deficit_without_leech > 0 else 1
        add("mana_leech", "resource", strength,
            f"{mana_cost:g} Mana/s spent, {mana_regen:g} regenerated, {mana_leech:g} leeched; {mana_free_text} unreserved")
    if mana_regen > 0:
        strength = 3 if deficit_without_regen >= 5 and mana_regen >= deficit_without_regen * .5 else 2 if deficit_without_regen > 0 else 1
        add("mana_regen", "resource", strength,
            f"{mana_cost:g} Mana/s spent, {mana_regen:g} regenerated, {mana_leech:g} leeched; {mana_free_text} unreserved")
    if life_regen > 0 and life > 1:
        add("life_regen", "recovery", 2 if life_regen / life >= .03 else 1,
            f"{life_regen:,.0f} Life regeneration/s ({life_regen / life:.1%} of Life)")
    net_life_regen = profile.get("life_net_regen")
    if life > 1 and life_regen > 0 and net_life_regen is not None:
        ongoing_life_loss = max(0, life_regen - float(net_life_regen))
        if ongoing_life_loss > 0:
            loss_share = ongoing_life_loss / life
            alternate_leech = life_leech >= ongoing_life_loss * .5
            strength = (3 if loss_share >= .05 and life_regen >= ongoing_life_loss and not alternate_leech
                        else 2 if loss_share >= .02 else 1)
            add("sustained_life_drain", "recovery", strength,
                f"PoB shows {ongoing_life_loss:,.0f} ongoing Life loss/s ({loss_share:.1%} of Life), offset by {life_regen:,.0f} Life regeneration/s; {profile.get('main_skill', 'main skill')} is selected")
    if es_regen > 0 and es > 0:
        add("es_regen", "recovery", 2 if es_regen / es >= .03 else 1,
            f"{es_regen:,.0f} Energy Shield regeneration/s ({es_regen / es:.1%} of ES)")

    if profile.get("uses_cast_on_crit"):
        add("cooldown_loop", "offence", 3, "Cast on Critical Strike in the active skill set")
    elif profile.get("wardloop_detected"):
        add("cooldown_loop", "offence", 3, "Heartbound Loop, Cast when Damage Taken, a looping minion, and Ward/Olroth's Resolve detected")
    elif profile.get("automated_mine_detonation"):
        add("cooldown_loop", "offence", 3, "main skill uses mines with automated Detonate Mines")
    elif profile.get("uses_mines"):
        add("cooldown_loop", "offence", 2, "main skill uses mines; repeated detonation has a cooldown")

    if profile.get("minion_damage_primary"):
        add("minions", "offence", 3, f"{profile.get('main_skill', 'Main skill')} is a minion damage skill")
    elif profile.get("has_minion_skills"):
        add("minions", "offence", 1, "enabled utility minion skill detected")

    return signals


def signal_by_id(profile: dict) -> dict[str, dict]:
    # Recalculate so tests and callers can change a profile after import.
    return {signal["id"]: signal for signal in infer_build_signals(profile)}


def counter_rating(profile: dict, affected: tuple[str, ...], *, floor: str = "review", stack_layers: bool = True) -> tuple[str, str]:
    """Rate an affix by which measured build layers it actually counters."""
    known = signal_by_id(profile)
    found = [known[key] for key in affected if key in known]
    if not found:
        return floor, "The saved PoB snapshot does not establish reliance on this affected mechanic. Review conditional effects."
    highest = max(signal["strength"] for signal in found)
    combined = sum(signal["strength"] for signal in found)
    rating = "brick" if highest == 3 or stack_layers and combined >= 4 else "dangerous" if highest == 2 else "uncomfortable"
    evidence = "; ".join(signal["evidence"] for signal in found)
    return rating, f"This affix counters measured build layers: {evidence}. Exact post-map values are not simulated."
