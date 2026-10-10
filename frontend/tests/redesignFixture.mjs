import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { buildRegex } from '../src/services/regexBuilder.ts';
import { EMPTY_PREFERENCES } from '../src/types.ts';

const baseline = JSON.parse(readFileSync(new URL('../../fixtures/redesign-baseline.json', import.meta.url)));
// Source equality additionally protects optimization, numeric filters and store defaults.
for (const name of ['regexBuilder.ts','mapPreferencesRegex.ts']) {
  const bytes=readFileSync(new URL(`../src/services/${name}`,import.meta.url));
  assert.equal(createHash('sha256').update(bytes).digest('hex'), baseline.protected[`frontend/src/services/${name}`]);
}
const mods=baseline.analysis.mods.filter(mod=>!mod.id.startsWith('map-')).map(mod=>({...mod,category:'Other',tags:[]}));
const actual=Object.fromEntries(['safe','balanced','greedy'].map(preset=>[preset,buildRegex(mods,preset,{},EMPTY_PREFERENCES)]));
const expectedFile=new URL('../../fixtures/redesign-frontend-baseline.json',import.meta.url);
assert.deepEqual(actual,JSON.parse(readFileSync(expectedFile)));
console.log('PASS: frontend fixture regex, selections, warnings and length limits are identical.');
