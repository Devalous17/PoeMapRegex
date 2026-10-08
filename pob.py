"""Read Path of Building 1 exports without running the PoB calculation engine."""

from __future__ import annotations

import base64
import math
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib


MAX_INPUT = 300_000
MAX_XML = 2_000_000
POBB_LINK = re.compile(r"^https?://(?:www\.)?pobb\.in/([A-Za-z0-9_-]{3,64})/?(?:\?.*)?$", re.I)
CODE = re.compile(r"^[A-Za-z0-9_-]+={0,2}$")


class BuildInputError(ValueError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise BuildInputError("pobb.in redirected the build download; please paste the export code instead.")


def load_code(source: str) -> str:
    source = source.strip()
    if not source or len(source) > MAX_INPUT:
        raise BuildInputError("Paste a pobb.in link or a PoB export code (up to 300 KB).")
    match = POBB_LINK.fullmatch(source)
    if match:
        url = f"https://pobb.in/pob/{match.group(1)}"
        request = urllib.request.Request(url, headers={"User-Agent": "PoE-Map-Regex-Local/0.1"})
        try:
            with urllib.request.build_opener(_NoRedirect).open(request, timeout=12) as response:
                raw = response.read(MAX_INPUT + 1)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise BuildInputError(f"Could not download this pobb.in build: {exc}") from exc
        if len(raw) > MAX_INPUT:
            raise BuildInputError("The pobb.in export is too large.")
        try:
            source = raw.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise BuildInputError("pobb.in did not return a text export code.") from exc
    if not CODE.fullmatch(source):
        raise BuildInputError("This is not a supported pobb.in link or PoB export code.")
    return source


def decode_build(source: str) -> ET.Element:
    code = load_code(source)
    try:
        compressed = base64.urlsafe_b64decode(code + "=" * (-len(code) % 4))
        inflater = zlib.decompressobj()
        xml = inflater.decompress(compressed, MAX_XML + 1)
        if len(xml) > MAX_XML or inflater.unconsumed_tail or not inflater.eof:
            raise BuildInputError("The decoded build is too large or incomplete.")
    except (ValueError, zlib.error) as exc:
        if isinstance(exc, BuildInputError):
            raise
        raise BuildInputError("The export code could not be decoded.") from exc
    if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
        raise BuildInputError("This XML export contains unsupported entities.")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise BuildInputError("The decoded build is not valid XML.") from exc
    if root.tag != "PathOfBuilding":
        raise BuildInputError("This is not a Path of Building export.")
    return root


def _number(value: str | None) -> float | None:
    try:
        result = float(value) if value is not None else None
    except ValueError:
        return None
    return result if result is not None and math.isfinite(result) else None


def _active_skill(root: ET.Element, build: ET.Element) -> tuple[str, list[str]]:
    skills = root.find("Skills")
    if skills is None:
        return "Unknown", []
    active_set = skills.get("activeSkillSet", "1")
    skill_set = next((s for s in skills.findall("SkillSet") if s.get("id") == active_set), None)
    groups = skill_set.findall("Skill") if skill_set is not None else skills.findall("Skill")
    if not groups:
        return "Unknown", []
    all_gems = [g.get("nameSpec", "") for group in groups for g in group.findall("Gem") if g.get("enabled") != "false"]
    try:
        main_index = int(build.get("mainSocketGroup", "1")) - 1
        main_group = groups[main_index]
    except (ValueError, IndexError):
        return "Unknown", all_gems
    active_gems = [g for g in main_group.findall("Gem") if g.get("enabled") != "false"]
    try:
        gem_index = int(main_group.get("mainActiveSkill", "1")) - 1
        chosen = active_gems[gem_index]
    except (ValueError, IndexError):
        chosen = None
    # Some PoB exports point mainActiveSkill at a support gem in the raw XML.
    # Use the first enabled active gem in that socket group in that case.
    if chosen is None or not chosen.get("nameSpec") or "SupportGem" in chosen.get("gemId", ""):
        chosen = next((g for g in active_gems if g.get("nameSpec") and "SupportGem" not in g.get("gemId", "")), None)
    name = chosen.get("nameSpec", "Unknown") if chosen is not None else "Unknown"
    return name, all_gems


def _equipped_item_text(root: ET.Element) -> str:
    items = root.find("Items")
    if items is None:
        return ""
    active_id = items.get("activeItemSet", "1")
    active_set = next((s for s in items.findall("ItemSet") if s.get("id") == active_id), None)
    if active_set is None:
        return ""
    active_items = {slot.get("itemId") for slot in active_set.findall("Slot") if "Swap" not in slot.get("name", "")}
    return "\n".join(item.text or "" for item in items.findall("Item") if item.get("id") in active_items)


# A small, explicit skill table. Unknown skills remain unknown rather than being
# assigned a damage type from their name or ascendancy.
SKILL_DAMAGE = {
    "winter orb": "elemental",
    "arc": "elemental",
    "lightning arrow": "elemental",
    "ice shot": "elemental",
    "frost blades": "elemental",
    "fireball": "elemental",
    "righteous fire": "fire dot",
    "cyclone": "physical",
    "boneshatter": "physical",
    "earthquake": "physical",
    "toxic rain": "chaos dot",
    "essence drain": "chaos dot",
    "lacerate of haemorrhage": "physical",
    "smite": "elemental",
}

ATTACK_SKILLS = {"lightning arrow", "ice shot", "frost blades", "cyclone", "boneshatter", "earthquake", "toxic rain", "lacerate of haemorrhage", "smite"}
NON_ATTACK_SKILLS = {"winter orb", "arc", "fireball", "righteous fire", "essence drain"}
SKILL_ELEMENT = {"winter orb": "Cold", "lightning arrow": "Lightning", "ice shot": "Cold", "frost blades": "Cold", "arc": "Lightning", "fireball": "Fire", "smite": "Lightning"}
CHANNELLED_SKILLS = {"winter orb", "cyclone", "blade flurry", "divine ire", "storm burst", "scorching ray", "incinerate", "flameblast"}


def build_profile(root: ET.Element) -> dict:
    build = root.find("Build")
    if build is None:
        raise BuildInputError("The export has no Build section.")
    stats = {stat.get("stat", ""): _number(stat.get("value")) for stat in build.findall("PlayerStat")}
    chaos_immune = any(stat.get("stat") == "ChaosMaximumHitTaken" and
                       stat.get("value", "").lower() in {"inf", "infinity"}
                       for stat in build.findall("PlayerStat"))
    skill, gems = _active_skill(root, build)
    skills = root.find("Skills")
    active_set = skills.get("activeSkillSet", "1") if skills is not None else "1"
    skill_set = next((s for s in skills.findall("SkillSet") if s.get("id") == active_set), None) if skills is not None else None
    groups = skill_set.findall("Skill") if skill_set is not None else skills.findall("Skill") if skills is not None else []
    try:
        main_group = groups[int(build.get("mainSocketGroup", "1")) - 1]
    except (ValueError, IndexError):
        main_group = None
    main_gems = [g for g in main_group.findall("Gem") if g.get("enabled") != "false"] if main_group is not None else []
    main_ids = [g.get("gemId", "") for g in main_gems]
    mine_supports = ("SupportGemHighImpactMine", "SupportGemRemoteMine", "SupportGemBlastchainMine", "SupportGemLocusMine", "SupportGemMinefield")
    uses_mines = any(any(marker in gem_id for marker in mine_supports) for gem_id in main_ids) or skill.lower().endswith(" mine")
    automated_mine_detonation = uses_mines and any(
        {"Detonate Mines", "Automation"}.issubset({g.get("nameSpec", "") for g in group.findall("Gem") if g.get("enabled") != "false"})
        for group in groups
    )
    uses_cast_on_crit = any("cast on critical strike" in gem.lower() for gem in gems)
    item_text = _equipped_item_text(root).lower()
    gem_names = {gem.lower() for gem in gems}
    selected_tree = root.find("Tree")
    active_spec = selected_tree.get("activeSpec", "1") if selected_tree is not None else "1"
    specs = selected_tree.findall("Spec") if selected_tree is not None else []
    spec = specs[int(active_spec) - 1] if active_spec.isdigit() and 0 < int(active_spec) <= len(specs) else None
    allocated_nodes = set((spec.get("nodes", "") if spec is not None else "").split(","))
    item_set = root.find("Items")
    active_items = item_set.get("activeItemSet", "1") if item_set is not None else "1"
    equipped_set = next((s for s in item_set.findall("ItemSet") if s.get("id") == active_items), None) if item_set is not None else None
    occupied_flask_slots = sum(bool(slot.get("itemId")) for slot in equipped_set.findall("Slot") if re.fullmatch(r"Flask [1-5]", slot.get("name", ""))) if equipped_set is not None else 0
    empty_flask_slots = 5 - occupied_flask_slots if equipped_set is not None else None
    flask_ids = {slot.get("itemId") for slot in equipped_set.findall("Slot") if re.fullmatch(r"Flask [1-5]", slot.get("name", "")) and slot.get("itemId")} if equipped_set is not None else set()
    flask_item_texts = [(item.text or "").lower() for item in item_set.findall("Item") if item.get("id") in flask_ids and "tincture" not in (item.text or "").lower().split("unique id:", 1)[0]] if item_set is not None else []
    filled_flasks = len(flask_item_texts)
    main_skill_lower = skill.lower()
    damage_type = SKILL_DAMAGE.get(main_skill_lower, "unknown")
    main_uses_channeling = main_skill_lower in CHANNELLED_SKILLS or any("channelling" in g.get("nameSpec", "").lower() for g in main_gems)
    main_hit_types = (["physical", "elemental"] if main_skill_lower == "smite" else
                      [damage_type] if damage_type in {"physical", "elemental"} else [])
    armour_scales_attack_damage = bool(re.search(r"increased attack damage per \d+ armour", item_text))
    charge_generators = {
        "Power": bool(re.search(r"(?:gain|generate)[^\n]{0,45}power charge|power charge on critical strike|power charge on hit", item_text)
                      or "power charge on critical strike" in gem_names),
        "Frenzy": bool(re.search(r"(?:gain|generate)[^\n]{0,45}frenzy charge|frenzy charge on hit", item_text)
                       or {"frenzy", "blood rage"} & gem_names),
        "Endurance": bool(re.search(r"(?:gain|generate)[^\n]{0,45}endurance charge|endurance charge on hit", item_text)
                          or {"enduring cry", "endurance charge on melee stun"} & gem_names),
    }
    flask_effect_lines = re.findall(r"(\d+)% increased (?:effect of flasks|flask effect|effect of magic utility flasks)", item_text)
    flask_effect_investment = sum(int(value) for value in flask_effect_lines)
    flask_effect_investment += sum(int(value) for flask_text in flask_item_texts for value in re.findall(r"(\d+)% increased effect(?:\n|$)", flask_text))
    nature_adrenaline = "51101" in allocated_nodes
    # For this tool, Balbala plus any empty flask slot is treated as an active
    # The Traitor setup. One empty slot is enough; a filled flask must benefit.
    traitor_likely = (empty_flask_slots or 0) >= 1 and filled_flasks >= 1 and ("the traitor" in item_text or "brutal restraint" in item_text and "balbala" in item_text)
    active_hexes = gem_names & {"frostbite", "flammability", "conductivity", "despair", "elemental weakness", "enfeeble", "temporal chains", "vulnerability", "punishment"}
    curse_dependent = ("anathema" in item_text or "impending doom" in gem_names or
                       len(active_hexes) >= 2 or main_skill_lower == "hexblast" and bool(active_hexes))
    crit_chance = stats.get("CritChance")
    raw_multi = stats.get("CritMultiplier")
    crit_multiplier = raw_multi * 100 if raw_multi is not None and raw_multi <= 20 else raw_multi
    area_multiplier = stats.get("AreaOfEffectMod")
    area_increased = (area_multiplier - 1) * 100 if area_multiplier is not None and 0 < area_multiplier <= 5 else stats.get("AreaOfEffectIncrease")
    if area_increased is None:
        area_increased = sum(int(value) for value in re.findall(r"(\d+)% increased area of effect", item_text))
    stun_dependent = main_skill_lower.startswith("boneshatter") or ("stun support" in {g.get("nameSpec", "").lower() for g in main_gems} and bool(re.search(r"when you stun|on stunning|on stun", item_text)))
    minion_names = ("animate guardian", "raise zombie", "raise spectre", "summon ", "carrion golem", "stone golem", "flame golem", "chaos golem", "ice golem", "lightning golem", "holy relic", "dominating blow")
    has_minion_skills = any(g.lower().startswith(minion_names) for g in gems)
    minion_damage_primary = skill.lower().startswith(("raise zombie", "raise spectre", "summon ", "carrion golem", "stone golem", "flame golem", "chaos golem", "ice golem", "lightning golem", "holy relic", "dominating blow"))
    wardloop_detected = (
        "heartbound loop" in item_text
        and any("cast when damage taken" in g.lower() for g in gems)
        and any(g.lower().startswith(("summon skeleton", "raise zombie of falling")) for g in gems)
        and ((stats.get("Ward") or 0) > 0 or "olroth's resolve" in item_text)
    )
    effective_attack_block = stats.get("EffectiveBlockChance")
    effective_spell_block = stats.get("EffectiveSpellBlockChance")
    armour = stats.get("Armour")
    evasion = stats.get("Evasion")
    spell_suppression = stats.get("EffectiveSpellSuppressionChance")
    strongest_block = max(effective_attack_block or 0, effective_spell_block or 0)
    defence_archetypes = []
    if strongest_block >= 85:
        defence_archetypes.append("High block")
    elif strongest_block >= 50:
        defence_archetypes.append("Block")
    if (armour or 0) >= 15_000:
        defence_archetypes.append("Armour")
    if (evasion or 0) >= 15_000:
        defence_archetypes.append("Evasion")
    if (spell_suppression or 0) >= 60:
        defence_archetypes.append("Spell suppression")
    if not defence_archetypes:
        defence_archetypes.append("Unclear from saved stats")
    attack_archetype = (
        "Cast on Critical Strike" if uses_cast_on_crit else
        "Wardloop" if wardloop_detected else
        "Mines" if uses_mines else
        "Minions" if minion_damage_primary else
        "Bleed attack" if skill.lower() == "lacerate of haemorrhage" else
        "Attack" if skill.lower() in ATTACK_SKILLS else
        "Non-attack" if skill.lower() in NON_ATTACK_SKILLS else
        "Unclear from saved skill"
    )
    profile = {
        "game": "Path of Exile 1",
        "class": build.get("className", "Unknown"),
        "ascendancy": build.get("ascendClassName", "Unknown"),
        "level": build.get("level", "?"),
        "main_skill": skill,
        "damage_type": damage_type,
        "main_skill_kind": "attack" if skill.lower() in ATTACK_SKILLS else "non_attack" if skill.lower() in NON_ATTACK_SKILLS else "unknown",
        "main_hit_types": main_hit_types,
        "main_element": SKILL_ELEMENT.get(main_skill_lower),
        "main_uses_channeling": main_uses_channeling,
        "main_action_rate": stats.get("Speed"),
        "armour_scales_attack_damage": armour_scales_attack_damage,
        "maximum_charges": {kind: stats.get(f"{kind}ChargesMax") for kind in ("Power", "Frenzy", "Endurance")},
        "configured_charges": {kind: stats.get(f"{kind}Charges") for kind in ("Power", "Frenzy", "Endurance")},
        "charge_generation": charge_generators,
        "filled_flasks": filled_flasks,
        "empty_flask_slots": empty_flask_slots,
        "nature_adrenaline": nature_adrenaline,
        "traitor_likely": traitor_likely,
        "flask_effect_investment": flask_effect_investment,
        "curse_dependent": curse_dependent,
        "crit_chance": crit_chance,
        "crit_multiplier": crit_multiplier,
        "area_of_effect_increased": area_increased,
        "stun_dependent": stun_dependent,
        "attack_archetype": attack_archetype,
        "defence_archetypes": defence_archetypes,
        "effective_attack_block": effective_attack_block,
        "effective_spell_block": effective_spell_block,
        "spell_suppression": spell_suppression,
        "armour": armour,
        "evasion": evasion,
        "uses_cast_on_crit": uses_cast_on_crit,
        "uses_mines": uses_mines,
        "automated_mine_detonation": automated_mine_detonation,
        "wardloop_detected": wardloop_detected,
        "minion_damage_primary": minion_damage_primary,
        "life": stats.get("Life"),
        "energy_shield": stats.get("EnergyShield"),
        "mana": stats.get("Mana"),
        "mana_unreserved": stats.get("ManaUnreserved"),
        "ward": stats.get("Ward"),
        "total_dps": stats.get("TotalDPS"),
        "chaos_resistance": stats.get("ChaosResist"),
        "chaos_immune": chaos_immune,
        "elemental_resistances": {name: stats.get(f"{name}Resist") for name in ("Fire", "Cold", "Lightning")},
        "life_leech": stats.get("LifeLeechGainRate") or 0,
        "mana_leech": stats.get("ManaLeechGainRate") or 0,
        "energy_shield_leech": stats.get("EnergyShieldLeechGainRate") or 0,
        "life_regen": stats.get("LifeRegenRecovery") or 0,
        "life_net_regen": stats.get("NetLifeRegen"),
        "total_build_degen": stats.get("TotalBuildDegen"),
        "mana_regen": stats.get("ManaRegenRecovery") or 0,
        "energy_shield_regen": stats.get("EnergyShieldRegenRecovery") or 0,
        "mana_cost_per_second": stats.get("ManaPerSecondCost") or 0,
        "uses_auras": any(g.lower() in {"discipline", "grace", "determination", "haste", "zealotry", "wrath", "anger", "hatred", "purity of elements"} for g in gems),
        "uses_hexes": any(g.lower() in {"frostbite", "flammability", "conductivity", "despair", "elemental weakness", "enfeeble", "temporal chains", "vulnerability", "punishment"} for g in gems),
        "has_minion_skills": has_minion_skills,
        "reflect_protection_detected": bool(re.search(r"cannot take reflected|immune to reflected", item_text)),
        "notes": ["PoB export stats are a saved snapshot. Passive tree effects and conditional protections may need manual review."],
    }
    from build_signals import infer_build_signals
    profile["signals"] = infer_build_signals(profile)
    return profile
