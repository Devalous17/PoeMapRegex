"""Small, inspectable PoE 1 map-mod rule set for the first local version."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mod:
    id: str
    name: str
    pattern: str


# Patterns match displayed English map text. Keep them readable; shortening can
# come later after testing against a full current modifier corpus.
MODS = [
    Mod("elemental_reflect", "Elemental Reflect", "reflect.*elemental"),
    Mod("physical_reflect", "Physical Reflect", "reflect.*physical"),
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
]

PRESETS = {
    "safe": {"brick", "dangerous", "uncomfortable"},
    "balanced": {"brick", "dangerous"},
    "greedy": {"brick"},
}
REGEX_LIMIT = 250


def classify(profile: dict) -> list[dict]:
    damage = profile["damage_type"]
    leech = profile["life_leech"] + profile["mana_leech"] + profile["energy_shield_leech"]
    regen = profile["life_regen"] + profile["mana_regen"] + profile["energy_shield_regen"]
    result = []

    for mod in MODS:
        rating, reason = "review", "The saved PoB data does not prove whether this modifier is safe for your build."
        if mod.id == "elemental_reflect":
            if profile["reflect_protection_detected"]:
                rating, reason = "review", "Equipped item text mentions reflected-damage protection. Confirm that it covers this skill before allowing the map."
            elif damage == "elemental":
                rating, reason = "brick", f"{profile['main_skill']} is an elemental hit skill, and no reflected-damage protection was detected on equipped items."
            elif damage in {"physical", "chaos dot", "fire dot"}:
                rating, reason = "free", f"The selected main skill ({profile['main_skill']}) is not classified as an elemental hit skill. Check secondary skills."
        elif mod.id == "physical_reflect":
            if damage == "physical":
                rating, reason = "brick", f"{profile['main_skill']} is classified as a physical hit skill."
            elif damage in {"elemental", "chaos dot", "fire dot"}:
                if profile["has_minion_skills"]:
                    rating, reason = "review", "The main skill is not physical, but an equipped minion skill may deal reflected Physical damage."
                else:
                    rating, reason = "free", f"The selected main skill ({profile['main_skill']}) is not classified as a physical hit skill. Check secondary skills."
        elif mod.id == "no_leech":
            if leech > 0:
                resources = [label for label, key in (("Life", "life_leech"), ("Mana", "mana_leech"), ("Energy Shield", "energy_shield_leech")) if profile[key] > 0]
                rating, reason = "brick", f"PoB shows active {' / '.join(resources)} leech. This map modifier removes it."
            else:
                rating, reason = "free", "The saved PoB stats show no Life, Mana, or Energy Shield leech for the selected setup."
        elif mod.id == "no_regen":
            if profile["mana_regen"] > 0 and profile["mana_cost_per_second"] > 0 and profile["mana_leech"] == 0:
                rating, reason = "dangerous", "The build spends Mana and PoB shows Mana regeneration without Mana leech. Check other Mana recovery sources."
            elif regen > 0:
                rating, reason = "uncomfortable", "The build has regeneration that this modifier would remove."
            else:
                rating, reason = "free", "No meaningful regeneration appears in the saved PoB stats."
        elif mod.id == "reduced_recovery":
            if leech + regen > 0:
                rating, reason = "dangerous", "The build uses leech or regeneration, which a recovery penalty weakens."
            else:
                rating, reason = "review", "No leech or regeneration appears in the saved stats, but other recovery could still matter."
        elif mod.id == "minus_max_res":
            rating, reason = "dangerous", "Losing maximum elemental resistance increases incoming elemental damage."
        elif mod.id == "extra_chaos":
            chaos_res = profile["chaos_resistance"]
            if chaos_res is not None and chaos_res < 0:
                rating, reason = "dangerous", f"PoB shows {chaos_res:g}% Chaos Resistance. Extra Chaos damage is especially concerning."
            elif chaos_res is not None:
                rating, reason = "uncomfortable", f"PoB shows {chaos_res:g}% Chaos Resistance; extra Chaos damage still raises incoming damage."
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
            if profile.get("uses_cast_on_crit"):
                rating, reason = "brick", "The active build contains Cast on Critical Strike. Less Cooldown Recovery Rate slows triggered spells and can disrupt the attack-speed trigger timing that this damage loop depends on."
            elif profile.get("automated_mine_detonation"):
                rating, reason = "brick", "The main skill uses mines and Detonate Mines is linked with Automation. Less Cooldown Recovery Rate slows repeated detonation and can stall the build's clear loop; manual detonation is still possible."
            elif profile.get("uses_mines"):
                rating, reason = "dangerous", "Detonate Mines has a cooldown. Less Cooldown Recovery Rate slows repeated mine detonation and can make mapping much less smooth."
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
