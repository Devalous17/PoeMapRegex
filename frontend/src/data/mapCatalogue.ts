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
  '1078205993': 'elemental_thorns', '-235013251': 'physical_thorns', '-1430865583': 'combined_thorns',
  '252096506': 'no_leech', '1305115176': 'no_regen', '-2050206104': 'reduced_recovery',
  '-477049138': 'minus_max_res', '-2038489408': 'minus_max_res',
  '10729340': 'extra_chaos', '127168403': 'extra_chaos',
  '1551446200': 'hexproof', '1101434369': 'reduced_auras',
  '-1772662453': 'avoid_ailments', '1634487773': 'extra_projectiles', '1469490158': 'extra_projectiles',
  '-1344829253': 'monster_crit', '246480838': 'monster_crit',
  '-172005981': 'monster_life', '-114660370': 'less_accuracy',
  '-1473394034': 'reduced_cooldown',
  '-999805715': 'reduced_block_and_armour',
  '151806012': 'reduced_suppression_and_evasion',
  '1205583947': 'reduced_leech',
  '-1358177810': 'charge_theft', '-763914456': 'reduced_flask_charges',
  '-539026720': 'reduced_monster_curse_effect', '-54649013': 'monster_crit_reduction',
  '829751875': 'less_player_aoe', '1541760497': 'unstunnable_monsters',
};

// Player-reviewed normal affixes marked Free by default. This is a selection
// policy, not a simulation of every possible interaction; manual block remains
// available.
const normalFree = new Set([
  '-1934587276', '-1616686189', '-1204380788', '-1139261923', '-1099682289',
  '-1094717370', '-1088873049', '-1047451686', '-946283701', '-737013402',
  '-694214737', '-688435205', '-683043845', '-627831782', '-617888797',
  '-580302769', '-481946502', '-268547495', '-225071089', '-210607554',
  '-166549521', '-128171261', '-106750911', '-106071007', '-80588106',
  '-26777606', '17483843', '58884108', '156744008', '194321329',
  '339937661', '472035128', '583869527', '775962019', '823410479',
  '955801458', '980061401', '1062763755', '1082020744', '1202132179',
  '1211148661', '1283094925', '1424047266', '1428847539', '1578069823',
  '1598599541', '1723792253', '1743546402', '1799781772', '1882321261',
  '1899039946', '2080363489', '2105788016', '2122294281', '2132856290',
]);

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

export function classifyCatalogue(analyzed: { id: string; rating: Rating; reason: string }[]): ClassifiedMod[] {
  const byGroup = new Map(analyzed.map(row => [row.id, row]));
  return mapCatalogue.map(mod => {
    const group = analyzedGroups[mod.id.slice(4)];
    const rule = group ? byGroup.get(group) : undefined;
    return rule ? { ...mod, rating: rule.rating, reason: rule.reason } : mod;
  });
}
