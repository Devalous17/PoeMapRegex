import assert from 'node:assert/strict';
import test from 'node:test';
import rows from '../src/data/mapPool.json' with { type: 'json' };
import nightmareAffixes from '../src/data/poedbNightmareAffixes.json' with { type: 'json' };
import normalAffixes from '../src/data/poedbNormalAffixes.json' with { type: 'json' };
import { buildRegex, rollSamples, recommendedDecision } from '../src/services/regexBuilder.ts';
import { numberRangeRegex } from '../src/services/mapPreferencesRegex.ts';
import { EMPTY_PREFERENCES } from '../src/types.ts';
const noMinimums = { ...EMPTY_PREFERENCES, minimums: {} };

test('marginal penalties are not selected by Maximum Filtering without an explicit dependency', () => {
  const minor = { id: 'minor', rating: 'uncomfortable', name: 'Minor', pattern: 'minor' };
  assert.equal(recommendedDecision(minor, 'safe'), 'neutral');
  assert.equal(recommendedDecision({ ...minor, strict_avoid: true }, 'safe'), 'block');
  assert.equal(recommendedDecision({ ...minor, strict_avoid: true }, 'balanced'), 'neutral');
  assert.equal(recommendedDecision({ ...minor, combination_avoid: true }, 'balanced'), 'block');
  assert.equal(buildRegex([{ ...minor, strict_avoid: true }], 'safe', { minor: 'allow' }, noMinimums).blocked.length, 0);
});

test('manual catalogue never invents preset exclusions or build warnings', () => {
  const mods = catalogue(false).map(mod => ({ ...mod, manual: true }));
  assert.ok(mods.every(mod => recommendedDecision(mod, 'safe') === 'neutral'));
  const initial = buildRegex(mods, 'safe', {}, noMinimums, 250);
  assert.equal(initial.blocked.length, 0);
  assert.equal(initial.warnings.length, 0);
  const selected = buildRegex(mods, 'safe', { [mods[0].id]: 'block' }, noMinimums, 250);
  assert.equal(selected.blocked.length, 1);
  assert.ok(selected.regex.startsWith('"!'));
});

function catalogue(nightmare) {
  const affixByKey = new Map((nightmare ? nightmareAffixes : normalAffixes).map(row => [`${row.group}|${row.name}`, row]));
  return rows.filter(row => row.nightmare === nightmare).map(row => ({
    id: row.id, name: row.text, pattern: row.pattern,
    matchText: affixByKey.get(`${row.poedbGroup}|${row.poedbName}`)?.text ?? row.text,
    suppliedAvoid: row.suppliedAvoid, rating: 'review', mapPool: nightmare ? 'nightmare' : 'normal',
  }));
}

function textSample(raw, upper = false) {
  return raw.replaceAll(/\[([^|\]]+)\|([^\]]+)\]/g, '$2')
    .replaceAll(/\((\d+)[—-](\d+)\)/g, (_, low, high) => upper ? high : low)
    .replaceAll('|', '\n');
}

function expectExactCoverage(mods, selected, output) {
  assert.equal(output.valid, true, output.warnings.join('; '));
  const block = output.parts.find(part => part.kind === 'exclude');
  assert.ok(block);
  const pattern = new RegExp(block.text.slice(2, -1), 'im');
  for (const mod of mods) {
    for (const sample of rollSamples(mod.matchText)) {
      assert.equal(pattern.test(sample), selected.has(mod.id), `${mod.name}: ${sample}`);
    }
  }
}

test('shortens selected normal modifiers without catching unselected ones', () => {
  const mods = catalogue(false);
  const selected = new Set(['252096506', '1305115176', '-477049138', '-1344829253']);
  const overrides = Object.fromEntries([...selected].map(id => [id, 'block']));
  const output = buildRegex(mods, 'balanced', overrides, EMPTY_PREFERENCES);
  expectExactCoverage(mods, selected, output);
  assert.ok(output.length < 70, `Expected a short query, got ${output.length}`);
});

test('signed rolls and mixed intermediate rolls are all expanded', () => {
  const samples = rollSamples('A (-3—-1)% B (1—3)%');
  assert.equal(samples.length, 9);
  assert.ok(samples.includes('A -2% B 2%'));
  assert.ok(samples.includes('A -3% B 3%'));
});

test('a recovery substring cannot silently exclude cooldown recovery', () => {
  const mods = [
    { id: 'recovery', name: 'Life recovery', matchText: 'Players have 60% less Recovery Rate of Life and Energy Shield', pattern: 'recovery rate', rating: 'brick', mapPool: 'normal' },
    { id: 'cooldown', name: 'Cooldown recovery', matchText: 'Players have 40% less Cooldown Recovery Rate', pattern: 'cooldown recovery rate', rating: 'free', mapPool: 'normal' },
  ];
  const output = buildRegex(mods, 'greedy', {}, noMinimums);
  expectExactCoverage(mods, new Set(['recovery']), output);
});

test('a pattern matching only range endpoints cannot miss the middle rolls', () => {
  const mods = [
    { id: 'a', name: 'A', matchText: 'Players have (1—3)% alpha recovery', pattern: '[13]% alpha', rating: 'brick', mapPool: 'normal' },
    { id: 'b', name: 'B', matchText: 'Players have (1—3)% beta recovery', pattern: 'beta', rating: 'free', mapPool: 'normal' },
  ];
  expectExactCoverage(mods, new Set(['a']), buildRegex(mods, 'greedy', {}, noMinimums));
});

test('Unknowns need review in every preset; Balanced respects measured recovery conflicts', () => {
  const unknown = { id: 'unknown', rating: 'review' };
  const conflict = { id: 'pair', rating: 'free', combination_avoid: true };
  assert.equal(recommendedDecision(unknown, 'safe'), 'neutral');
  assert.equal(recommendedDecision(unknown, 'balanced'), 'neutral');
  assert.equal(recommendedDecision(conflict, 'balanced'), 'block');
  assert.equal(recommendedDecision(conflict, 'greedy'), 'allow');
});

test('overflow never silently drops required exclusions', () => {
  const mods = catalogue(false).map(mod => ({ ...mod, rating: 'brick' }));
  const output = buildRegex(mods, 'greedy', {}, noMinimums, 20);
  assert.equal(output.blocked.length, mods.length);
  assert.ok(output.length > 20);
  assert.ok(output.warnings.some(warning => warning.includes('game limit')));
  expectExactCoverage(mods, new Set(mods.map(mod => mod.id)), output);
});

test('the supplied Nightmare avoid pool covers its selected modifiers only', () => {
  const mods = catalogue(true);
  const selected = new Set(mods.filter(mod => mod.suppliedAvoid).map(mod => mod.id));
  const overrides = Object.fromEntries(mods.map(mod => [mod.id, selected.has(mod.id) ? 'block' : 'allow']));
  const output = buildRegex(mods, 'balanced', overrides, EMPTY_PREFERENCES);
  expectExactCoverage(mods, selected, output);
});

test('the supplied normal avoid pool stays accurate when it exceeds the game limit', () => {
  const mods = catalogue(false);
  const selected = new Set(mods.filter(mod => mod.suppliedAvoid).map(mod => mod.id));
  const overrides = Object.fromEntries(mods.map(mod => [mod.id, selected.has(mod.id) ? 'block' : 'allow']));
  const output = buildRegex(mods, 'balanced', overrides, EMPTY_PREFERENCES);
  expectExactCoverage(mods, selected, output);
  if (output.length > 250) assert.ok(output.warnings.some(warning => warning.includes('game limit')));
});

test('wanted modifiers create a separate positive term', () => {
  const mods = catalogue(false);
  const output = buildRegex(mods, 'balanced', {
    '252096506': 'block', '1062763755': 'want',
  }, EMPTY_PREFERENCES);
  assert.equal(output.valid, true);
  assert.equal(output.parts.length, 3);
  assert.equal(output.wanted.length, 1);
  assert.ok(output.regex.includes(' '));
});

test('a few Nightmare clicks keep the requested short fragments and order', () => {
  const mods = catalogue(true);
  const selected = new Set(['-2064669900', '-2038489408', '-1940135977', '-1818595967', '-1621497665']);
  const overrides = Object.fromEntries([...selected].map(id => [id, 'block']));
  const output = buildRegex(mods, 'balanced', overrides, noMinimums);
  expectExactCoverage(mods, selected, output);
  assert.equal(output.regex, '"!cco|m resistances$|k damage$|re sha|mum f"');
});

test('a few normal map clicks keep the requested short fragments and order', () => {
  const mods = catalogue(false);
  const selected = new Set(['-2050206104', '-477049138', '10729340', '252096506', '1101434369']);
  const overrides = Object.fromEntries([...selected].map(id => [id, 'block']));
  const output = buildRegex(mods, 'balanced', overrides, noMinimums);
  expectExactCoverage(mods, selected, output);
  assert.equal(output.regex, '"!te o|m resistances$|ds on|from$|ills$"');
});

test('all 47 PoEDB Nightmare affixes are present and individually selectable', () => {
  const mods = catalogue(true);
  assert.equal(mods.length, 47);
  assert.equal(new Set(mods.map(mod => mod.id)).size, 47);
  for (const mod of mods) {
    const selected = new Set([mod.id]);
    const output = buildRegex(mods, 'balanced', { [mod.id]: 'block' }, EMPTY_PREFERENCES);
    expectExactCoverage(mods, selected, output);
  }
});

test('all 78 PoEDB top-tier normal affixes are present and individually selectable', () => {
  const mods = catalogue(false);
  assert.equal(mods.length, 78);
  assert.equal(new Set(mods.map(mod => mod.id)).size, 78);
  for (const mod of mods) {
    const selected = new Set([mod.id]);
    const output = buildRegex(mods, 'balanced', { [mod.id]: 'block' }, EMPTY_PREFERENCES);
    expectExactCoverage(mods, selected, output);
  }
});

test('number ranges match their inclusive bounds across map values', () => {
  for (const [min, max] of [[0, 9], [40, 60], [100, 999], [105, 205], [999, 999]]) {
    const pattern = new RegExp(`^(?:${numberRangeRegex(min, max)})$`);
    for (let value = 0; value <= 999; value++) {
      assert.equal(pattern.test(String(value)), value >= min && value <= max, `${min}-${max} at ${value}`);
    }
  }
});

test('new preferences require 40% item quantity, which can be cleared or changed', () => {
  const initial = buildRegex([], 'balanced', {}, EMPTY_PREFERENCES);
  assert.equal(initial.valid, true);
  assert.equal(initial.parts.length, 1);
  const pattern = new RegExp(initial.parts[0].text.slice(1, -1), 'i');
  assert.equal(pattern.test('Item Quantity: +39%'), false);
  assert.equal(pattern.test('Item Quantity: +40%'), true);
  assert.equal(pattern.test('Item Quantity: +100%'), true);
  assert.equal(buildRegex([], 'balanced', {}, noMinimums).regex, '');
  assert.notEqual(buildRegex([], 'balanced', {}, { ...EMPTY_PREFERENCES, minimums: { quantity: '80' } }).regex, initial.regex);
});

test('legacy quality inputs no longer add search terms', () => {
  const result = buildRegex([], 'balanced', {}, {
    ...EMPTY_PREFERENCES,
    minimums: { quantity: '40', quality_Quantity: '20', quality_Currency: '20' },
  });
  assert.equal(result.valid, true);
  assert.equal(result.parts.length, 1);
  assert.equal(result.regex, buildRegex([], 'balanced', {}, EMPTY_PREFERENCES).regex);
});

test('map value inputs change the copyable regex immediately', () => {
  const preferences = { ...EMPTY_PREFERENCES, minimums: { quantity: '100', pack: '40', currency: '50' } };
  const result = buildRegex([], 'balanced', {}, preferences);
  assert.equal(result.valid, true);
  assert.match(result.regex, /"m q\.\*\[1-9\]\.\.%"/);
  assert.match(result.regex, /"iz\.\*/);
  assert.match(result.regex, /"cy:\.\*/);
  assert.equal(result.parts.length, 3);
  assert.notEqual(buildRegex([], 'balanced', {}, { ...preferences, minimums: { quantity: '110' } }).regex, result.regex);
});

test('every map value field emits a separate numeric condition', () => {
  const minimums = Object.fromEntries(['quantity', 'pack', 'maps', 'rarity', 'currency', 'scarabs', 'divination'].map(key => [key, '50']));
  const result = buildRegex([], 'balanced', {}, { ...EMPTY_PREFERENCES, minimums });
  assert.equal(result.valid, true);
  assert.equal(result.parts.filter(part => part.kind === 'preference').length, 7);
  for (const sample of ['Item Quantity: +50%', 'Monster Pack Size: +50%', 'More Maps: +50%', 'Item Rarity: +50%', 'More Currency: +50%', 'More Scarabs: +50%', 'More Divination: +50%']) {
    assert.ok(result.parts.some(part => new RegExp(part.text.slice(1, -1), 'i').test(sample)), sample);
  }
});

test('maximums and state filters are included while invalid ranges block copying', () => {
  const selected = { ...EMPTY_PREFERENCES, minimums: { quantity: '100', max_quantity: '120' },
    corrupted: true, unidentified: true, rarities: ['Rare'] };
  const result = buildRegex([], 'balanced', {}, selected);
  assert.equal(result.valid, true);
  assert.match(result.regex, /corrupted unidentified "y: r"/);
  const numeric = result.parts.find(part => part.text.startsWith('"m q.'));
  assert.ok(numeric);
  const number = new RegExp(numeric.text.slice(1, -1), 'i');
  assert.equal(number.test('Item Quantity: +100%'), true);
  assert.equal(number.test('Item Quantity: +120%'), true);
  assert.equal(number.test('Item Quantity: +121%'), false);
  assert.equal(buildRegex([], 'balanced', {}, { ...selected, minimums: { quantity: '120', max_quantity: '100' } }).valid, false);
});

test('trade-only preferences are identified without claiming to be in the copied regex', () => {
  const result = buildRegex([], 'balanced', {}, { ...EMPTY_PREFERENCES, eightMod: true, excludeValdo: true });
  assert.equal(result.parts.length, 1);
  assert.match(result.regex, /^"m q\./);
  assert.match(result.warnings.join(' '), /Trade filters only/);
});

test('Free policy is distinguished from verified safety and manual choice still wins', () => {
  const mods = catalogue(false).slice(0, 1).map(mod => ({ ...mod, rating: 'free', assessment_status: 'policy' }));
  const allowed = buildRegex(mods, 'greedy', {}, noMinimums);
  assert.ok(allowed.warnings.some(warning => warning.includes('Free policy')));
  const blocked = buildRegex(mods, 'greedy', { [mods[0].id]: 'block' }, noMinimums);
  assert.equal(blocked.blocked.length, 1);
  assert.ok(!blocked.warnings.some(warning => warning.includes('Free policy')));
});
