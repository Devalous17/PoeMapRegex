import rawCatalogue from './mapPool.json';
import poedbNightmareAffixes from './poedbNightmareAffixes.json';
import poedbNormalAffixes from './poedbNormalAffixes.json';
import type { Category, ClassifiedMod, Rating } from '../types';

type RawMapMod = { id: string; text: string; pattern: string; nightmare: boolean; suppliedAvoid: boolean; poedbGroup?: string; poedbName?: string };
type PoedbAffix = { group: string; name: string; kind: 'prefix' | 'suffix'; weight: number; text: string; effects: string[]; rewards: string[] };
const nightmareAffixes = new Map((poedbNightmareAffixes as PoedbAffix[]).map(row => [`${row.group}|${row.name}`, row]));
const normalAffixes = new Map((poedbNormalAffixes as PoedbAffix[]).map(row => [`${row.group}|${row.name}`, row]));

// The local PoB analyzer rates these specific groups. Other entries stay at Review
// until a build rule or a manual choice supplies an answer.
const analyzedGroups: Record<string, string> = {
  '1078205993': 'elemental_reflect', '-235013251': 'physical_reflect',
  '252096506': 'no_leech', '1305115176': 'no_regen', '-2050206104': 'reduced_recovery',
  '-477049138': 'minus_max_res', '-2038489408': 'minus_max_res',
  '10729340': 'extra_chaos', '127168403': 'extra_chaos',
  '1551446200': 'hexproof', '1101434369': 'reduced_auras',
  '-1772662453': 'avoid_ailments', '1634487773': 'extra_projectiles', '1469490158': 'extra_projectiles',
  '-1344829253': 'monster_crit', '246480838': 'monster_crit',
  '-172005981': 'monster_life', '-114660370': 'less_accuracy',
  '-1473394034': 'reduced_cooldown',
};

function categoryFor(text: string): Category {
  const line = text.toLowerCase();
  if (line.includes('cooldown')) return 'Cooldown / Triggers';
  if (line.includes('reflect')) return 'Reflect';
  if (/leech|recover|regenerat|flask/.test(line)) return 'Recovery / Leech';
  if (/resistan|exposure|suppres/.test(line)) return 'Resistances';
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
  return {
  id: `map-${row.id}`,
  name: displayName(row.text),
  pattern: row.pattern,
  category: categoryFor(row.text),
  tags: [row.nightmare ? 'Nightmare' : 'Normal', ...(affix ? [affix.name, affix.kind] : [])],
  defaultRating: 'review' as Rating,
  whyBad: 'The saved PoB does not establish whether this modifier is safe. Review it and choose whether to avoid or want it.',
  rating: 'review' as Rating,
  reason: 'The saved PoB does not establish whether this modifier is safe. Review it and choose whether to avoid or want it.',
  mapPool: row.nightmare ? 'nightmare' as const : 'normal' as const,
  matchText: affix?.text ?? row.text,
  effectText: row.text,
  suppliedAvoid: row.suppliedAvoid,
  affixName: affix?.name,
  affixKind: affix?.kind,
  spawnWeight: affix?.weight,
  rewardText: affix?.rewards.join(' · '),
}; });

export function classifyCatalogue(analyzed: { id: string; rating: Rating; reason: string }[]): ClassifiedMod[] {
  const byGroup = new Map(analyzed.map(row => [row.id, row]));
  return mapCatalogue.map(mod => {
    const group = analyzedGroups[mod.id.slice(4)];
    const rule = group ? byGroup.get(group) : undefined;
    return rule ? { ...mod, rating: rule.rating, reason: rule.reason } : mod;
  });
}
