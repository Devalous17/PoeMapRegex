import type { BuildProfile } from "../types";

// Generated from the saved Winter Orb fixture through the shared analyzer.
export const mockBuild: BuildProfile = {
  "game": "Path of Exile 1",
  "class": "Witch",
  "ascendancy": "Occultist",
  "level": "100",
  "main_skill": "Winter Orb",
  "uses_totems": false,
  "ancestral_bond": false,
  "totem_source": null,
  "active_totem_limit": null,
  "maximum_hit_taken": {
    "Physical": 19115.0,
    "Fire": 73260.0,
    "Cold": 60178.0,
    "Lightning": 73260.0,
    "Chaos": null
  },
  "damage_type": "elemental",
  "main_skill_kind": "non_attack",
  "main_hit_types": [
    "elemental"
  ],
  "main_element": "Cold",
  "main_uses_channeling": true,
  "main_action_rate": 10.68,
  "armour_scales_attack_damage": false,
  "maximum_charges": {
    "Power": 15.0,
    "Frenzy": 15.0,
    "Endurance": 3.0
  },
  "configured_charges": {
    "Power": 15.0,
    "Frenzy": 15.0,
    "Endurance": 0.0
  },
  "charge_generation": {
    "Power": true,
    "Frenzy": true,
    "Endurance": false
  },
  "filled_flasks": 5,
  "empty_flask_slots": 0,
  "nature_adrenaline": false,
  "traitor_likely": false,
  "flask_effect_investment": 0,
  "global_flask_effect_investment": 0,
  "flask_charge_investment": 0,
  "crit_extra_damage_reduction": null,
  "curse_dependent": false,
  "crit_chance": 100.0,
  "crit_multiplier": 752.0,
  "area_of_effect_increased": 53,
  "stun_dependent": false,
  "attack_archetype": "Non-attack",
  "defence_archetypes": [
    "High block"
  ],
  "effective_attack_block": 58.0,
  "effective_spell_block": 75.0,
  "spell_suppression": 7.0,
  "armour": 3943.0,
  "evasion": 33.0,
  "uses_cast_on_crit": false,
  "uses_mines": false,
  "automated_mine_detonation": false,
  "wardloop_detected": false,
  "minion_damage_primary": false,
  "life": 1.0,
  "energy_shield": 14254.0,
  "mana": 1167.0,
  "mana_unreserved": 119.0,
  "ward": 0.0,
  "total_dps": 44203509.605095,
  "chaos_resistance": -45.0,
  "ailment_avoidance": {
    "Poison": null,
    "Ignite": null,
    "Freeze": null,
    "Shock": null
  },
  "chaos_immune": true,
  "elemental_resistances": {
    "Fire": 80.0,
    "Cold": 75.0,
    "Lightning": 80.0
  },
  "life_leech": 0,
  "mana_leech": 0,
  "energy_shield_leech": 2494.80635,
  "life_regen": 0,
  "life_net_regen": null,
  "total_build_degen": null,
  "mana_regen": 51.1,
  "energy_shield_regen": 100.0,
  "mana_cost_per_second": 117.48,
  "recovery_channels": [
    {
      "pool": "Life",
      "channel": "regeneration",
      "value": 0.0,
      "unit": "/s",
      "condition": "continuous",
      "source": "LifeRegenRecovery"
    },
    {
      "pool": "Life",
      "channel": "leech",
      "value": 0.0,
      "unit": "/s",
      "condition": "requires damage to a leechable target",
      "source": "LifeLeechGainRate"
    },
    {
      "pool": "Life",
      "channel": "recharge",
      "value": null,
      "unit": "/s",
      "condition": "requires recharge uptime",
      "source": "not saved"
    },
    {
      "pool": "Life",
      "channel": "recoup",
      "value": null,
      "unit": "% of damage",
      "condition": "delayed; requires incoming hits",
      "source": "not saved"
    },
    {
      "pool": "Life",
      "channel": "gain_on_hit",
      "value": null,
      "unit": "per hit",
      "condition": "requires a successful hit",
      "source": "not saved"
    },
    {
      "pool": "Life",
      "channel": "gain_on_kill",
      "value": null,
      "unit": "per kill",
      "condition": "requires kills; unavailable on isolated bosses",
      "source": "not saved"
    },
    {
      "pool": "Life",
      "channel": "instant_leech",
      "value": null,
      "unit": "unmeasured",
      "condition": "requires leech; removed by Cannot Leech",
      "source": "not saved"
    },
    {
      "pool": "Life",
      "channel": "flask",
      "value": null,
      "unit": "unmeasured",
      "condition": "requires flask charges and uptime",
      "source": "not saved"
    },
    {
      "pool": "Mana",
      "channel": "regeneration",
      "value": 51.1,
      "unit": "/s",
      "condition": "continuous",
      "source": "ManaRegenRecovery"
    },
    {
      "pool": "Mana",
      "channel": "leech",
      "value": 0.0,
      "unit": "/s",
      "condition": "requires damage to a leechable target",
      "source": "ManaLeechGainRate"
    },
    {
      "pool": "Mana",
      "channel": "recharge",
      "value": null,
      "unit": "/s",
      "condition": "requires recharge uptime",
      "source": "not saved"
    },
    {
      "pool": "Mana",
      "channel": "recoup",
      "value": null,
      "unit": "% of damage",
      "condition": "delayed; requires incoming hits",
      "source": "not saved"
    },
    {
      "pool": "Mana",
      "channel": "gain_on_hit",
      "value": null,
      "unit": "per hit",
      "condition": "requires a successful hit",
      "source": "not saved"
    },
    {
      "pool": "Mana",
      "channel": "gain_on_kill",
      "value": null,
      "unit": "per kill",
      "condition": "requires kills; unavailable on isolated bosses",
      "source": "not saved"
    },
    {
      "pool": "Mana",
      "channel": "instant_leech",
      "value": null,
      "unit": "unmeasured",
      "condition": "requires leech; removed by Cannot Leech",
      "source": "not saved"
    },
    {
      "pool": "Mana",
      "channel": "flask",
      "value": null,
      "unit": "unmeasured",
      "condition": "requires flask charges and uptime",
      "source": "not saved"
    },
    {
      "pool": "EnergyShield",
      "channel": "regeneration",
      "value": 100.0,
      "unit": "/s",
      "condition": "continuous",
      "source": "EnergyShieldRegenRecovery"
    },
    {
      "pool": "EnergyShield",
      "channel": "leech",
      "value": 2494.80635,
      "unit": "/s",
      "condition": "requires damage to a leechable target",
      "source": "EnergyShieldLeechGainRate"
    },
    {
      "pool": "EnergyShield",
      "channel": "recharge",
      "value": null,
      "unit": "/s",
      "condition": "requires recharge uptime",
      "source": "not saved"
    },
    {
      "pool": "EnergyShield",
      "channel": "recoup",
      "value": null,
      "unit": "% of damage",
      "condition": "delayed; requires incoming hits",
      "source": "not saved"
    },
    {
      "pool": "EnergyShield",
      "channel": "gain_on_hit",
      "value": null,
      "unit": "per hit",
      "condition": "requires a successful hit",
      "source": "not saved"
    },
    {
      "pool": "EnergyShield",
      "channel": "gain_on_kill",
      "value": null,
      "unit": "per kill",
      "condition": "requires kills; unavailable on isolated bosses",
      "source": "not saved"
    },
    {
      "pool": "EnergyShield",
      "channel": "instant_leech",
      "value": null,
      "unit": "unmeasured",
      "condition": "requires leech; removed by Cannot Leech",
      "source": "not saved"
    },
    {
      "pool": "EnergyShield",
      "channel": "flask",
      "value": null,
      "unit": "unmeasured",
      "condition": "requires flask charges and uptime",
      "source": "not saved"
    }
  ],
  "mana_defence_detected": true,
  "maximum_resistances": {
    "Fire": 80.0,
    "Cold": 75.0,
    "Lightning": 80.0
  },
  "maximum_resistance_sources": {
    "Fire": "inferred from resistance plus positive over-cap",
    "Cold": "inferred from resistance plus positive over-cap",
    "Lightning": "inferred from resistance plus positive over-cap"
  },
  "uses_auras": true,
  "uses_hexes": true,
  "has_minion_skills": false,
  "reflect_protection_detected": false,
  "notes": [
    "PoB export stats are a saved snapshot. Passive tree effects and conditional protections may need manual review."
  ],
  "signals": [
    {
      "id": "block",
      "category": "avoidance",
      "strength": 3,
      "evidence": "58% effective attack block / 75% effective spell block"
    },
    {
      "id": "channelled_hits",
      "category": "offence",
      "strength": 2,
      "evidence": "Winter Orb channels and produces player-owned hits"
    },
    {
      "id": "es_leech",
      "category": "recovery",
      "strength": 3,
      "evidence": "2,495 Energy Shield leech/s (17.5% of ES); 100 ES regeneration/s"
    },
    {
      "id": "mana_regen",
      "category": "resource",
      "strength": 2,
      "evidence": "117.48 Mana/s spent, 51.1 regenerated, 0 leeched; 119 unreserved"
    },
    {
      "id": "es_regen",
      "category": "recovery",
      "strength": 1,
      "evidence": "100 Energy Shield regeneration/s (0.7% of ES)"
    }
  ],
  "accuracy_scaling_sources": [],
  "accuracy_scales_offence": false,
  "main_accuracy": null,
  "dependencies": [
    {
      "id": "delivery",
      "axis": "delivery",
      "label": "Player",
      "status": "detected",
      "evidence": "Selected main skill: Winter Orb; player delivery. A utility minion/totem does not determine this."
    },
    {
      "id": "conditional_ailment_0",
      "axis": "scaling",
      "label": "Equipped conditional damage",
      "status": "detected",
      "evidence": "{fractured}49% increased damage with hits against chilled enemies Its share of total damage is not recalculated."
    },
    {
      "id": "Mana_regeneration",
      "axis": "sustain",
      "label": "Mana regeneration",
      "status": "detected",
      "evidence": "51.1 /s; continuous"
    },
    {
      "id": "EnergyShield_regeneration",
      "axis": "sustain",
      "label": "EnergyShield regeneration",
      "status": "detected",
      "evidence": "100 /s; continuous"
    },
    {
      "id": "EnergyShield_leech",
      "axis": "sustain",
      "label": "EnergyShield leech",
      "status": "detected",
      "evidence": "2494.81 /s; requires damage to a leechable target"
    },
    {
      "id": "block",
      "axis": "defence",
      "label": "Block",
      "status": "detected",
      "evidence": "58% effective attack block / 75% effective spell block"
    }
  ],
  "coverage": {
    "issues": [
      "Supporting aura contribution is unmeasured; confirm whether it is essential.",
      "Hex contribution is unmeasured; confirm whether it is essential."
    ],
    "metadata_revision": "16de4b82d57f1c0de6eb40f37143c32d4da36a02",
    "main_skill_recognized": true,
    "normal_modifiers": {
      "total": 78,
      "counter": 11,
      "unaffected": 11,
      "uncertain": 2,
      "policy": 54
    },
    "nightmare_modifiers": {
      "brick": 2,
      "dangerous": 8,
      "uncomfortable": 2,
      "free": 35,
      "review": 0
    }
  },
  "assumptions": {},
  "recovery_conflicts": [],
  "assessment_summary": {
    "total": 125,
    "by_basis": {
      "snapshot_model": 5,
      "dependency_rule": 16,
      "user_confirmation": 0,
      "conservative_policy": 13,
      "policy_allowance": 89,
      "unknown": 2
    }
  }
};
