import { useMemo } from 'react';
import { SectionHeading, Sigil } from '../../components/UI';
import { buildRegex } from '../../services/regexBuilder';
import { useAppStore } from '../../store/useAppStore';
import type { ClassifiedMod, Preset } from '../../types';

const options: { id: Preset; title: string; description: string; caption: string }[] = [
  { id: 'safe', title: 'Safe', description: 'Blocks troublesome mods, measured recovery conflicts, and unknowns. Most cautious filtering.', caption: 'MAXIMUM CAUTION' },
  { id: 'balanced', title: 'Balanced', description: 'Blocks serious risks and measured recovery conflicts. Unknowns need review.', caption: 'MIDDLE GROUND' },
  { id: 'greedy', title: 'Greedy', description: 'Blocks only mods currently rated Brick.', caption: 'MINIMUM FILTERING' },
];

function PresetCard({ option, mods }: { option: typeof options[number]; mods: ClassifiedMod[] }) {
  const active = useAppStore(state => state.preset === option.id);
  const setPreset = useAppStore(state => state.setPreset);
  const overrides = useAppStore(state => state.overrides);
  const preferences = useAppStore(state => state.preferences);
  const result = useMemo(() => buildRegex(mods, option.id, overrides, preferences), [mods, option.id, overrides, preferences]);
  const distribution = [
    ['brick', result.blocked.filter(mod => mod.rating === 'brick').length],
    ['dangerous', result.blocked.filter(mod => mod.rating === 'dangerous').length],
    ['uncomfortable', result.blocked.filter(mod => mod.rating === 'uncomfortable').length],
  ] as const;
  return <button type="button" className={`preset-card ${active ? 'preset-card--active' : ''}`} aria-pressed={active} onClick={() => setPreset(option.id)}>
    <Sigil className="preset-watermark" />
    <div className="preset-card__top"><span className="panel-kicker">{option.caption}</span><span className="preset-selector" aria-hidden="true">{active ? '◆' : '◇'}</span></div>
    <span className="preset-card__title">{option.title}</span><span className="preset-card__description">{option.description}</span>
    <div className="preset-card__bottom"><span><strong>{result.blocked.length}</strong> mods blocked</span><span>{result.length} chars</span></div>
    <div className="distribution-bar" aria-label={`${result.blocked.length} blocked modifiers`}>
      {distribution.map(([rating, count]) => count > 0 && <span key={rating} className={`distribution-bar__${rating}`} style={{ flex: count }} />)}
      {!result.blocked.length && <span className="distribution-bar__empty" />}
    </div>
  </button>;
}

export function Presets({ mods }: { mods: ClassifiedMod[] }) {
  const overrides = useAppStore(state => state.overrides);
  const overrideCount = mods.filter(mod => overrides[mod.id] !== undefined).length;
  return <section id="presets" className="content-section">
    <SectionHeading number="02" title="Choose your comfort level" subtitle="Pick a starting point. Every mod can still be changed below." />
    <div className="preset-grid">{options.map(option => <PresetCard key={option.id} option={option} mods={mods} />)}</div>
    {overrideCount > 0 && <p className="preset-override-note">{overrideCount} manual choices are active in every preset. Use “Use preset” in the modifier database to clear them.</p>}
  </section>;
}
