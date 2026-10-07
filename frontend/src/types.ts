export type Rating = 'brick' | 'dangerous' | 'uncomfortable' | 'free' | 'review';
export type Preset = 'safe' | 'balanced' | 'greedy';
export type Decision = 'block' | 'neutral' | 'allow' | 'want';
export type Category = 'Reflect' | 'Recovery / Leech' | 'Cooldown / Triggers' | 'Resistances' | 'Charges' | 'Ailments / Curses' | 'Monsters' | 'Area' | 'Other';

export interface BuildProfile {
  game: string;
  class: string;
  ascendancy: string;
  level: string;
  main_skill: string;
  damage_type: string;
  main_skill_kind: string;
  uses_cast_on_crit?: boolean;
  uses_mines?: boolean;
  automated_mine_detonation?: boolean;
  life: number | null;
  energy_shield: number | null;
  mana: number | null;
  total_dps: number | null;
  chaos_resistance: number | null;
  elemental_resistances: Record<string, number | null>;
  life_leech: number;
  mana_leech: number;
  energy_shield_leech: number;
  life_regen: number;
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
  ailment_avoidance?: string;
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
  rating: Rating;
  reason: string;
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
  chisels: string[];
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
  minimums: {},
  corrupted: false,
  unidentified: false,
  rarities: [],
  chisels: [],
  eightMod: false,
  excludeValdo: false,
  excludeShaper: false,
  excludeElder: false,
};
