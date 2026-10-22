import { Sprite } from './Sprite';
import { recommendedDecision } from '../services/regexBuilder';
import { useAppStore } from '../store/useAppStore';
import type { ClassifiedMod } from '../types';

function riskTag(mod: ClassifiedMod): { label: string; color: number } {
  const text = `${mod.name} ${mod.effectText ?? ''}`;
  if (/physical thorns/i.test(text)) return {label: 'Physical Thorns', color: 0};
  if (/elemental thorns/i.test(text)) return {label: 'Elemental Thorns', color: 1};
  if (/cannot regenerate/i.test(text)) return {label: 'No Regeneration', color: 2};
  if (/cannot.*leech/i.test(text)) return {label: 'No Leech', color: 3};
  if (/maximum resistances/i.test(text)) return {label: 'Minus Max Res', color: 4};
  if (/vulnerability/i.test(text)) return {label: 'Vulnerability', color: 5};
  if (/enfeeble/i.test(text)) return {label: 'Enfeeble', color: 6};
  if (/cooldown/i.test(text)) return {label: 'Less Cooldown Recovery', color: 2};
  if (/recovery rate/i.test(text)) return {label: 'Less Recovery', color: 2};
  if (/armour/i.test(text)) return {label: 'Less Armour / Block', color: 1};
  if (/avoid elemental ailments/i.test(text)) return {label: 'Avoid Elemental Ailments', color: 5};
  if (/critical strikes/i.test(text)) return {label: 'Less Critical Damage', color: 6};
  if (/flask/i.test(text)) return {label: 'Reduced Flask Charges', color: 3};
  return {label: mod.name, color: 0};
}

export function MapSearch() {
  const mapPool = useAppStore(state => state.mapPool);
  const setMapPool = useAppStore(state => state.setMapPool);
  return <section className="map-search-row"><h2>Choose Map Type</h2><div className="map-type-tabs" role="group" aria-label="Map type"><button type="button" className={mapPool === 'normal' ? 'is-active' : ''} aria-pressed={mapPool === 'normal'} onClick={()=>setMapPool('normal')}><Sprite name="chip" /><img className="map-type-icon" src="/assets/figma/lava-lake.png" width="78" height="78" alt="" data-figma-node="8:2" />Standard Map</button><button type="button" className={mapPool === 'nightmare' ? 'is-active' : ''} aria-pressed={mapPool === 'nightmare'} onClick={()=>setMapPool('nightmare')}><Sprite name="chip" /><img className="map-type-icon" src="/assets/figma/abomination.png" width="78" height="78" alt="" data-figma-node="8:3" />T17 Mods</button></div></section>;
}

export function Vulnerabilities({ mods }: { mods: ClassifiedMod[] }) {
  const analysis = useAppStore(state => state.analysis);
  const preset = useAppStore(state => state.preset);
  const overrides = useAppStore(state => state.overrides);
  const setSearch = useAppStore(state => state.setSearch);
  const affected = mods.filter(mod => !mod.manual && ['brick', 'dangerous', 'uncomfortable'].includes(mod.rating) && (overrides[mod.id] ?? recommendedDecision(mod, preset)) === 'block');
  return <section className="vulnerabilities-section" aria-labelledby="vulnerability-heading"><h2 id="vulnerability-heading">Tag Filter / Vulnerabilities</h2><div className="tool-panel vulnerability-panel">
    {affected.length ? <div className="vulnerability-tags">{affected.map(mod => <button type="button" key={mod.id} className={`vulnerability-tag tag-color-${riskTag(mod).color}`} title={`${mod.name}\n${mod.reason}`} onClick={() => { setSearch(mod.name); document.getElementById('mod-database')?.scrollIntoView({block:'start'}); }}>{riskTag(mod).label}</button>)}</div> : <p className="empty-state">{analysis ? 'No assessed risks are blocked by your current choices.' : 'Import a build to see its detected vulnerabilities.'}</p>}
    <p className="panel-note">{affected.length ? 'Detected risks in your current block list. Click a tag to find the modifier.' : 'Manual selections remain available in the modifier database.'}</p>
  </div></section>;
}

export function BuildStatus({ mods }: { mods: ClassifiedMod[] }) {
  const analysis = useAppStore(state => state.analysis);
  const loading = useAppStore(state => state.loading);
  const error = useAppStore(state => state.error);
  const bricks = mods.filter(mod => !mod.manual && mod.rating === 'brick').length;
  const danger = mods.filter(mod => !mod.manual && mod.rating === 'dangerous').length;
  return <section className="build-status-section" aria-labelledby="status-heading"><h2 id="status-heading">Calculations / Analysis</h2><div className="tool-panel analysis-panel" role="status" aria-live="polite"><Sprite name="status" />
    <p><span className={`status-mark ${analysis ? 'is-ok' : ''}`} aria-hidden="true">{analysis ? '✓' : '○'}</span>{loading ? 'Importing Path of Building…' : analysis ? `${analysis.profile.main_skill || 'Build'} imported` : 'Waiting for a PoB import'}</p>
    <p><span className={`status-mark ${analysis ? 'is-ok' : ''}`} aria-hidden="true">{analysis ? '✓' : '○'}</span>{analysis ? `${mods.length} map modifiers analyzed` : 'Build dependencies checked after import'}</p>
    {analysis && <><p><span className="status-mark is-warning" aria-hidden="true">!</span>{bricks} build-breaking · {danger} dangerous mods</p><p className="analysis-build-name">{analysis.profile.ascendancy || analysis.profile.class} · Level {analysis.profile.level}</p><a href="#build-profile">View defensive layers & analysis</a>{!!analysis.profile.coverage?.issues.length && <p className="panel-note">{analysis.profile.coverage.issues.length} checks need your review.</p>}</>}
    {error && <p className="status-error">{error}</p>}
    <p className="panel-note">Recommendations use your saved PoB. Review conditional mechanics before mapping.</p>
  </div></section>;
}
