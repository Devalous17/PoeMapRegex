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
}


def build_profile(root: ET.Element) -> dict:
    build = root.find("Build")
    if build is None:
        raise BuildInputError("The export has no Build section.")
    stats = {stat.get("stat", ""): _number(stat.get("value")) for stat in build.findall("PlayerStat")}
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
    return {
        "game": "Path of Exile 1",
        "class": build.get("className", "Unknown"),
        "ascendancy": build.get("ascendClassName", "Unknown"),
        "level": build.get("level", "?"),
        "main_skill": skill,
        "damage_type": SKILL_DAMAGE.get(skill.lower(), "unknown"),
        "main_skill_kind": "attack" if skill.lower() in {"lightning arrow", "ice shot", "frost blades", "cyclone", "boneshatter", "earthquake", "toxic rain"} else "non_attack" if skill.lower() in {"winter orb", "arc", "fireball", "righteous fire", "essence drain"} else "unknown",
        "uses_cast_on_crit": uses_cast_on_crit,
        "uses_mines": uses_mines,
        "automated_mine_detonation": automated_mine_detonation,
        "life": stats.get("Life"),
        "energy_shield": stats.get("EnergyShield"),
        "mana": stats.get("Mana"),
        "total_dps": stats.get("TotalDPS"),
        "chaos_resistance": stats.get("ChaosResist"),
        "elemental_resistances": {name: stats.get(f"{name}Resist") for name in ("Fire", "Cold", "Lightning")},
        "life_leech": stats.get("LifeLeechGainRate") or 0,
        "mana_leech": stats.get("ManaLeechGainRate") or 0,
        "energy_shield_leech": stats.get("EnergyShieldLeechGainRate") or 0,
        "life_regen": stats.get("LifeRegenRecovery") or 0,
        "mana_regen": stats.get("ManaRegenRecovery") or 0,
        "energy_shield_regen": stats.get("EnergyShieldRegenRecovery") or 0,
        "mana_cost_per_second": stats.get("ManaPerSecondCost") or 0,
        "uses_auras": any(g.lower() in {"discipline", "grace", "determination", "haste", "zealotry", "wrath", "anger", "hatred", "purity of elements"} for g in gems),
        "uses_hexes": any(g.lower() in {"frostbite", "flammability", "conductivity", "despair", "elemental weakness", "enfeeble", "temporal chains", "vulnerability", "punishment"} for g in gems),
        "has_minion_skills": any(g.lower().startswith(("animate guardian", "raise zombie", "raise spectre", "summon ", "carrion golem", "stone golem", "flame golem", "chaos golem", "ice golem", "lightning golem")) for g in gems),
        "reflect_protection_detected": bool(re.search(r"cannot take reflected|immune to reflected", item_text)),
        "notes": ["PoB export stats are a saved snapshot. Passive tree effects and conditional protections may need manual review."],
    }
