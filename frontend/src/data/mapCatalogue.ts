import rawCatalogue from './mapPool.json';
import modifierRules from '../../../backend/modifier_rules.json';
import normalFreePolicy from '../../../backend/normal_free_policy.json';
import poedbNightmareAffixes from './poedbNightmareAffixes.json';
import poedbNormalAffixes from './poedbNormalAffixes.json';
import type { Category, ClassifiedMod, Rating } from '../types';

type RawMapMod = { id: string; text: string; pattern: string; nightmare: boolean; suppliedAvoid: boolean; poedbGroup?: string; poedbName?: string };
type PoedbAffix = { group: string; name: string; kind: 'prefix' | 'suffix'; weight: number; text: string; effects: string[]; rewards: string[] };
const nightmareAffixes = new Map((poedbNightmareAffixes as PoedbAffix[]).map(row => [`${row.group}|${row.name}`, row]));
const normalAffixes = new Map((poedbNormalAffixes as PoedbAffix[]).map(row => [`${row.group}|${row.name}`, row]));

// The local PoB analyzer rates these specific groups. Other entries stay at Review
// until a build rule or a manual choice supplies an answer.
const analyzedGroups: Record<string, string> = modifierRules;

// Player-reviewed normal affixes marked Free by default. This is a selection
// policy, not a simulation of every possible interaction; manual block remains
// available.
const normalFree = new Set(normalFreePolicy);

function categoryFor(text: string): Category {
  const line = text.toLowerCase();
  if (line.includes('cooldown')) return 'Cooldown / Triggers';
  if (/block|armour|evasion|defence|suppres/.test(line)) return 'Defences';
  if (line.includes('thorns')) return 'Thorns';
  if (/leech|recover|regenerat|flask/.test(line)) return 'Recovery / Leech';
  if (/resistan|exposure/.test(line)) return 'Resistances';
  if (/charge/.test(line)) return 'Charges';
  if (/curse|ailment|poison|ignite|freeze|shock|bleed|hexproof/.test(line)) return 'Ailments / Curses';
  if (/ground|patches|area contains|area is inhabited/.test(line)) return 'Area';
  if (/monster|boss/.test(line)) return 'Monsters';
  return 'Other';
}

function displayName(text: string): string {
  return text.replaceAll(/\[([^|\]]+)\|([^\]]+)\]/g, '$2')
    .split('|')[0].replaceAll(/\((\d+)-(\d+)\)/g, (_, left: string, right: string) =>
      `${Math.min(Number(left), Number(right))}–${Math.max(Number(left), Number(right))}`);
}

export const mapCatalogue: ClassifiedMod[] = (rawCatalogue as RawMapMod[]).map(row => {
  const affix = (row.nightmare ? nightmareAffixes : normalAffixes).get(`${row.poedbGroup}|${row.poedbName}`);
  const playerFree = !row.nightmare && normalFree.has(row.id);
  const reviewReason = playerFree
    ? 'Marked Free by your normal-map policy. This is not a simulation of every interaction; you can still block it manually.'
    : 'The saved PoB does not establish whether this modifier is safe. Review it and choose whether to avoid or want it.';
  return {
  id: `map-${row.id}`,
  name: displayName(row.text),
  pattern: row.pattern,
  category: categoryFor(row.text),
  tags: [row.nightmare ? 'Nightmare' : 'Normal', ...(affix ? [affix.name, affix.kind] : [])],
  defaultRating: (playerFree ? 'free' : 'review') as Rating,
  whyBad: reviewReason,
  rating: (playerFree ? 'free' : 'review') as Rating,
  reason: reviewReason,
  mapPool: row.nightmare ? 'nightmare' as const : 'normal' as const,
  matchText: affix?.text ?? row.text,
  effectText: row.text,
  suppliedAvoid: playerFree ? false : row.suppliedAvoid,
  affixName: affix?.name,
  affixKind: affix?.kind,
  spawnWeight: affix?.weight,
  rewardText: affix?.rewards.join(' · '),
}; });

export function classifyCatalogue(analyzed: { id: string; rating: Rating; reason: string; confidence?: 'low' | 'medium' | 'high'; combination_avoid?: boolean; combination_reason?: string; combination_partners?: string[][]; assessment_status?: ClassifiedMod['assessment_status']; dependency_axes?: string[]; dependency_evidence?: string[] }[]): ClassifiedMod[] {
  const byGroup = new Map(analyzed.map(row => [row.id, row]));
  return mapCatalogue.map(mod => {
    const group = analyzedGroups[mod.id.slice(4)];
    const rule = byGroup.get(mod.id) ?? (group ? byGroup.get(group) : undefined);
    return rule ? { ...mod, rating: rule.rating, reason: rule.reason, confidence: rule.confidence, assessment_status: rule.assessment_status, dependency_axes: rule.dependency_axes, dependency_evidence: rule.dependency_evidence,
      combination_avoid: rule.combination_avoid, combination_reason: rule.combination_reason,
      combination_partners: rule.combination_partners?.map(partners => mapCatalogue.filter(candidate => candidate.mapPool === mod.mapPool && partners.includes(analyzedGroups[candidate.id.slice(4)])).map(candidate => candidate.id)) } : mod;
  });
}
