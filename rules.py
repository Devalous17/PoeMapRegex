"""Small, inspectable PoE 1 map-mod rule set for the first local version."""

from __future__ import annotations

from dataclasses import dataclass

from build_signals import counter_rating, signal_by_id


@dataclass(frozen=True)
class Mod:
    id: str
    name: str
    pattern: str


# Patterns match displayed English map text. Keep them readable; shortening can
# come later after testing against a full current modifier corpus.
MODS = [
    Mod("elemental_thorns", "Elemental Thorns", "elemental thorns"),
    Mod("physical_thorns", "Physical Thorns", "physical thorns"),
    Mod("combined_thorns", "Physical and Elemental Thorns", "thorns reflecting"),
    Mod("no_leech", "Cannot Leech", "cannot leech"),
    Mod("no_regen", "Cannot Regenerate", "cannot regen"),
    Mod("reduced_recovery", "Reduced Recovery", "recovery rate"),
    Mod("minus_max_res", "Reduced Maximum Resistances", "maximum.*resistan"),
    Mod("extra_chaos", "Extra Chaos Damage", "extra chaos"),
    Mod("hexproof", "Hexproof Monsters", "hexproof"),
    Mod("reduced_auras", "Reduced Aura Effect", "reduced effect.*auras"),
    Mod("avoid_ailments", "Monsters Avoid Elemental Ailments", "avoid elemental ailments"),
    Mod("extra_projectiles", "Additional Monster Projectiles", "additional projectiles"),
    Mod("monster_crit", "Increased Monster Critical Strikes", "critical strike chance"),
    Mod("monster_life", "Increased Monster Life", "increased maximum life"),
    Mod("less_accuracy", "Reduced Player Accuracy", "less accuracy rating"),
    Mod("reduced_cooldown", "Reduced Cooldown Recovery", "cooldown recovery rate"),
    Mod("reduced_block_and_armour", "Reduced Chance to Block and Armour", "reduced chance to block"),
    Mod("reduced_suppression_and_evasion", "Reduced Suppression and Evasion", "suppressed spell damage prevented"),
    Mod("reduced_leech", "Reduced Maximum Leech Recovery", "recovery per second from leech"),
    Mod("charge_theft", "Monsters Steal Charges", "steal.*charges"),
    Mod("reduced_flask_charges", "Reduced Flask Charges Gained", "reduced flask charges"),
    Mod("reduced_monster_curse_effect", "Less Curse Effect on Monsters", "less effect of curses on monsters"),
    Mod("monster_crit_reduction", "Monsters Take Reduced Critical Damage", "reduced extra damage from critical strikes"),
    Mod("less_player_aoe", "Less Player Area of Effect", "less area of effect"),
    Mod("unstunnable_monsters", "Monsters Cannot Be Stunned", "monsters cannot be stunned"),
]

PRESETS = {
    "safe": {"brick", "dangerous", "uncomfortable"},
    "balanced": {"brick", "dangerous"},
    "greedy": {"brick"},
}
REGEX_LIMIT = 250


def _thorns_assessment(profile: dict, kind: str, flat_hit: int) -> tuple[str, str]:
    """Estimate exposure to flat Thorns from the main skill, not old % reflect."""
    types = profile.get("main_hit_types") or []
    skill = profile.get("main_skill", "Main skill")
    if not types:
        if profile.get("minion_damage_primary"):
            return "review", "The main skill uses minions; their hit types and Thorns mitigation are not established by this snapshot."
        if profile.get("damage_type") in {"fire dot", "chaos dot"} and profile.get("main_skill_kind") == "non_attack":
            return "free", f"{skill} deals damage over time rather than player-owned hits. Check secondary hit skills."
        return "review", f"The saved main skill ({skill}) has no verified {kind} hit classification."
    if kind not in types:
        if profile.get("main_skill_kind") == "attack" and kind == "physical":
            return "review", "This attack is classified as elemental, but physical damage conversion is not fully calculated from the saved build."
        return "free", f"{skill} is not classified as dealing {kind} hits. Check secondary skills."
    if profile.get("reflect_protection_detected"):
        return "review", "Equipped item text mentions reflected-damage protection; confirm it applies to Thorns in the current setup."

    if kind == "physical":
        armour = float(profile.get("armour") or 0)
        after_hit = flat_hit * (5 * flat_hit) / (armour + 5 * flat_hit)
        mitigation = f"{armour:,.0f} Armour"
    else:
        element = profile.get("main_element")
        resistances = profile.get("elemental_resistances") or {}
        resistance = resistances.get(element) if element else None
        if resistance is None:
            known = [value for value in resistances.values() if value is not None]
            if not known:
                return "review", "Elemental Thorns can answer player-owned hits, but the saved elemental resistances are missing."
            resistance = min(known)
            element = "lowest saved elemental"
        after_hit = flat_hit * max(0, 1 - min(float(resistance), 100) / 100)
        mitigation = f"{resistance:g}% {element} Resistance"

    channel = " Channelling does not prevent the skill's hits from triggering Thorns." if profile.get("main_uses_channeling") else ""
    evidence = f"{skill} can trigger {kind.title()} Thorns: up to {flat_hit:,} flat damage before mitigation, roughly {after_hit:,.0f} after {mitigation} per trigger.{channel} Evasion, block, conditional effects, and actual hit rate are not simulated."
    if after_hit < 10:
        return "free", evidence
    pool = float(profile.get("life") or 0) + float(profile.get("energy_shield") or 0)
    if pool <= 0:
        return "review", evidence
    recovery = sum(float(profile.get(key) or 0) for key in ("life_regen", "life_leech", "energy_shield_regen", "energy_shield_leech"))
    # Thorns can affect the player at most once per 0.1 s per damage type.
    upper_rate = after_hit * 10
    rating = "dangerous" if upper_rate > recovery * 1.2 and upper_rate > pool * .1 else "uncomfortable"
    return rating, evidence


def classify(profile: dict) -> list[dict]:
    damage = profile["damage_type"]
    signals = signal_by_id(profile)
    result = []

    for mod in MODS:
        rating, reason = "review", "The saved PoB data does not prove whether this modifier is safe for your build."
        if mod.id == "elemental_thorns":
            rating, reason = _thorns_assessment(profile, "elemental", 1500)
        elif mod.id == "physical_thorns":
            rating, reason = _thorns_assessment(profile, "physical", 800)
        elif mod.id == "combined_thorns":
            physical = _thorns_assessment(profile, "physical", 1500)
            elemental = _thorns_assessment(profile, "elemental", 2500)
            rating = max((physical[0], elemental[0]), key={"free": 0, "uncomfortable": 1, "review": 2, "dangerous": 3, "brick": 4}.get)
            reason = physical[1] + " " + elemental[1]
        elif mod.id == "no_leech":
            rating, reason = counter_rating(profile, ("life_leech", "mana_leech", "es_leech"), stack_layers=False)
            if rating == "review":
                rating, reason = "free", "The saved PoB stats show no Life, Mana, or Energy Shield leech for the selected setup."
        elif mod.id == "no_regen":
            rating, reason = counter_rating(profile, ("mana_regen", "life_regen", "es_regen", "sustained_life_drain"), stack_layers=False)
            if rating == "review":
                rating, reason = "free", "No meaningful regeneration appears in the saved PoB stats."
        elif mod.id == "reduced_recovery":
            rating, reason = counter_rating(profile, ("life_leech", "es_leech", "life_regen", "es_regen"), stack_layers=False)
            if rating == "brick":
                rating = "dangerous"  # A 60% penalty is severe, but does not delete recovery.
            if rating == "review":
                reason = "No Life or Energy Shield recovery appears in the saved stats; flasks and gain on hit still need review."
        elif mod.id == "reduced_leech":
            rating, reason = counter_rating(profile, ("life_leech", "mana_leech", "es_leech"), stack_layers=False)
            if rating == "brick":
                rating = "dangerous"  # Lower leech maximum is not the same as no leech.
        elif mod.id == "minus_max_res":
            rating, reason = "dangerous", "Losing maximum elemental resistance increases incoming elemental damage."
        elif mod.id == "extra_chaos":
            rating, reason = counter_rating(profile, ("chaos_exposure",), floor="uncomfortable")
            if profile.get("chaos_immune"):
                rating, reason = "free", "The saved PoB reports an infinite Chaos maximum hit taken (Chaos immunity); negative Chaos Resistance does not imply vulnerability."
            elif profile.get("chaos_resistance") is not None and profile["chaos_resistance"] >= 75:
                rating, reason = "free", f"The saved build has {profile['chaos_resistance']:g}% Chaos Resistance. This is not an automatic avoid choice."
            elif (profile.get("life") or 0) <= 1 and (profile.get("energy_shield") or 0) > 0:
                rating, reason = "review", "Life is 1 with Energy Shield, which suggests Chaos Inoculation, but the saved stats do not explicitly confirm Chaos immunity."
            elif rating == "uncomfortable" and "chaos_exposure" not in signals:
                reason = "Extra Chaos damage still raises incoming damage; the saved Chaos Resistance does not show a clear vulnerability."
        elif mod.id == "hexproof":
            if profile["uses_hexes"]:
                rating, reason = "dangerous", "The active skill set contains a Hex; Hexproof can remove part of its benefit."
            else:
                rating, reason = "free", "No Hex was detected in the active skill set."
        elif mod.id == "reduced_auras":
            if profile["uses_auras"]:
                rating, reason = "dangerous", "The active skill set contains auras whose effect would be reduced."
            else:
                rating, reason = "free", "No common aura was detected in the active skill set."
        elif mod.id == "avoid_ailments":
            if damage == "elemental":
                rating, reason = "uncomfortable", "An elemental skill may lose chill, freeze, shock, or ignite utility."
        elif mod.id == "extra_projectiles":
            rating, reason = "uncomfortable", "More monster projectiles can make dodging and dense encounters harder."
        elif mod.id == "monster_crit":
            rating, reason = "uncomfortable", "Monster critical strikes can create damage spikes."
        elif mod.id == "monster_life":
            rating, reason = "uncomfortable", "More monster life slows clears; how much it matters depends on the encounter and PoB configuration."
        elif mod.id == "less_accuracy":
            if profile["main_skill_kind"] == "non_attack":
                rating, reason = "free", f"{profile['main_skill']} does not use Accuracy Rating to hit. Check secondary attacks."
            elif profile["main_skill_kind"] == "attack":
                rating, reason = "uncomfortable", "Reduced Accuracy can lower the main attack skill’s hit chance."
        elif mod.id == "reduced_cooldown":
            rating, reason = counter_rating(profile, ("cooldown_loop",))
            if profile.get("automated_mine_detonation"):
                reason += " Some manual detonation is still possible."
        elif mod.id == "reduced_block_and_armour":
            rating, reason = counter_rating(profile, ("block", "armour", "armour_damage"))
            reason = "40% reduced chance to block and 30% less Armour. " + reason
        elif mod.id == "reduced_suppression_and_evasion":
            rating, reason = counter_rating(profile, ("suppression", "evasion"))
            reason = "20 percentage points less suppressed spell damage prevented and higher monster Accuracy. " + reason
        elif mod.id == "charge_theft":
            relied_on = [kind for kind, maximum in (profile.get("maximum_charges") or {}).items()
                         if maximum is not None and maximum >= 5 and
                         ((profile.get("charge_generation") or {}).get(kind) or
                          ((profile.get("configured_charges") or {}).get(kind) or 0) >= 5)]
            if relied_on:
                rating, reason = "uncomfortable", f"This build has at least 5 maximum {', '.join(relied_on)} charges and either detected generation or 5+ configured active charges. Charge theft is a Safe-preset avoid choice; configured charges do not prove real uptime."
            else:
                rating, reason = "free", "No charge type meets both the 5-maximum threshold and detected generation or configured uptime. This is not automatically excluded."
        elif mod.id == "reduced_flask_charges":
            pathfinder = profile.get("ascendancy", "").lower() == "pathfinder"
            nature = profile.get("nature_adrenaline")
            traitor = profile.get("traitor_likely")
            flask_effect = profile.get("flask_effect_investment") or 0
            if traitor or pathfinder and (nature or flask_effect >= 100) and (profile.get("filled_flasks") or 0) >= 2:
                rating = "brick"
                flask_source = "Nature's Adrenaline" if nature else f"{flask_effect}% cumulative Flask Effect modifiers on equipped items"
                evidence = ("The Traitor is assumed active from the equipped Balbala setup and at least one empty flask slot" if traitor else
                            f"Pathfinder with {flask_source}")
                reason = f"{evidence} depends on flask charge supply; halving charges gained can break flask uptime. The export does not simulate uptime."
            else:
                rating, reason = "free", "No strong Pathfinder or Traitor flask-charge reliance was detected. Flask uptime remains a manual check."
        elif mod.id == "reduced_monster_curse_effect":
            if profile.get("curse_dependent"):
                rating, reason = "brick", "Anathema with active Hexes, Impending Doom, or another detected curse-dependent damage setup loses a central mechanic when curse effect on monsters is cut by 60%."
            else:
                rating, reason = "free", "No curse-dependent main damage setup was detected."
        elif mod.id == "monster_crit_reduction":
            chance, multiplier = profile.get("crit_chance"), profile.get("crit_multiplier")
            if chance is not None and multiplier is not None and chance >= 50 and multiplier >= 300:
                rating, reason = "brick", f"The selected skill has {chance:g}% Critical Strike Chance and {multiplier:g}% Critical Strike Multiplier. Reduced extra critical damage sharply cuts this build's damage."
            else:
                rating, reason = "free", "The selected skill does not meet both 50% critical chance and 300% critical multiplier in the saved PoB."
        elif mod.id == "less_player_aoe":
            scaled = profile.get("area_of_effect_increased") or 0
            if scaled >= 75:
                rating, reason = "uncomfortable", f"The saved build has at least {scaled:g}% increased Area of Effect; this modifier is excluded by the Safe preset only."
            else:
                rating, reason = "free", "The export does not show at least 75% increased Area of Effect; no automatic exclusion."
        elif mod.id == "unstunnable_monsters":
            if profile.get("stun_dependent"):
                rating, reason = "brick", f"{profile.get('main_skill', 'The main skill')} or its linked stun setup depends on stunning monsters for a core effect or area clear."
            else:
                rating, reason = "free", "No stun-triggered main damage or clear mechanic was detected."
        result.append({"id": mod.id, "name": mod.name, "pattern": mod.pattern, "rating": rating, "reason": reason})
    return result


def make_regex(mods: list[dict], preset: str, overrides: dict[str, str] | None = None) -> dict:
    if preset not in PRESETS:
        raise ValueError("Unknown preset")
    overrides = overrides or {}
    blocked = []
    for mod in mods:
        choice = overrides.get(mod["id"])
        if choice == "avoid" or (choice != "allow" and mod["rating"] in PRESETS[preset]):
            blocked.append(mod)
    query = '"!' + "|".join(mod["pattern"] for mod in blocked) + '"' if blocked else ""
    return {
        "query": query,
        "count": len(blocked),
        "length": len(query),
        "within_limit": len(query) <= REGEX_LIMIT,
        "blocked_ids": [mod["id"] for mod in blocked],
    }
