import { Button, Check, Panel, SectionHeading } from '../../components/UI';
import { useAppStore } from '../../store/useAppStore';
import type { Preferences as PreferencesType } from '../../types';

const valueFields = [
  ['quantity', 'Item Quantity'], ['pack', 'Monster Pack Size'], ['maps', 'More Maps'],
  ['rarity', 'Item Rarity'], ['currency', 'More Currency'], ['scarabs', 'More Scarabs'], ['divination', 'More Divination'],
] as const;
const chiselTypes = ['Quantity', 'Pack size', 'Item rarity', 'Currency', 'Scarabs', 'Divination', 'More maps'];

export function Preferences() {
  const preferences = useAppStore(state => state.preferences);
  const setPreferences = useAppStore(state => state.setPreferences);
  const resetPreferences = useAppStore(state => state.resetPreferences);
  const update = (patch: Partial<PreferencesType>) => setPreferences({ ...preferences, ...patch });
  const toggleList = (key: 'rarities' | 'chisels', entry: string) => update({ [key]: preferences[key].includes(entry) ? preferences[key].filter(item => item !== entry) : [...preferences[key], entry] });
  const setNumber = (key: string, value: string) => update({ minimums: { ...preferences.minimums, [key]: value } });
  return <section id="preferences" className="content-section preferences-section">
    <SectionHeading number="04" title="Map preferences" subtitle="Shape the maps you want to search for." aside={<span className="edition-tag">LIVE REGEX</span>} />
    <Panel className="preferences-panel">
      <div className="preferences-intro"><div><span className="panel-kicker">FURTHER REFINEMENT</span><h3>Fine-tune your maps</h3><p>Map values, rarity, state and available quality types update the search above as you change them.</p></div><Button type="button" variant="quiet" onClick={resetPreferences}>Reset all</Button></div>
      <div className="preferences-grid">
        <details className="preference-group" open><summary>MAP VALUES <span aria-hidden="true">+</span></summary><div className="value-fields">
          {valueFields.map(([key, label]) => <div className="value-field" key={key}><label htmlFor={`minimum-${key}`}>{label}</label><div className="value-field__inputs"><span>MIN</span><input id={`minimum-${key}`} className="poe-input" type="number" min="0" max="999" value={preferences.minimums[key] || ''} onChange={event => setNumber(key, event.target.value)} placeholder="—" /><span>MAX</span><input aria-label={`${label} maximum`} className="poe-input" type="number" min="0" max="999" value={preferences.minimums[`max_${key}`] || ''} onChange={event => setNumber(`max_${key}`, event.target.value)} placeholder="—" /></div></div>)}
        </div></details>
        <div className="preference-column">
          <details className="preference-group" open><summary>STATE &amp; RARITY <span aria-hidden="true">+</span></summary><div className="preference-checks"><Check label="Corrupted" checked={preferences.corrupted} onChange={corrupted => update({ corrupted })} /><Check label="Unidentified" checked={preferences.unidentified} onChange={unidentified => update({ unidentified })} /><div className="check-subtitle">MAP RARITY</div><div className="rarity-row">{['Normal', 'Magic', 'Rare'].map(rarity => <Check key={rarity} label={rarity} checked={preferences.rarities.includes(rarity)} onChange={() => toggleList('rarities', rarity)} />)}</div></div></details>
          <details className="preference-group" open><summary>MAP QUALITY TYPE <span aria-hidden="true">+</span></summary><div className="preference-checks chisel-grid">{chiselTypes.map(chisel => <Check key={chisel} label={chisel === 'More maps' ? 'More maps (not a chisel type)' : chisel} checked={preferences.chisels.includes(chisel)} disabled={chisel === 'More maps'} onChange={() => toggleList('chisels', chisel)} />)}</div></details>
          <details className="preference-group" open><summary>TRADE-ONLY FILTERS <span aria-hidden="true">+</span></summary><div className="preference-checks"><p className="preference-note">These selections need PoE Trade data and cannot be guaranteed by a stash regex.</p><Check label="8-mod maps only" checked={preferences.eightMod} onChange={eightMod => update({ eightMod })} /><Check label="Exclude Valdo maps" checked={preferences.excludeValdo} onChange={excludeValdo => update({ excludeValdo })} /><Check label="Exclude Shaper-influenced" checked={preferences.excludeShaper} onChange={excludeShaper => update({ excludeShaper })} /><Check label="Exclude Elder-influenced" checked={preferences.excludeElder} onChange={excludeElder => update({ excludeElder })} /></div></details>
        </div>
      </div>
    </Panel>
  </section>;
}
