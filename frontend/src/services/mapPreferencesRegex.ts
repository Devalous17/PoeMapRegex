import type { Preferences, RegexPart } from '../types';

// These fragments match the English map text used by PoE's stash search.
// Keep each numeric condition in its own quoted term so conditions are ANDed.
const valueFields: Record<string, string> = {
  quantity: 'm q.*',
  pack: 'iz.*',
  maps: 're maps.*',
  rarity: 'm rar.*',
  currency: 'cy:.*',
  scarabs: 'sca.*',
  divination: 'div.*',
};

function digits(from: number, to: number): string {
  if (from === to) return String(from);
  if (from === 0 && to === 9) return '.';
  return `[${from}-${to}]`;
}

function fixedRange(lo: number, hi: number, width: number): string {
  if (width === 0) return '';
  const place = 10 ** (width - 1);
  const first = Math.floor(lo / place);
  const last = Math.floor(hi / place);
  const pieces: string[] = [];
  let groupStart = first;
  let previousSuffix = '';
  const flush = (end: number) => pieces.push(`${digits(groupStart, end)}${previousSuffix}`);
  for (let digit = first; digit <= last; digit++) {
    const lowTail = digit === first ? lo % place : 0;
    const highTail = digit === last ? hi % place : place - 1;
    const suffix = lowTail === 0 && highTail === place - 1 ? '.'.repeat(width - 1) : fixedRange(lowTail, highTail, width - 1);
    if (digit !== first && suffix !== previousSuffix) { flush(digit - 1); groupStart = digit; }
    previousSuffix = suffix;
  }
  flush(last);
  return pieces.length === 1 ? pieces[0] : `(${pieces.join('|')})`;
}

export function numberRangeRegex(min: number, max: number): string {
  const parts: string[] = [];
  for (let width = 1; width <= 3; width++) {
    const lower = width === 1 ? 0 : 10 ** (width - 1);
    const upper = 10 ** width - 1;
    const lo = Math.max(min, lower);
    const hi = Math.min(max, upper);
    if (lo <= hi) parts.push(fixedRange(lo, hi, width));
  }
  return parts.length === 1 ? parts[0] : `(${parts.join('|')})`;
}

function parsedValue(raw: string | undefined): number | null {
  if (raw === undefined || raw === '') return null;
  if (!/^\d+$/.test(raw)) return NaN;
  return Number(raw);
}

export function mapPreferenceTerms(preferences: Preferences): { parts: RegexPart[]; warnings: string[]; valid: boolean } {
  const parts: RegexPart[] = [];
  const warnings: string[] = [];
  let valid = true;
  for (const [key, prefix] of Object.entries(valueFields)) {
    const min = parsedValue(preferences.minimums[key]);
    const max = parsedValue(preferences.minimums[`max_${key}`]);
    if (min === null && max === null) continue;
    if ((min !== null && (!Number.isInteger(min) || min < 0 || min > 999)) ||
        (max !== null && (!Number.isInteger(max) || max < 0 || max > 999)) ||
        (min !== null && max !== null && min > max)) {
      warnings.push(`Check the ${key} range: use whole numbers from 0 to 999 with MIN ≤ MAX.`);
      valid = false;
      continue;
    }
    parts.push({ kind: 'preference', text: `"${prefix}${numberRangeRegex(min ?? 0, max ?? 999)}%"` });
  }
  if (preferences.corrupted) parts.push({ kind: 'preference', text: 'corrupted' });
  if (preferences.unidentified) parts.push({ kind: 'preference', text: 'unidentified' });
  const rarityCodes = preferences.rarities.map(value => ({ Normal: 'n', Magic: 'm', Rare: 'r' }[value])).filter(Boolean);
  if (rarityCodes.length && rarityCodes.length < 3) {
    parts.push({ kind: 'preference', text: `"y: ${rarityCodes.length === 1 ? rarityCodes[0] : `(${rarityCodes.join('|')})`}"` });
  }
  const tradeOnly = [
    preferences.eightMod && '8-mod maps',
    preferences.excludeValdo && 'Valdo maps',
    preferences.excludeShaper && 'Shaper influence',
    preferences.excludeElder && 'Elder influence',
  ].filter(Boolean);
  if (tradeOnly.length) warnings.push(`Trade filters only: ${tradeOnly.join(', ')} cannot be checked reliably by the in-game map regex.`);
  return { parts, warnings, valid };
}
