"""Measured modifier effects. Missing snapshot values remain unknown."""

from __future__ import annotations

import math
import re

CHANNELS = {
    "regeneration": ("RegenRecovery", "/s", "continuous"),
    "leech": ("LeechGainRate", "/s", "requires damage to a leechable target"),
    "recharge": ("Recharge", "/s", "requires recharge uptime"),
    "recoup": ("Recoup", "% of damage", "delayed; requires incoming hits"),
    "gain_on_hit": ("OnHit", "per hit", "requires a successful hit"),
    "gain_on_kill": ("OnKill", "per kill", "requires kills; unavailable on isolated bosses"),
}


def recovery_snapshot(stats: dict, item_text: str, flask_texts: list[str]) -> list[dict]:
    rows = []
    for pool in ("Life", "Mana", "EnergyShield"):
        for channel, (suffix, unit, condition) in CHANNELS.items():
            # Only stats actually present in the export are numeric evidence.
            value = stats.get(pool + suffix)
            label = pool.replace("EnergyShield", "energy shield").lower()
            text_evidence = channel == "recoup" and f"recouped as {label}" in item_text
            if channel in {"gain_on_hit", "gain_on_kill"}:
                trigger = r"(?:on hit|enemy hit)" if channel == "gain_on_hit" else r"(?:on kill|when you kill)"
                text_evidence = bool(re.search(rf"[^\n]*{label}[^\n]*{trigger}|[^\n]*{trigger}[^\n]*{label}", item_text))
            rows.append({"pool": pool, "channel": channel, "value": value,
                         "unit": unit, "condition": condition,
                         "source": pool + suffix if value is not None else "equipped item text; amount unmeasured" if text_evidence else "not saved"})
        rows.append({"pool": pool, "channel": "instant_leech", "value": None,
                     "unit": "unmeasured", "condition": "requires leech; removed by Cannot Leech",
                     "source": "item text" if "leech is instant" in item_text else "not saved"})
        flask_kind = {"Life": r"(?:life|hybrid) flask", "Mana": r"(?:mana|hybrid) flask", "EnergyShield": r"(?!)"}[pool]
        # A life flask mentioning Mana removal is not a Mana recovery source.
        flask_present = any(re.search(flask_kind, text.split("unique id:", 1)[0], re.I) for text in flask_texts)
        rows.append({"pool": pool, "channel": "flask", "value": None,
                     "unit": "unmeasured", "condition": "requires flask charges and uptime",
                     "source": "equipped flask" if flask_present else "not saved"})
    return rows


def _value(profile: dict, pool: str, channel: str) -> float | None:
    rows = profile.get("recovery_channels")
    if rows is not None:
        return next((row["value"] for row in rows if row["pool"] == pool and row["channel"] == channel), None)
    # Support callers with an already assembled profile, including regression cases.
    prefix = {"Life": "life", "Mana": "mana", "EnergyShield": "energy_shield"}[pool]
    suffix = {"regeneration": "regen", "leech": "leech", "recharge": "recharge"}.get(channel, channel)
    return profile.get(prefix + "_" + suffix)


def _potential_backup(profile: dict, pool: str) -> bool:
    return any(row["pool"] == pool and row["channel"] in {"recoup", "gain_on_hit", "gain_on_kill", "flask"}
               and (bool(row.get("value")) or row.get("source") not in {None, "not saved"})
               for row in profile.get("recovery_channels", []))


def recovery_assessment(profile: dict, modifier: str, penalty: float = 60) -> tuple[str, str]:
    assumptions = profile.get("assumptions", {})
    extra = assumptions.get("mana_alternative_per_second", 0)
    cost = profile.get("saved_mana_cost_per_second", profile.get("mana_cost_per_second"))
    results: list[tuple[str, str]] = []
    details = []

    def remaining(pool: str) -> tuple[float, float, bool]:
        regen, leech = _value(profile, pool, "regeneration"), _value(profile, pool, "leech")
        recharge = _value(profile, pool, "recharge") or 0
        # Recharge is a fallback, not guaranteed concurrent income during damage.
        sustainable_recharge = recharge if assumptions.get("recharge_sustainable") else 0
        base = max(0, regen or 0) + max(0, leech or 0) + sustainable_recharge
        after = base
        if modifier == "no_regen":
            after -= max(0, regen or 0)
        elif modifier == "no_leech":
            after -= leech or 0
        elif modifier == "reduced_leech":
            after -= (leech or 0) * penalty / 100
        elif modifier == "reduced_recovery" and pool != "Mana":
            after *= max(0, 1 - penalty / 100)
        return base, max(0, after), regen is not None and leech is not None

    if modifier != "reduced_recovery":
        base, after, known = remaining("Mana")
        base += extra
        after += extra
        if cost is None:
            results.append(("review", "The main skill's Mana/s cost is not saved."))
        elif cost > 0:
            details.append(f"Mana: {cost:g}/s cost, {base:g}/s measured income, {after:g}/s after this modifier.")
            if base < cost:
                results.append(("review", "Saved Mana income already falls below the cost before the modifier; confirm the missing sustain source."))
            elif after < cost:
                uncertain = _potential_backup(profile, "Mana") and not extra
                rating = "dangerous" if uncertain else "brick" if known else "review"
                seconds = (profile.get("mana_unreserved") or 0) / (cost - after)
                results.append((rating, f"Measured Mana sustain falls short by {cost-after:g}/s."
                                + (f" The saved free Mana buffer lasts about {seconds:.1f}s of continuous use." if seconds else "")
                                + (" Unmeasured conditional recovery may cover the gap." if uncertain else "")))
            elif base > after:
                results.append(("uncomfortable" if profile.get("mana_defence_detected") else "free",
                                "Remaining measured income covers the main skill's Mana cost; Mana used for defence still needs headroom."))

    pool = "EnergyShield" if (profile.get("life") or 0) <= 1 and (profile.get("energy_shield") or 0) > 0 else "Life"
    capacity = profile.get("energy_shield" if pool == "EnergyShield" else "life") or 0
    base, after, known = remaining(pool)
    regen = _value(profile, pool, "regeneration") or 0
    net = profile.get("life_net_regen") if pool == "Life" else profile.get("energy_shield_net_regen")
    drain = max(0, regen - net) if net is not None else 0
    recharge = _value(profile, pool, "recharge") or 0
    affected = max(0, base - after)
    if modifier == "reduced_leech" and profile.get("instant_leech_detected"):
        results.append(("review", "Instant leech is detected but not separated from timed leech; the leech-cap penalty cannot be calculated accurately."))
    if affected > 0:
        details.append(f"{pool}: {base:g}/s measured continuous recovery becomes {after:g}/s.")
        conditional = _potential_backup(profile, pool) or (recharge > 0 and not assumptions.get("recharge_sustainable"))
        if drain > after and base >= drain:
            results.append(("brick",
                            f"Remaining recovery cannot offset {drain:g}/s of saved ongoing {pool} loss."
                            + (" Conditional hits, kills and finite flask use are not assumed to cover continuous self-drain." if conditional else "")))
        elif capacity > 0 and affected >= capacity * .03 and after < capacity * .02:
            definite_leech_reliance = modifier == "no_leech" and affected >= capacity * .1
            results.append(("brick" if definite_leech_reliance and not conditional else "dangerous",
                            f"This removes the main measured {pool} recovery during combat."
                            + (" Recharge/conditional recovery remains, but uptime is not established." if conditional else "")))
        else:
            results.append(("dangerous" if capacity > 0 and affected >= capacity * .03 and after < base * .4 else "uncomfortable",
                            "Recovery is weakened; this alone does not demonstrate that the build stops functioning."))
    elif not known:
        results.append(("review", f"Complete {pool} regeneration and leech values are not saved."))
    elif modifier == "reduced_recovery" and (recharge or _potential_backup(profile, pool)):
        results.append(("dangerous", "Recovery over time, including recharge and recoup, is weakened; conditional rates cannot be treated as guaranteed income."))
    if not results:
        results.append(("free", "No measured affected recovery dependency was found."))
    rank = {"free": 0, "uncomfortable": 1, "review": 2, "dangerous": 3, "brick": 4}
    rating = max(results, key=lambda row: rank[row[0]])[0]
    explanations = [text for _, text in results]
    if modifier == "reduced_leech" and rating == "brick":
        rating = "dangerous"
        explanations.append("The leech-cap estimate does not recalculate additive cap modifiers or instant leech, so it cannot establish a Brick.")
    if modifier == "no_regen":
        explanations.append("Cannot Regenerate leaves recharge, leech, recoup, flasks and gain on hit/kill available where the build can use them.")
    if modifier == "reduced_recovery":
        explanations.append(f"Assumes {penalty:g}% less Life/ES recovery rate; Mana recovery and instant gains are not reduced by this affix.")
    return rating, " ".join(details + explanations)


def critical_damage_factor(chance: float, multiplier: float, reduction: float) -> float:
    c = min(1, max(0, chance / 100))
    m = max(1, multiplier / 100)
    r = min(1, max(0, reduction / 100))
    return (1 - c + c * (1 + (m - 1) * (1 - r))) / (1 - c + c * m)


def assessed_rule(profile: dict, rule: str, value: float | None = None) -> tuple[str, str] | None:
    from .dependencies import dependency_assessment
    dependency_result = dependency_assessment(profile, rule, value)
    if dependency_result is not None:
        return dependency_result
    assumptions = profile.get("assumptions", {})
    if rule in {"no_regen", "no_leech", "reduced_recovery", "reduced_leech"}:
        return recovery_assessment(profile, rule, 60 if value is None else value)
    if rule == "monster_crit_reduction":
        if profile.get("minion_damage_primary"):
            return "review", "Main damage comes from minions; player critical stats do not establish the minions' damage loss."
        if profile.get("damage_type", "").endswith(" dot"):
            if profile.get("main_skill", "").lower() in {"righteous fire", "vaal righteous fire", "death aura"}:
                return "free", f"{profile['main_skill']} deals damage over time without critically striking. Check secondary hit skills."
            return "review", "This build scales damage over time; a hit-only critical formula does not establish its total damage loss."
        c, m = profile.get("crit_chance"), profile.get("crit_multiplier")
        if c is None or m is None:
            return "review", "Saved critical chance or multiplier is missing; damage loss cannot be calculated."
        reduction = 40 if value is None else value
        factor = critical_damage_factor(c, m, reduction)
        loss = 1 - factor
        rating = "dangerous" if loss >= .4 else "uncomfortable" if loss >= .1 else "free"
        return rating, (f"At {reduction:g}% reduced extra critical damage, estimated main hit damage is {factor:.1%} of baseline ({loss:.1%} lower). "
                        "This estimates hit damage only; ailments, secondary skills and target-specific effects need review. Damage loss alone does not prove a Brick.")
    if rule == "minus_max_res":
        loss = 12 if value is None else value
        caps = profile.get("maximum_resistances", {})
        resistances = profile.get("elemental_resistances", {})
        factors = []
        details = []
        for element in ("Fire", "Cold", "Lightning"):
            cap, actual = caps.get(element), resistances.get(element)
            if cap is None or actual is None or actual >= 100:
                continue
            after = min(actual, cap - loss)
            factor = (100 - after) / (100 - actual)
            factors.append(factor)
            details.append(f"{element}: {actual:g}% to {after:g}% ({factor:.2f}x damage taken)")
        if not factors:
            return "review", f"Assumes -{loss:g} maximum resistances. Maximum caps are not established; saved resistance alone does not prove the cap."
        rating = "dangerous" if max(factors) >= 1.5 else "uncomfortable" if max(factors) > 1 else "free"
        return rating, "; ".join(details) + ". Resistance-only estimate, before conversion, penetration and other mitigation. No encounter-specific lethal threshold is assumed."
    if rule == "hexproof":
        bypass = assumptions.get("hexproof_bypass", profile.get("hexproof_bypass_detected", False))
        if bypass:
            return "free", "Hexproof bypass is detected or confirmed; Hexproof also does not disable Marks."
        if not profile.get("uses_hexes"):
            return "free", "No enabled Hex detected. Marks are not affected by Hexproof."
        role = assumptions.get("curse_role", "unknown")
        if role == "mechanic":
            return "brick", "You confirmed that functioning Hexes are required for the build's core mechanic, and no Hexproof bypass is active."
        if role == "damage":
            return "dangerous", "You confirmed important Hex damage contribution. Its size is not recalculated from this snapshot."
        if role == "utility":
            return "uncomfortable", "You confirmed utility Hexes; losing their benefit may affect comfort or defence."
        return "review", "Hexes are enabled, but their contribution and any tree-based Hexproof bypass are not calculated. Confirm their role below."
    if rule == "reduced_monster_curse_effect":
        if not profile.get("uses_hexes") and not profile.get("uses_marks"):
            return "free", "No enabled Hex or Mark detected."
        role = assumptions.get("curse_role", "unknown")
        if role == "utility":
            return "uncomfortable", "Less curse effect weakens confirmed utility curses."
        if role in {"damage", "mechanic"} or profile.get("curse_dependent"):
            return "dangerous", "Less curse effect weakens curse benefits; Anathema or Impending Doom presence alone does not prove that reduced effect disables the build."
        return "review", "Curse contribution is unmeasured. Reduced effect does not inherently remove curse application or curse triggers."
    if rule == "reduced_auras":
        if profile.get("primary_damage_aura"):
            reduction = 60 if value is None else value
            return "brick", (f"{profile.get('main_skill', 'Main skill')} is the selected primary damage aura. "
                f"{reduction:g}% reduced non-curse aura effect directly counters its chaos damage over time, "
                "as well as supporting non-curse auras. Excluded as Brick under the core-skill policy; "
                "this does not prove zero damage or inevitable death. Actual loss depends on increased aura effect and map effect.")
        if not profile.get("uses_auras"):
            return "free", "No supported enabled aura was detected; secondary or unfamiliar aura skills still need review."
        role = assumptions.get("aura_role", "unknown")
        if role == "utility":
            return "uncomfortable", "You confirmed utility auras; reduced aura effect weakens their benefits."
        if role in {"damage", "defence", "mechanic"}:
            return "dangerous", "You confirmed important aura contribution. Reduced effect weakens it; exact damage, defence and sustain changes require recalculation."
        return "review", "Auras are enabled, but their contribution is not recalculated. Confirm their role; presence alone does not establish a Brick."
    if rule == "reduced_flask_charges" and "flask_essential" in assumptions:
        return ("brick", "You confirmed essential flask uptime; reduced charge supply can stop the usual setup.") if assumptions["flask_essential"] else ("uncomfortable", "You confirmed flasks are optional for the usual setup; charge supply is still reduced.")
    if rule == "charge_theft" and assumptions.get("charge_sustain") == "reliable":
        return "uncomfortable", "You confirmed rapid charge recovery. Theft still causes temporary losses when hit, so it is excluded by Safe only."
    if rule == "charge_theft" and assumptions.get("charge_sustain") == "required":
        return "dangerous", "You confirmed that losing charges disrupts the build. Theft rate versus generation is not simulated, so a guaranteed Brick is not claimed."
    return None


def validate_assumptions(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Build confirmations must be an object.")
    result = {}
    for key, value in data.items():
        if key in {"mana_alternative_per_second", "map_effect_increased"}:
            maximum = 1_000_000 if key == "mana_alternative_per_second" else 300
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= maximum:
                raise ValueError(f"Invalid {key} value.")
        elif key in {"recharge_sustainable", "hexproof_bypass", "flask_essential"}:
            if not isinstance(value, bool):
                raise ValueError(f"Invalid {key} confirmation.")
        elif key == "curse_role":
            if not isinstance(value, str) or value not in {"unknown", "utility", "damage", "mechanic"}:
                raise ValueError("Invalid curse role.")
        elif key == "aura_role":
            if not isinstance(value, str) or value not in {"unknown", "utility", "damage", "defence", "mechanic"}:
                raise ValueError("Invalid aura role.")
        elif key == "charge_sustain":
            if not isinstance(value, str) or value not in {"unknown", "reliable", "required"}:
                raise ValueError("Invalid charge sustain.")
        else:
            raise ValueError("Unknown build confirmation.")
        result[key] = value
    return result


def recovery_conflicts(profile: dict) -> list[dict]:
    """Find pairs whose combined loss crosses a measured sustain requirement."""
    from itertools import combinations
    conflicts = []
    assumptions = profile.get("assumptions", {})
    penalty = min(1, .6 * (1 + assumptions.get("map_effect_increased", 0) / 100))
    cost = profile.get("saved_mana_cost_per_second", profile.get("mana_cost_per_second"))
    health_pool = "EnergyShield" if (profile.get("life") or 0) <= 1 else "Life"
    for pair in combinations(("no_regen", "no_leech", "reduced_recovery"), 2):
        for pool in ("Mana", health_pool):
            regen = _value(profile, pool, "regeneration")
            leech = _value(profile, pool, "leech")
            if regen is None or leech is None:
                continue
            extra = assumptions.get("mana_alternative_per_second", 0) if pool == "Mana" else 0
            if assumptions.get("recharge_sustainable"):
                extra += _value(profile, pool, "recharge") or 0
            def income(modifiers):
                r = 0 if "no_regen" in modifiers else regen
                l = 0 if "no_leech" in modifiers else leech
                multiplier = 1 - penalty if pool != "Mana" and "reduced_recovery" in modifiers else 1
                # Confirmed additional Mana recovery is untouched by the Life/ES affix.
                return (r + l + extra) * multiplier
            baseline, combined = income(()), income(pair)
            net = profile.get("life_net_regen" if pool == "Life" else "energy_shield_net_regen")
            requirement = cost if pool == "Mana" else max(0, regen - net) if net is not None else 0
            if requirement and baseline >= requirement and combined < requirement and all(income((mod,)) >= requirement for mod in pair):
                conflicts.append({"mods": list(pair), "avoid": pair[0],
                                  "reason": f"Together these modifiers leave {combined:g} {pool}/s against a measured {requirement:g}/s requirement. Each alone leaves enough. Balanced/Safe avoid one member of this pair."})
                break
    return conflicts
