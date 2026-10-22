import { Sprite } from '../../components/Sprite';
import { useMemo } from 'react';
import { SectionHeading } from '../../components/UI';
import { buildRegex, recommendedDecision } from '../../services/regexBuilder';
import { useAppStore } from '../../store/useAppStore';
import type { ClassifiedMod, Preset } from '../../types';

const options: { id: Preset; title: string; description: string; caption: string }[] = [
  { id: 'safe', title: 'Maximum Filtering', description: 'Blocks major build risks plus detected charge and area-scaling dependencies and reviewed Nightmare exclusions. Marginal losses and unknowns are not blocked automatically.', caption: 'STRICTEST FILTERING' },
  { id: 'balanced', title: 'Balanced', description: 'Blocks bricks, substantial damage or recovery losses, and measured sustain conflicts. Unknowns need review.', caption: 'MIDDLE GROUND' },
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
  return <button type="button" className={`preset-card ${active ? 'preset-card--active' : ''}`} aria-pressed={active} onClick={() => setPreset(option.id)} title={option.description}><Sprite name={active ? 'presetActive' : 'preset'} />
    <div className="preset-card__top"><span className="panel-kicker">{option.caption}</span><span className="preset-selector" aria-hidden="true">{active ? '◆' : '◇'}</span></div>
    <span className="preset-card__title">{option.title}</span><span className="preset-card__description">{option.id === 'greedy' ? 'Only run-ending mods' : option.id === 'balanced' ? 'Threats + big disruption' : 'Detected build risks'}</span>
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
  const sameFiltering = mods.some(mod => !mod.manual) && mods.every(mod =>
    ((overrides[mod.id] ?? recommendedDecision(mod, 'balanced')) === 'block') ===
    ((overrides[mod.id] ?? recommendedDecision(mod, 'safe')) === 'block'));

  return <section id="presets" className="content-section">
    <SectionHeading number="02" title="Filtering Level" subtitle="Pick a starting point. Every mod can still be changed below." />
    <div className="preset-grid">{[...options].reverse().map(option => <PresetCard key={option.id} option={option} mods={mods} />)}</div>
    {sameFiltering && <p className="preset-equivalence">Balanced and Maximum Filtering block the same mods for this build with your current choices; Maximum only adds specifically flagged build risks, and manual choices apply to every preset.</p>}
    {overrideCount > 0 && <p className="preset-override-note">{overrideCount} manual choices are active in every preset. Use “Use preset” in the modifier database to clear them.</p>}
  </section>;
}
