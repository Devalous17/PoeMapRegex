import { ModText } from '../../components/ModText';
import { assessmentSummary } from '../../components/assessmentText';
import { Sprite } from '../../components/Sprite';
import { Icon } from '../../components/Icon';
import { useModHighlight } from '../../components/HighlightContext';
import { useMemo, useState } from 'react';
import { Button, SectionHeading, SeverityOrb, ratingLabels } from '../../components/UI';
import { recommendedDecision } from '../../services/regexBuilder';
import { useAppStore } from '../../store/useAppStore';
import type { Category, ClassifiedMod, Decision, Rating } from '../../types';

const categoryIcons: Record<Category, string> = {"Thorns": "thorns", "Recovery / Leech": "recovery", "Cooldown / Triggers": "cooldown", "Defences": "defences", "Resistances": "resistances", "Charges": "charges", "Ailments / Curses": "ailments", "Monsters": "monsters", "Area": "area", "Other": "other"};
const ratingOrder: Rating[] = ['brick', 'dangerous', 'uncomfortable', 'review', 'free'];
const categoryOrder: Category[] = ['Thorns', 'Recovery / Leech', 'Cooldown / Triggers', 'Defences', 'Resistances', 'Charges', 'Ailments / Curses', 'Monsters', 'Area', 'Other'];

function modifierText(mod: ClassifiedMod): string {
  return (mod.effectText ?? mod.matchText ?? mod.name)
    .replaceAll(/\[([^|\]]+)\|([^\]]+)\]/g, '$2')
    .replaceAll(/\((\d+)-(\d+)\)/g, '$1–$2')
    .replaceAll('|', ' · ');
}

const basisLabels = { snapshot_model: 'Calculated estimate', dependency_rule: 'Detected dependency', user_confirmation: 'Your confirmation', conservative_policy: 'Conservative exclusion', policy_allowance: 'Policy allowance', unknown: 'Needs review' };

function ModRow({ mod, action, explain }: { mod: ClassifiedMod; action: 'block' | 'want'; explain: boolean }) {
  const { ids, setIds } = useModHighlight();
  const preset = useAppStore(state => state.preset);
  const override = useAppStore(state => state.overrides[mod.id]);
  const setDecision = useAppStore(state => state.setDecision);
  const decision = override ?? recommendedDecision(mod, preset);
  const active = decision === action;
  const description = modifierText(mod);
  const basis = mod.assessment_basis ? basisLabels[mod.assessment_basis] : '';
  const detail = [basis, mod.reason, mod.combination_reason, mod.confidence && `Confidence: ${mod.confidence}`, mod.affixName && `${mod.affixName} · ${mod.affixKind} · spawn weight ${mod.spawnWeight}`, mod.rewardText].filter(Boolean).join('\n');
  return <button type="button" className={`mod-pick mod-pick--${action} mod-pick--rating-${mod.rating} ${active ? 'is-selected' : ''} ${ids.includes(mod.id) ? 'is-linked' : ''}`} onMouseEnter={() => setIds([mod.id])} onMouseLeave={() => setIds([])} onFocus={() => setIds([mod.id])} onBlur={() => setIds([])}
    aria-pressed={active} aria-label={`${active ? 'Remove' : 'Add'} ${description} ${active ? 'from' : 'to'} ${action === 'block' ? 'avoided' : 'wanted'} mods`}
    title={detail} onClick={() => setDecision(mod.id, active ? 'allow' : action)}>
    <Sprite name="row" /><span className="mod-pick__check" aria-hidden="true">{active ? <b>✓</b> : <Sprite name="plus" />}</span>
    <span className="mod-pick__text"><ModText text={description} />{explain && <small className="mod-pick__reason">{assessmentSummary([mod.reason, mod.combination_reason].filter(Boolean).join(' '))}</small>}</span>
    {mod.affixName && <span className="mod-pick__meta">{mod.affixName} · {mod.affixKind}</span>}
    <span className="mod-pick__rating"><SeverityOrb rating={mod.rating} small />{mod.manual ? 'Not assessed' : mod.combination_avoid ? 'Recovery pair' : ratingLabels[mod.rating]}</span>
  </button>;
}

function Filters({ mods }: { mods: ClassifiedMod[] }) {
  const ratingFilter = useAppStore(state => state.ratingFilter);
  const setRatingFilter = useAppStore(state => state.setRatingFilter);
  const categories = useAppStore(state => state.categories);
  const toggleCategory = useAppStore(state => state.toggleCategory);
  const availableCategories = categoryOrder.filter(category => mods.some(mod => mod.category === category));
  return <details className="mod-filters" open><summary>Filter by build rating or category <span aria-hidden="true">⌄</span></summary><Sprite name="filters" />
    <div className="mod-filters__body"><div className="mod-filters__group"><strong>Build rating</strong>
      <button type="button" className={ratingFilter === 'all' ? 'is-active' : ''} aria-pressed={ratingFilter === 'all'} onClick={() => setRatingFilter('all')}><Sprite name={ratingFilter === 'all' ? 'chipActive' : 'chip'} />All <small>{mods.length}</small></button>
      {ratingOrder.map(rating => <button type="button" key={rating} className={ratingFilter === rating ? 'is-active' : ''} aria-pressed={ratingFilter === rating} onClick={() => setRatingFilter(rating)}><Sprite name={ratingFilter === rating ? 'chipActive' : 'chip'} />{ratingLabels[rating]} <small>{mods.filter(mod => mod.rating === rating).length}</small></button>)}
    </div><div className="mod-filters__group"><strong>Category</strong>
      {availableCategories.map((category) => <button type="button" key={category} className={categories.includes(category) ? 'is-active' : ''} aria-pressed={categories.includes(category)} onClick={() => toggleCategory(category)}><Sprite name={categories.includes(category) ? 'chipActive' : 'chip'} /><Icon name={categoryIcons[category]} />{category} <small>{mods.filter(mod => mod.category === category).length}</small></button>)}
    </div></div>
  </details>;
}

function SelectedModsWindow({ blocked, wanted }: { blocked: ClassifiedMod[]; wanted: ClassifiedMod[] }) {
  const setDecision = useAppStore(state => state.setDecision);
  return <aside className="selected-mods-window" aria-label="Selected map modifiers">
    <div className="selected-mods-window__header"><div><span className="panel-kicker">CURRENT MAP POOL</span><h3>Selected modifiers</h3></div><span>{blocked.length + wanted.length} selected</span></div>
    <div className="selected-mods-window__columns">
      {([['Avoid', blocked], ['Want', wanted]] as const).filter(([label, selected]) => selected.length > 0 || (label === 'Avoid' && !blocked.length && !wanted.length)).map(([label, selected]) => <div className="selected-mods-window__group" key={label}>
        <div className="selected-mods-window__group-title"><strong>{label}</strong><span>{selected.length}</span></div>
        <div className="selected-mods-window__list" role="list" aria-label={`${label} selected modifiers`}>
          {selected.map(mod => <div role="listitem" key={mod.id}><button type="button" className={`selected-mod selected-mod--${mod.rating}`} title={mod.reason} aria-label={`Remove ${modifierText(mod)} from ${label.toLowerCase()} list`} onClick={() => setDecision(mod.id, 'allow')}><Sprite name="row" /><SeverityOrb rating={mod.rating} small /><span><ModText text={modifierText(mod)} /></span><span className="remove-selected" aria-hidden="true"><Sprite name="remove" /></span></button></div>)}
          {!selected.length && <p className="selected-mods-window__empty">No {label.toLowerCase()} modifiers selected.</p>}
        </div>
      </div>)}
    </div>
    <p className="selected-mods-window__hint">Click a selected modifier here to remove it. This list shows every selection, even when the database is filtered.</p>
  </aside>;
}

export function SelectionPanel({ mods, action, setAction, mode }: { mods: ClassifiedMod[]; action: 'block' | 'want'; setAction: (value: 'block' | 'want') => void; mode: 'live' | 'example' | 'manual' }) {
  const preset = useAppStore(state => state.preset);
  const overrides = useAppStore(state => state.overrides);
  const resetDecisions = useAppStore(state => state.resetDecisions);
  const clearDecisions = useAppStore(state => state.clearDecisions);
  const applySuppliedAvoid = useAppStore(state => state.applySuppliedAvoid);
  const blocked = mods.filter(mod => (overrides[mod.id] ?? recommendedDecision(mod, preset)) === 'block');
  const wanted = mods.filter(mod => (overrides[mod.id] ?? recommendedDecision(mod, preset)) === 'want');
  return <><div className="group-controls"><strong>Group Type</strong><div role="group" aria-label="Modifier selection mode"><button type="button" aria-pressed={action === 'block'} className={action === 'block' ? 'is-active is-not' : ''} onClick={() => setAction('block')}><Sprite name="not" />NOT <span>Avoid</span></button><button type="button" aria-pressed={action === 'want'} className={action === 'want' ? 'is-active' : ''} onClick={() => setAction('want')}><Sprite name="and" />AND <span>Want</span></button></div><span className="group-matches">Matches <b>All</b></span></div>
    <SelectedModsWindow blocked={blocked} wanted={wanted} />
    <p className="group-explanation">Exclude maps with any avoided mod. Require every wanted mod and map value.</p>
    <div className="selection-actions">{mode !== 'manual' && <Button variant="quiet" onClick={() => applySuppliedAvoid(mods)}>Apply avoid list</Button>}<Button variant="quiet" onClick={() => clearDecisions(mods)}>Clear selections</Button><Button variant="quiet" onClick={resetDecisions}>{mode === 'manual' ? 'Reset choices' : 'Use preset'}</Button></div>
    <a className="add-modifier" href="#mod-database"><Sprite name="add" />Add a modifier or requirement <span aria-hidden="true">+</span></a>
  </>;
}

export function ModAnalysis({ mods, mode, action, setAction }: { mods: ClassifiedMod[]; mode: 'live' | 'example' | 'manual'; action: 'block' | 'want'; setAction: (value: 'block' | 'want') => void }) {
  const preset = useAppStore(state => state.preset);
  const overrides = useAppStore(state => state.overrides);
  const ratingFilter = useAppStore(state => state.ratingFilter);
  const search = useAppStore(state => state.search);
  const setSearch = useAppStore(state => state.setSearch);
  const categories = useAppStore(state => state.categories);
  const mapPool = useAppStore(state => state.mapPool);
  const [selectedOnly, setSelectedOnly] = useState(false);
  const [explain, setExplain] = useState(false);
  const selected = useMemo(() => ({
    block: mods.filter(mod => (overrides[mod.id] ?? recommendedDecision(mod, preset)) === 'block'),
    want: mods.filter(mod => (overrides[mod.id] ?? recommendedDecision(mod, preset)) === 'want'),
  }), [mods, overrides, preset]);
  const counts = { block: selected.block.length, want: selected.want.length };
  const visible = useMemo(() => mods.filter(mod => {
    const decision: Decision = overrides[mod.id] ?? recommendedDecision(mod, preset);
    return (ratingFilter === 'all' || mod.rating === ratingFilter) &&
      (!categories.length || categories.includes(mod.category)) &&
      (!selectedOnly || decision === action) &&
      (!search.trim() || `${modifierText(mod)} ${mod.category} ${mod.tags.join(' ')}`.toLowerCase().includes(search.toLowerCase().trim()));
  }), [mods, overrides, preset, ratingFilter, categories, selectedOnly, action, search]);
  return <section id="mod-database" className="content-section">
    <SectionHeading number="03" title="Map Modifier Database" subtitle={mode === 'manual' ? 'Browse and select modifiers. Import a build for personalised ratings.' : 'Click a modifier to add or remove it from your regex.'} aside={<span className="edition-tag">POE 1 · NORMAL & NIGHTMARE</span>} />
    <div className="mod-picker"><Sprite name="database" />
      <div className="mod-picker__modes" role="group" aria-label="Modifier selection mode">
        <button type="button" className={action === 'block' ? 'is-active' : ''} aria-pressed={action === 'block'} onClick={() => setAction('block')}><Sprite name="avoid" />● I don't want these mods <span>{counts.block}</span></button>
        <button type="button" className={action === 'want' ? 'is-active' : ''} aria-pressed={action === 'want'} onClick={() => setAction('want')}><Sprite name="want" />✦ I want these mods <span>{counts.want}</span></button>
      </div>
      <div className="mod-picker__tools"><label className="mod-picker__selected"><input type="checkbox" checked={selectedOnly} onChange={event => setSelectedOnly(event.target.checked)} /> Selected only</label><div className="database-search"><Sprite name="search" /><input aria-label="Search modifiers" placeholder="Search mods…" value={search} onChange={e=>setSearch(e.target.value)} /></div></div>
      <Filters mods={mods} />
      {mode !== 'manual' && mapPool === 'nightmare' && <p className="scope-note">Nightmare recommendations follow your reviewed modifier policy, with build checks for attacks, flasks, Chaos Resistance, critical-strike protection and stuns. Show explanations to see why each mod is selected.</p>}
      <label className="mod-picker__selected"><input type="checkbox" checked={explain} onChange={event => setExplain(event.target.checked)} /> Show assessment explanations</label>
      <div className="rating-legend" aria-label="Rating legend">{ratingOrder.map(rating => <span key={rating}><SeverityOrb rating={rating} small />{ratingLabels[rating]}</span>)}</div><div className="mod-picker__status"><span><strong>{visible.length}</strong> of {mods.length} modifiers</span><span>Click a row to {action === 'block' ? 'block or unblock' : 'want or remove'} it</span></div>
      <div className="mod-picker__list" role="list" aria-label={`${mapPool === 'nightmare' ? 'Nightmare' : 'Normal'} map modifiers`}>
        {visible.map(mod => <div role="listitem" key={mod.id}><ModRow mod={mod} action={action} explain={explain} /></div>)}
        {!visible.length && <div className="empty-mods"><strong>No modifiers match.</strong><p>Try a different search or clear the filters.</p></div>}
      </div>
    </div>
    <p className="scope-note">{mode === 'example' ? 'Example build ratings are illustrative. ' : ''}The catalogue has 78 <a href="https://poedb.tw/us/Maps_top_tier" target="_blank" rel="noreferrer">top tier normal</a> and 47 <a href="https://poedb.tw/us/Nightmare_map" target="_blank" rel="noreferrer">Nightmare</a> affix entries from PoEDB. Hover a row for its affix name, roll weight and reward lines. Build ratings cover a focused subset; check the rest yourself.</p>
  </section>;
}
