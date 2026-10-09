"""Small, inspectable PoE 1 map-mod rule set for the first local version."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .build_signals import counter_rating, signal_by_id
from .assessment import assessed_rule, recovery_conflicts
from .dependencies import annotate_assessment


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
    Mod("reduced_recovery", "Reduced Recovery", "recovery rate of life"),
    Mod("minus_max_res", "Reduced Maximum Resistances", "maximum.*resistan"),
    Mod("extra_chaos", "Extra Chaos Damage", "extra chaos"),
    Mod("hexproof", "Hexproof Monsters", "hexproof"),
    Mod("reduced_auras", "Reduced Aura Effect", "reduced effect.*auras"),
    Mod("avoid_poison_bleed_impale", "Monsters Avoid Poison, Impale and Bleeding", "avoid poison, impale"),
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
    "safe": {"brick", "dangerous", "uncomfortable", "review"},
    "balanced": {"brick", "dangerous"},
    "greedy": {"brick"},
}
REGEX_LIMIT = 250


def _thorns_assessment(profile: dict, kind: str, flat_hit: int) -> tuple[str, str]:
    """Estimate exposure to flat Thorns from the main skill, not old % reflect."""
    if profile.get("uses_totems") or profile.get("uses_traps") or profile.get("uses_mines"):
        return "review", "The main skill uses totems, traps or mines. Player hit/mitigation assumptions do not establish the remote skill's Thorns interaction; review its damage delivery."
    types = profile.get("main_hit_types") or []
    skill = profile.get("main_skill", "Main skill")
    if not types:
        if profile.get("minion_damage_primary"):
            return "review", "The main skill uses minions; their hit types and Thorns mitigation are not established by this snapshot."
        if profile.get('main_damage_is_pure_dot') or ('main_damage_is_pure_dot' not in profile and profile.get("damage_type") in {"fire dot", "chaos dot"} and profile.get("main_skill_kind") == "non_attack"):
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
        measured = assessed_rule(profile, mod.id)
        if measured is not None:
            rating, reason = measured
        elif mod.id == "elemental_thorns":
            rating, reason = _thorns_assessment(profile, "elemental", 1500)
        elif mod.id == "physical_thorns":
            rating, reason = _thorns_assessment(profile, "physical", 800)
        elif mod.id == "combined_thorns":
            physical = _thorns_assessment(profile, "physical", 1500)
            elemental = _thorns_assessment(profile, "elemental", 2500)
            rating = max((physical[0], elemental[0]), key={"free": 0, "uncomfortable": 1, "review": 2, "dangerous": 3, "brick": 4}.get)
            reason = physical[1] + " " + elemental[1]
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
        elif mod.id == "avoid_ailments":
            if profile.get("uses_totems") and damage == "elemental" and not profile.get("ailment_damage_primary"):
                rating, reason = "free", "Elemental hit totems are detected; no required ailment mechanic is established. Optional chill/shock is not an automatic avoid choice."
            elif damage == "elemental":
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
            if profile.get("uses_totems") and "cooldown_loop" not in signals and not profile.get("main_skill_has_cooldown"):
                rating, reason = "free", "No cooldown dependency is detected for the main totem skill. Utility cooldowns such as Arcane Cloak can still be slower."
            if profile.get("automated_mine_detonation"):
                reason += " Some manual detonation is still possible."
        elif mod.id == "reduced_block_and_armour":
            rating, reason = counter_rating(profile, ("block", "armour", "armour_damage"))
            total_block = (profile.get("effective_attack_block") or 0) + (profile.get("effective_spell_block") or 0)
            if total_block >= 75:
                rating = "brick"
                reason = f"Your block-investment policy applies: attack plus spell block totals {total_block:g} percentage points (threshold 75). These are separate chances, not a combined hit-block probability. " + reason
            reason = "40% reduced chance to block and 30% less Armour. " + reason
        elif mod.id == "reduced_suppression_and_evasion":
            rating, reason = counter_rating(profile, ("suppression", "evasion"))
            if "suppression" not in signals and "evasion" not in signals and profile.get("spell_suppression") is not None and profile.get("evasion") is not None:
                rating, reason = "free", "Saved suppression and evasion show no substantial investment. Higher monster Accuracy and reduced suppression prevention are not an automatic avoid choice."
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
        confidence = "low" if rating == "review" else "medium"
        result.append(annotate_assessment(profile, {"id": mod.id, "name": mod.name, "pattern": mod.pattern, "rating": rating, "reason": reason, "confidence": confidence}))
    # Specific pool rolls override the generic group without changing old API IDs.
    context = json.loads((Path(__file__).parent / "map_rule_values.json").read_text(encoding="utf-8"))
    effect = 1 + profile.get("assumptions", {}).get("map_effect_increased", 0) / 100
    for row in context:
        value = row["worst_roll"] * effect
        assessed = assessed_rule(profile, row["rule"], value)
        if assessed is None:
            continue
        rating, reason = assessed
        result.append({"id": "map-" + row["id"], "name": row["name"], "pattern": row["pattern"],
                       "rating": rating, "reason": f"{row['pool'].title()} pool, worst catalogue roll; {effect:g}x map modifier effect. " + reason,
                       "confidence": "low" if rating == "review" else "medium"})
        annotate_assessment(profile, result[-1], row["rule"])
    conflicts = recovery_conflicts(profile)
    for row in result:
        matching = [conflict for conflict in conflicts if row["id"] == conflict["avoid"]]
        relevant = [conflict["reason"] for conflict in matching]
        if relevant:
            row["combination_avoid"] = True
            row["combination_reason"] = " ".join(relevant)
            row["combination_partners"] = [[mod for mod in conflict["mods"] if mod != row["id"]] for conflict in matching]
    return result


def make_regex(mods: list[dict], preset: str, overrides: dict[str, str] | None = None) -> dict:
    if preset not in PRESETS:
        raise ValueError("Unknown preset")
    overrides = overrides or {}
    blocked = []
    for mod in mods:
        if mod["id"].startswith("map-"):
            continue  # The frontend uses these for pool-specific ratings.
        choice = overrides.get(mod["id"])
        if choice == "avoid" or (choice != "allow" and (mod["rating"] in PRESETS[preset] or preset != "greedy" and mod.get("combination_avoid"))):
            blocked.append(mod)
    query = '"!' + "|".join(mod["pattern"] for mod in blocked) + '"' if blocked else ""
    return {
        "query": query,
        "count": len(blocked),
        "length": len(query),
        "within_limit": len(query) <= REGEX_LIMIT,
        "blocked_ids": [mod["id"] for mod in blocked],
    }
