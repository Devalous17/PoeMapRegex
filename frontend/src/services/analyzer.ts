import { mockBuild } from '../data/mockBuild';
import { modDefinitions } from '../data/mods';
import { classifyCatalogue } from '../data/mapCatalogue';
import type { AnalysisResult, BuildProfile, ClassifiedMod, ModDefinition, Rating } from '../types';

interface RawMod {
  id: string;
  name: string;
  pattern: string;
  rating: Rating;
  reason: string;
}

interface RawAnalysis {
  profile: BuildProfile;
  mods: RawMod[];
  regex_limit: number;
}

export async function analyzeBuild(source: string): Promise<AnalysisResult> {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source }),
  });
  let data: RawAnalysis | { error?: string };
  try {
    data = await response.json() as RawAnalysis | { error?: string };
  } catch {
    throw new Error('The local analyzer did not return a readable response.');
  }
  if (!response.ok) {
    throw new Error('error' in data && data.error ? data.error : 'Could not analyze this build.');
  }
  const result = data as RawAnalysis;
  if (!result.profile || !Array.isArray(result.mods)) throw new Error('The build result was incomplete.');
  return {
    profile: result.profile,
    mods: classifyCatalogue(result.mods),
    regexLimit: result.regex_limit || 250,
    mode: 'live',
  };
}

export function classifyMods(profile: BuildProfile, mods: ModDefinition[]): ClassifiedMod[] {
  return mods.map(mod => {
    let rating = mod.defaultRating;
    let reason = mod.whyBad;
    if (mod.id === 'elemental_thorns' && !profile.main_hit_types?.includes('elemental')) rating = 'free';
    if (mod.id === 'physical_thorns' && !profile.main_hit_types?.includes('physical')) rating = 'free';
    if (mod.id === 'no_leech' && profile.life_leech + profile.mana_leech + profile.energy_shield_leech === 0) rating = 'free';
    if (mod.id === 'extra_chaos' && (profile.chaos_immune || (profile.chaos_resistance ?? -60) >= 75)) rating = 'free';
    if (mod.id === 'charge_theft') rating = Object.entries(profile.maximum_charges ?? {}).some(([kind, max]) =>
      (max ?? 0) >= 5 && (profile.charge_generation?.[kind] || (profile.configured_charges?.[kind] ?? 0) >= 5)) ? 'uncomfortable' : 'free';
    if (mod.id === 'reduced_flask_charges') rating = profile.traitor_likely ||
      (profile.ascendancy === 'Pathfinder' && (profile.nature_adrenaline || (profile.flask_effect_investment ?? 0) >= 100) && (profile.filled_flasks ?? 0) >= 2) ? 'brick' : 'free';
    if (mod.id === 'reduced_monster_curse_effect') rating = profile.curse_dependent ? 'brick' : 'free';
    if (mod.id === 'monster_crit_reduction') rating = (profile.crit_chance ?? 0) >= 50 && (profile.crit_multiplier ?? 0) >= 300 ? 'brick' : 'free';
    if (mod.id === 'less_player_aoe') rating = (profile.area_of_effect_increased ?? 0) >= 75 ? 'uncomfortable' : 'free';
    if (mod.id === 'unstunnable_monsters') rating = profile.stun_dependent ? 'brick' : 'free';
    return { ...mod, rating, reason };
  });
}

export async function exampleAnalysis(): Promise<AnalysisResult> {
  await new Promise(resolve => window.setTimeout(resolve, 900));
  return { profile: mockBuild, mods: classifyCatalogue(classifyMods(mockBuild, modDefinitions)), regexLimit: 250, mode: 'example' };
}
