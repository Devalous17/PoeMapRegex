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
    if (mod.id === 'elemental_reflect' && profile.damage_type !== 'elemental') rating = 'free';
    if (mod.id === 'physical_reflect' && profile.damage_type === 'physical') rating = 'brick';
    if (mod.id === 'physical_reflect' && profile.has_minion_skills) reason = 'The main skill is elemental, but equipped minions may deal reflected Physical damage.';
    if (mod.id === 'no_leech' && profile.life_leech + profile.mana_leech + profile.energy_shield_leech === 0) rating = 'free';
    if (mod.id === 'extra_chaos' && (profile.chaos_resistance ?? 0) >= 75) rating = 'uncomfortable';
    return { ...mod, rating, reason };
  });
}

export async function exampleAnalysis(): Promise<AnalysisResult> {
  await new Promise(resolve => window.setTimeout(resolve, 900));
  return { profile: mockBuild, mods: classifyCatalogue(classifyMods(mockBuild, modDefinitions)), regexLimit: 250, mode: 'example' };
}
