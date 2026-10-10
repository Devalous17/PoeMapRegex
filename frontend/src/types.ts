export type Rating = 'brick' | 'dangerous' | 'uncomfortable' | 'free' | 'review';
export type Preset = 'safe' | 'balanced' | 'greedy';
export type Decision = 'block' | 'neutral' | 'allow' | 'want';
export interface BuildAssumptions {
  mana_alternative_per_second?: number;
  map_effect_increased?: number;
  recharge_sustainable?: boolean;
  hexproof_bypass?: boolean;
  flask_essential?: boolean;
  curse_role?: 'unknown' | 'utility' | 'damage' | 'mechanic';
  aura_role?: 'unknown' | 'utility' | 'damage' | 'defence' | 'mechanic';
  charge_sustain?: 'unknown' | 'reliable' | 'required';
}
export type Category = 'Thorns' | 'Recovery / Leech' | 'Cooldown / Triggers' | 'Defences' | 'Resistances' | 'Charges' | 'Ailments / Curses' | 'Monsters' | 'Area' | 'Other';

export type AssessmentBasis = 'snapshot_model' | 'dependency_rule' | 'user_confirmation' | 'conservative_policy' | 'policy_allowance' | 'unknown';
export interface BuildProfile {
  assessment_summary?: { total: number; by_basis: Partial<Record<AssessmentBasis, number>> };
  dependencies?: { id: string; axis: string; label: string; status: 'detected' | 'uncertain'; evidence: string }[];
  coverage?: { issues: string[]; main_skill_recognized: boolean; metadata_revision: string; normal_modifiers?: Record<string, number>; nightmare_modifiers?: Record<string, number> };
  game: string;
  class: string;
  ascendancy: string;
  level: string;
  main_skill: string;
  uses_totems?: boolean;
  ancestral_bond?: boolean;
  active_totem_limit?: number | null;
  totem_source?: string | null;
  mana_defence_detected?: boolean;
  maximum_hit_taken?: Record<string, number | null>;
  assumptions?: BuildAssumptions;
  recovery_channels?: { pool: string; channel: string; value: number | null; unit: string; condition: string; source: string }[];
  recovery_conflicts?: { mods: string[]; avoid: string; reason: string }[];
  maximum_resistances?: Record<string, number | null>;
  maximum_resistance_sources?: Record<string, string>;
  damage_type: string;
  main_skill_kind: string;
  main_hit_types?: string[];
  main_element?: string | null;
  main_uses_channeling?: boolean;
  main_action_rate?: number | null;
  armour_scales_attack_damage?: boolean;
  accuracy_scales_offence?: boolean;
  accuracy_scaling_sources?: string[];
  main_accuracy?: number | null;
  maximum_charges?: Record<string, number | null>;
  configured_charges?: Record<string, number | null>;
  charge_generation?: Record<string, boolean>;
  filled_flasks?: number;
  empty_flask_slots?: number | null;
  nature_adrenaline?: boolean;
  traitor_likely?: boolean;
  flask_effect_investment?: number;
  curse_dependent?: boolean;
  crit_chance?: number | null;
  crit_multiplier?: number | null;
  area_of_effect_increased?: number | null;
  stun_dependent?: boolean;
  attack_archetype?: string;
  defence_archetypes?: string[];
  effective_attack_block?: number | null;
  effective_spell_block?: number | null;
  spell_suppression?: number | null;
  uses_cast_on_crit?: boolean;
  uses_mines?: boolean;
  automated_mine_detonation?: boolean;
  wardloop_detected?: boolean;
  minion_damage_primary?: boolean;
  mana_unreserved?: number | null;
  ward?: number | null;
  signals?: { id: string; category: string; strength: number; evidence: string }[];
  life: number | null;
  energy_shield: number | null;
  mana: number | null;
  total_dps: number | null;
  chaos_resistance: number | null;
  chaos_immune?: boolean;
  elemental_resistances: Record<string, number | null>;
  life_leech: number;
  mana_leech: number;
  energy_shield_leech: number;
  life_regen: number;
  life_net_regen?: number | null;
  total_build_degen?: number | null;
  mana_regen: number;
  energy_shield_regen: number;
  mana_cost_per_second: number;
  uses_auras: boolean;
  uses_hexes: boolean;
  has_minion_skills: boolean;
  reflect_protection_detected: boolean;
  notes: string[];
  armour?: number | null;
  evasion?: number | null;
  block?: number | null;
  ailment_avoidance?: Partial<Record<'Poison' | 'Ignite' | 'Freeze' | 'Shock', number | null>>;
  global_flask_effect_investment?: number;
  flask_charge_investment?: number;
  crit_extra_damage_reduction?: number | null;
  charges?: string;
}

export interface ModDefinition {
  id: string;
  name: string;
  pattern: string;
  category: Category;
  tags: string[];
  defaultRating: Rating;
  whyBad: string;
  mapPool?: 'normal' | 'nightmare';
  matchText?: string;
  effectText?: string;
  suppliedAvoid?: boolean;
  affixName?: string;
  affixKind?: 'prefix' | 'suffix';
  spawnWeight?: number;
  rewardText?: string;
}

export interface ClassifiedMod extends ModDefinition {
  strict_avoid?: boolean;
  assessment_basis?: AssessmentBasis;
  measurement?: { engine: string; status: 'unsupported' | 'partial' | 'estimated'; quantities: { name: string; before: number; after: number; unit: string }[]; limitations: string[] };
  assessment_status?: 'counter' | 'unaffected' | 'uncertain' | 'policy';
  dependency_axes?: string[];
  dependency_evidence?: string[];
  manual?: boolean;
  rating: Rating;
  reason: string;
  confidence?: 'low' | 'medium' | 'high';
  combination_avoid?: boolean;
  combination_reason?: string;
  combination_partners?: string[][];
}

export interface AnalysisResult {
  profile: BuildProfile;
  mods: ClassifiedMod[];
  regexLimit: number;
  mode: 'live' | 'example';
}

export interface Preferences {
  minimums: Record<string, string>;
  corrupted: boolean;
  unidentified: boolean;
  rarities: string[];
  eightMod: boolean;
  excludeValdo: boolean;
  excludeShaper: boolean;
  excludeElder: boolean;
}

export interface RegexPart {
  kind: 'exclude' | 'include' | 'preference';
  text: string;
}

export interface RegexResult {
  regex: string;
  length: number;
  blocked: ClassifiedMod[];
  wanted: ClassifiedMod[];
  warnings: string[];
  parts: RegexPart[];
  split: string[];
  valid: boolean;
}

export const EMPTY_PREFERENCES: Preferences = {
  minimums: { quantity: '40' },
  corrupted: false,
  unidentified: false,
  rarities: [],
  eightMod: false,
  excludeValdo: false,
  excludeShaper: false,
  excludeElder: false,
};
