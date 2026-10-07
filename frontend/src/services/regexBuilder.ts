import type { ClassifiedMod, Decision, Preferences, Preset, Rating, RegexResult } from '../types';
import suppliedPatterns from '../data/mapPoolPatterns.json' with { type: 'json' };
import { mapPreferenceTerms } from './mapPreferencesRegex.ts';

const blockedByPreset: Record<Preset, Rating[]> = {
  safe: ['brick', 'dangerous', 'uncomfortable'],
  balanced: ['brick', 'dangerous'],
  greedy: ['brick'],
};

export function recommendedDecision(mod: ClassifiedMod, preset: Preset): Decision {
  if (blockedByPreset[preset].includes(mod.rating)) return 'block';
  return mod.rating === 'free' ? 'allow' : 'neutral';
}

function sampleText(text: string, upper = false): string {
  return text.replaceAll(/\[([^|\]]+)\|([^\]]+)\]/g, '$2')
    .replaceAll(/\((\d+)[—-](\d+)\)/g, (_, low: string, high: string) => upper ? high : low)
    .replaceAll('|', '\n');
}

function matches(pattern: string, text: string): boolean {
  try { return new RegExp(pattern, 'im').test(text); } catch { return false; }
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

type Candidate = { pattern: string; ids: Set<string> };

function optimizedPatterns(all: ClassifiedMod[], blocked: ClassifiedMod[]): { patterns: string[]; uncovered: string[] } {
  const selected = new Set(blocked.map(mod => mod.id));
  const samples = new Map(all.map(mod => [mod.id, [sampleText(mod.matchText ?? mod.name), sampleText(mod.matchText ?? mod.name, true)]] as const));
  const candidates: Candidate[] = [];
  const seen = new Set<string>();
  function add(pattern: string) {
    if (!pattern || seen.has(pattern)) return;
    seen.add(pattern);
    if (all.some(mod => !selected.has(mod.id) && (samples.get(mod.id) ?? []).some(sample => matches(pattern, sample)))) return;
    const ids = new Set(all.filter(mod => selected.has(mod.id) && (samples.get(mod.id) ?? []).every(sample => matches(pattern, sample))).map(mod => mod.id));
    if (ids.size) candidates.push({ pattern, ids });
  }
  blocked.forEach(mod => add(mod.pattern));
  // Keep the catalogue's short fragments in their displayed order when they
  // safely cover the selection. This makes a few clicks reproduce the exact
  // in-game regex the player expects; only large selections need compression.
  const directUncovered = new Set(selected);
  const directPatterns: string[] = [];
  for (const mod of blocked) {
    const candidate = candidates.find(item => item.pattern === mod.pattern);
    if (!candidate || ![...candidate.ids].some(id => directUncovered.has(id))) continue;
    directPatterns.push(candidate.pattern);
    candidate.ids.forEach(id => directUncovered.delete(id));
  }
  if (!directUncovered.size && makeQuery(directPatterns).length <= 250) {
    return { patterns: directPatterns, uncovered: [] };
  }
  const pool = all[0]?.mapPool;
  if (pool) suppliedPatterns[pool].forEach(add);
  for (const mod of blocked) {
    if (candidates.some(candidate => candidate.ids.has(mod.id))) continue;
    const lines = (samples.get(mod.id)?.[0] ?? '').toLowerCase().split('\n');
    for (let length = 8; length <= 36 && !candidates.some(candidate => candidate.ids.has(mod.id)); length++) {
      for (const line of lines) {
        for (let start = 0; start + length <= line.length; start++) {
          const fragment = line.slice(start, start + length);
          if (!/^[a-z '\-]+$/.test(fragment) || fragment.trim().length < 8) continue;
          add(escapeRegex(fragment));
          if (candidates.some(candidate => candidate.ids.has(mod.id))) break;
        }
        if (candidates.some(candidate => candidate.ids.has(mod.id))) break;
      }
    }
  }
  const uncovered = new Set(selected);
  const patterns: string[] = [];
  while (uncovered.size) {
    const ranked = candidates.map(candidate => ({
      ...candidate,
      gain: [...candidate.ids].filter(id => uncovered.has(id)).length,
    })).filter(candidate => candidate.gain);
    ranked.sort((a, b) => b.gain / (b.pattern.length + 1) - a.gain / (a.pattern.length + 1) ||
      a.pattern.length - b.pattern.length || a.pattern.localeCompare(b.pattern));
    const best = ranked[0];
    if (!best) break;
    patterns.push(best.pattern);
    best.ids.forEach(id => uncovered.delete(id));
  }
  return { patterns, uncovered: blocked.filter(mod => uncovered.has(mod.id)).map(mod => mod.name) };
}

function makeQuery(patterns: string[]): string {
  return patterns.length ? `"!${patterns.join('|')}"` : '';
}

function makeInclude(patterns: string[]): string {
  return patterns.length ? `"${patterns.join('|')}"` : '';
}

function splitQueries(patterns: string[], limit: number): string[] {
  const chunks: string[][] = [];
  let current: string[] = [];
  for (const pattern of patterns) {
    if (current.length && makeQuery([...current, pattern]).length > limit) {
      chunks.push(current);
      current = [];
    }
    current.push(pattern);
  }
  if (current.length) chunks.push(current);
  return chunks.map(makeQuery);
}

export function buildRegex(
  mods: ClassifiedMod[], preset: Preset, overrides: Record<string, Decision>,
  preferences: Preferences, limit = 250,
): RegexResult {
  const blocked = mods.filter(mod => (overrides[mod.id] ?? recommendedDecision(mod, preset)) === 'block');
  const wanted = mods.filter(mod => (overrides[mod.id] ?? recommendedDecision(mod, preset)) === 'want');
  const catalogMode = mods.length > 0 && mods.every(mod => mod.matchText);
  const result = catalogMode ? optimizedPatterns(mods, blocked) :
    { patterns: [...new Set(blocked.map(mod => mod.pattern))], uncovered: [] as string[] };
  const wantedResult = catalogMode ? optimizedPatterns(mods, wanted) :
    { patterns: [...new Set(wanted.map(mod => mod.pattern))], uncovered: [] as string[] };
  const exclude = makeQuery(result.patterns);
  const include = makeInclude(wantedResult.patterns);
  const preferenceTerms = mapPreferenceTerms(preferences);
  const regex = [exclude, include, ...preferenceTerms.parts.map(part => part.text)].filter(Boolean).join(' ');
  const warnings: string[] = [...preferenceTerms.warnings];
  if (result.uncovered.length) warnings.push(`Could not safely match ${result.uncovered.length} blocked modifier(s): ${result.uncovered.slice(0, 3).join(', ')}.`);
  if (wantedResult.uncovered.length) warnings.push(`Could not safely match ${wantedResult.uncovered.length} wanted modifier(s): ${wantedResult.uncovered.slice(0, 3).join(', ')}.`);
  if (blocked.length && wanted.length) warnings.push('The Want search looks for at least one wanted modifier while excluding every blocked modifier.');
  if (regex.length > limit) warnings.push(`This selection needs ${regex.length} characters; the game limit is ${limit}. Select fewer blocked mods to get one complete search.`);
  return {
    regex, length: regex.length, blocked, wanted, warnings,
    valid: result.uncovered.length === 0 && wantedResult.uncovered.length === 0 && preferenceTerms.valid,
    parts: [...(exclude ? [{ kind: 'exclude' as const, text: exclude }] : []), ...(include ? [{ kind: 'include' as const, text: include }] : []), ...preferenceTerms.parts],
    split: regex.length > limit ? [...splitQueries(result.patterns, limit).map(query => [query, ...preferenceTerms.parts.map(part => part.text)].join(' ')), ...wantedResult.patterns.map(pattern => [makeInclude([pattern]), ...preferenceTerms.parts.map(part => part.text)].join(' '))].filter(query => query.length <= limit) : [],
  };
}
