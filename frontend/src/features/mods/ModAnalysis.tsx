import { useMemo, useState } from 'react';
import { Button, SectionHeading, SeverityOrb, ratingLabels } from '../../components/UI';
import { recommendedDecision } from '../../services/regexBuilder';
import { useAppStore } from '../../store/useAppStore';
import type { Category, ClassifiedMod, Decision, Rating } from '../../types';

const ratingOrder: Rating[] = ['brick', 'dangerous', 'uncomfortable', 'review', 'free'];
const categoryOrder: Category[] = ['Reflect', 'Recovery / Leech', 'Cooldown / Triggers', 'Resistances', 'Charges', 'Ailments / Curses', 'Monsters', 'Area', 'Other'];

function modifierText(mod: ClassifiedMod): string {
  return (mod.effectText ?? mod.matchText ?? mod.name)
    .replaceAll(/\[([^|\]]+)\|([^\]]+)\]/g, '$2')
    .replaceAll(/\((\d+)-(\d+)\)/g, '$1–$2')
    .replaceAll('|', ' · ');
}

function ModRow({ mod, action }: { mod: ClassifiedMod; action: 'block' | 'want' }) {
  const preset = useAppStore(state => state.preset);
  const override = useAppStore(state => state.overrides[mod.id]);
  const setDecision = useAppStore(state => state.setDecision);
  const decision = override ?? recommendedDecision(mod, preset);
  const active = decision === action;
  const description = modifierText(mod);
  const detail = [mod.reason, mod.affixName && `${mod.affixName} · ${mod.affixKind} · spawn weight ${mod.spawnWeight}`, mod.rewardText].filter(Boolean).join('\n');
  return <button type="button" className={`mod-pick mod-pick--${action} mod-pick--rating-${mod.rating} ${active ? 'is-selected' : ''}`}
    aria-pressed={active} aria-label={`${active ? 'Remove' : 'Add'} ${description} ${active ? 'from' : 'to'} ${action === 'block' ? 'avoided' : 'wanted'} mods`}
    title={detail} onClick={() => setDecision(mod.id, active ? 'allow' : action)}>
    <span className="mod-pick__check" aria-hidden="true">{active ? '✓' : '+'}</span>
    <span className="mod-pick__text">{description}</span>
    {mod.affixName && <span className="mod-pick__meta">{mod.affixName} · {mod.affixKind}</span>}
    <span className="mod-pick__rating"><SeverityOrb rating={mod.rating} small />{ratingLabels[mod.rating]}</span>
  </button>;
}

function Filters({ mods }: { mods: ClassifiedMod[] }) {
  const ratingFilter = useAppStore(state => state.ratingFilter);
  const setRatingFilter = useAppStore(state => state.setRatingFilter);
  const categories = useAppStore(state => state.categories);
  const toggleCategory = useAppStore(state => state.toggleCategory);
  const availableCategories = categoryOrder.filter(category => mods.some(mod => mod.category === category));
  return <details className="mod-filters"><summary>Filter by build rating or category <span aria-hidden="true">⌄</span></summary>
    <div className="mod-filters__body"><div className="mod-filters__group"><strong>Build rating</strong>
      <button type="button" className={ratingFilter === 'all' ? 'is-active' : ''} aria-pressed={ratingFilter === 'all'} onClick={() => setRatingFilter('all')}>All <small>{mods.length}</small></button>
      {ratingOrder.map(rating => <button type="button" key={rating} className={ratingFilter === rating ? 'is-active' : ''} aria-pressed={ratingFilter === rating} onClick={() => setRatingFilter(rating)}>{ratingLabels[rating]} <small>{mods.filter(mod => mod.rating === rating).length}</small></button>)}
    </div><div className="mod-filters__group"><strong>Category</strong>
      {availableCategories.map(category => <button type="button" key={category} className={categories.includes(category) ? 'is-active' : ''} aria-pressed={categories.includes(category)} onClick={() => toggleCategory(category)}>{category} <small>{mods.filter(mod => mod.category === category).length}</small></button>)}
    </div></div>
  </details>;
}

function SelectedModsWindow({ blocked, wanted }: { blocked: ClassifiedMod[]; wanted: ClassifiedMod[] }) {
  const setDecision = useAppStore(state => state.setDecision);
  return <aside className="selected-mods-window" aria-label="Selected map modifiers">
    <div className="selected-mods-window__header"><div><span className="panel-kicker">CURRENT MAP POOL</span><h3>Selected modifiers</h3></div><span>{blocked.length + wanted.length} selected</span></div>
    <div className="selected-mods-window__columns">
      {([['Avoid', blocked], ['Want', wanted]] as const).map(([label, selected]) => <div className="selected-mods-window__group" key={label}>
        <div className="selected-mods-window__group-title"><strong>{label}</strong><span>{selected.length}</span></div>
        <div className="selected-mods-window__list" role="list" aria-label={`${label} selected modifiers`}>
          {selected.map(mod => <div role="listitem" key={mod.id}><button type="button" className={`selected-mod selected-mod--${mod.rating}`} title={mod.reason} aria-label={`Remove ${modifierText(mod)} from ${label.toLowerCase()} list`} onClick={() => setDecision(mod.id, 'allow')}><SeverityOrb rating={mod.rating} small /><span>{modifierText(mod)}</span><span aria-hidden="true">×</span></button></div>)}
          {!selected.length && <p className="selected-mods-window__empty">No {label.toLowerCase()} modifiers selected.</p>}
        </div>
      </div>)}
    </div>
    <p className="selected-mods-window__hint">Click a selected modifier here to remove it. This list shows every selection, even when the database is filtered.</p>
  </aside>;
}

export function ModAnalysis({ mods, mode }: { mods: ClassifiedMod[]; mode: 'live' | 'example' }) {
  const preset = useAppStore(state => state.preset);
  const overrides = useAppStore(state => state.overrides);
  const ratingFilter = useAppStore(state => state.ratingFilter);
  const search = useAppStore(state => state.search);
  const setSearch = useAppStore(state => state.setSearch);
  const categories = useAppStore(state => state.categories);
  const resetDecisions = useAppStore(state => state.resetDecisions);
  const clearDecisions = useAppStore(state => state.clearDecisions);
  const mapPool = useAppStore(state => state.mapPool);
  const setMapPool = useAppStore(state => state.setMapPool);
  const applySuppliedAvoid = useAppStore(state => state.applySuppliedAvoid);
  const [action, setAction] = useState<'block' | 'want'>('block');
  const [selectedOnly, setSelectedOnly] = useState(false);
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
  return <section id="mods" className="content-section">
    <SectionHeading number="03" title="Map modifier database" subtitle="Click a modifier to add or remove it from your regex." aside={<span className="edition-tag">POE 1 · NORMAL & NIGHTMARE</span>} />
    <div className="mod-picker">
      <div className="mod-picker__header">
        <div className="map-pool-tabs" role="group" aria-label="Map type">
          <button type="button" className={mapPool === 'normal' ? 'is-active' : ''} aria-pressed={mapPool === 'normal'} onClick={() => setMapPool('normal')}>Normal maps <small>78</small></button>
          <button type="button" className={mapPool === 'nightmare' ? 'is-active' : ''} aria-pressed={mapPool === 'nightmare'} onClick={() => setMapPool('nightmare')}>Nightmare maps <small>47</small></button>
        </div>
        <div className="mod-picker__actions"><Button type="button" variant="quiet" onClick={() => applySuppliedAvoid(mods)}>Apply your avoid list</Button><Button type="button" variant="quiet" onClick={() => clearDecisions(mods)}>Clear selections</Button><Button type="button" variant="quiet" onClick={resetDecisions}>Use preset</Button></div>
      </div>
      <div className="mod-picker__modes" role="group" aria-label="Modifier selection mode">
        <button type="button" className={action === 'block' ? 'is-active' : ''} aria-pressed={action === 'block'} onClick={() => setAction('block')}>● I don't want these mods <span>{counts.block}</span></button>
        <button type="button" className={action === 'want' ? 'is-active' : ''} aria-pressed={action === 'want'} onClick={() => setAction('want')}>✦ I want these mods <span>{counts.want}</span></button>
      </div>
      <SelectedModsWindow blocked={selected.block} wanted={selected.want} />
      <div className="mod-picker__tools"><label className="sr-only" htmlFor="mod-search">Search modifiers</label><input id="mod-search" className="poe-input" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search for a modifier…" /><label className="mod-picker__selected"><input type="checkbox" checked={selectedOnly} onChange={event => setSelectedOnly(event.target.checked)} /> Selected only</label></div>
      <Filters mods={mods} />
      <div className="mod-picker__status"><span><strong>{visible.length}</strong> of {mods.length} modifiers</span><span>Click a row to {action === 'block' ? 'block or unblock' : 'want or remove'} it</span></div>
      <div className="mod-picker__list" role="list" aria-label={`${mapPool === 'nightmare' ? 'Nightmare' : 'Normal'} map modifiers`}>
        {visible.map(mod => <div role="listitem" key={mod.id}><ModRow mod={mod} action={action} /></div>)}
        {!visible.length && <div className="empty-mods"><strong>No modifiers match.</strong><p>Try a different search or clear the filters.</p></div>}
      </div>
    </div>
    <p className="scope-note">{mode === 'example' ? 'Example build ratings are illustrative. ' : ''}The catalogue has 78 <a href="https://poedb.tw/us/Maps_top_tier" target="_blank" rel="noreferrer">top tier normal</a> and 47 <a href="https://poedb.tw/us/Nightmare_map" target="_blank" rel="noreferrer">Nightmare</a> affix entries from PoEDB. Hover a row for its affix name, roll weight and reward lines. Build ratings cover a focused subset; check the rest yourself.</p>
  </section>;
}
