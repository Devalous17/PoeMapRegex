import { mockBuild } from '../data/mockBuild';
import exampleMods from '../data/exampleMods.json' with { type: 'json' };
import { classifyCatalogue } from '../data/mapCatalogue';
import type { AnalysisResult, BuildAssumptions, BuildProfile, ClassifiedMod, Rating } from '../types';

interface RawMod {
  strict_avoid?: boolean;
  assessment_basis?: ClassifiedMod['assessment_basis'];
  measurement?: ClassifiedMod['measurement'];
  id: string;
  name: string;
  pattern: string;
  rating: Rating;
  reason: string;
  assessment_status?: ClassifiedMod['assessment_status'];
  dependency_axes?: string[];
  dependency_evidence?: string[];
  confidence?: 'low' | 'medium' | 'high';
  combination_avoid?: boolean;
  combination_reason?: string;
  combination_partners?: string[][];
}

interface RawAnalysis {
  profile: BuildProfile;
  mods: RawMod[];
  regex_limit: number;
}

export async function analyzeBuild(source: string, assumptions: BuildAssumptions = {}): Promise<AnalysisResult> {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, assumptions }),
  });
  let data: RawAnalysis | { error?: string };
  try {
    data = await response.json() as RawAnalysis | { error?: string };
  } catch {
    throw new Error('The analyzer did not return a readable response.');
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

export async function exampleAnalysis(): Promise<AnalysisResult> {
  await new Promise(resolve => window.setTimeout(resolve, 900));
  return { profile: mockBuild, mods: classifyCatalogue(exampleMods as RawMod[]), regexLimit: 250, mode: 'example' };
}
