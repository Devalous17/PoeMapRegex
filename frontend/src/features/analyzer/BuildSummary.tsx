import { OrnamentDivider, Panel, PoeTooltip, SectionHeading, Sigil } from '../../components/UI';
import type { AnalysisResult, BuildProfile } from '../../types';

function value(number: number | null | undefined): string {
  return typeof number === 'number' && Number.isFinite(number) ? Math.round(number).toLocaleString() : 'Not saved';
}

function statRows(profile: BuildProfile): [string, string, string][] {
  const pools = profile.energy_shield && profile.life && profile.energy_shield > profile.life * 2 ? 'Energy Shield' : profile.life && profile.energy_shield && profile.energy_shield > profile.life / 2 ? 'Hybrid' : 'Life';
  const leech = [profile.life_leech > 0 && 'Life', profile.mana_leech > 0 && 'Mana', profile.energy_shield_leech > 0 && 'ES'].filter(Boolean).join(' + ') || 'None saved';
  const regen = profile.life_regen + profile.mana_regen + profile.energy_shield_regen > 0 ? 'Regeneration' : 'None saved';
  const res = ['Fire', 'Cold', 'Lightning'].map(key => profile.elemental_resistances?.[key] == null ? '—' : String(profile.elemental_resistances[key])).join(' / ');
  return [
    ['Primary pool', pools, `Life ${value(profile.life)} · Energy Shield ${value(profile.energy_shield)}. These are saved PoB snapshot values.`],
    ['Cooldown loop', profile.uses_cast_on_crit ? 'Cast on Crit' : profile.automated_mine_detonation ? 'Automated mines' : profile.uses_mines ? 'Mines' : 'Not detected', 'Read from enabled gems in the active PoB skill set. Reduced cooldown recovery can interrupt repeated triggers or mine detonation.'],
    ['Elemental res', res, 'Fire / Cold / Lightning Resistance from the saved PoB snapshot. Maximum resistance is not available here.'],
    ['Armour / Evasion', `${value(profile.armour)} / ${value(profile.evasion)}`, 'These layers are only shown when the imported data contains them.'],
    ['Block', profile.block == null ? 'Not saved' : `${profile.block}%`, 'Block chance is not included in the first live importer.'],
    ['Leech', leech, 'Leech is a key signal when judging Cannot Leech map mods.'],
    ['Recovery', regen, 'Regeneration and leech may be weakened by recovery modifiers.'],
    ['Ailments', profile.ailment_avoidance || 'Needs review', 'Ailment avoidance is not derived by the first live importer.'],
    ['Minions', profile.has_minion_skills ? 'Present' : 'None detected', 'Minion skills can interact with reflect even when the main skill does not.'],
    ['Charges', profile.charges || 'Needs review', 'Charge reliance is not derived by the first live importer.'],
  ];
}

function Signal({ title, value, width, tone }: { title: string; value: string; width: number; tone: string }) {
  return <div className="signal-row"><div className="signal-row__top"><span>{title}</span><strong>{value}</strong></div><div className="signal-track"><span className={`signal-fill signal-fill--${tone}`} style={{ width: `${Math.max(4, Math.min(width, 100))}%` }} /></div></div>;
}

export function BuildSummary({ analysis }: { analysis: AnalysisResult }) {
  const profile = analysis.profile;
  const defenceTotal = (profile.life || 0) + (profile.energy_shield || 0);
  const esShare = defenceTotal ? Math.round((profile.energy_shield || 0) / defenceTotal * 100) : 0;
  const leechValue = profile.life_leech + profile.mana_leech + profile.energy_shield_leech;
  return <section id="build-profile" className="content-section">
    <SectionHeading number="05" title="The exile behind the regex" subtitle="The saved build snapshot tells us what is dangerous for this character." aside={<span className="edition-tag">{analysis.mode === 'example' ? 'EXAMPLE PROFILE' : 'LIVE POB PROFILE'}</span>} />
    <Panel className="build-panel">
      <div className="character-plate">
        <div className="character-plate__top"><span className="panel-kicker">CHARACTER PROFILE</span><span className="level-badge">LVL {profile.level}</span></div>
        <div className="character-identity"><div className="character-seal"><Sigil /></div><div><p className="character-class">{profile.class} / {profile.ascendancy}</p><h3>{profile.main_skill}</h3><span className="gem-line">MAIN SKILL · {profile.damage_type.toUpperCase()}</span></div></div>
        <OrnamentDivider />
        <div className="character-pools"><div><span>ENERGY SHIELD</span><strong className="energy-value">{value(profile.energy_shield)}</strong></div><div><span>LIFE</span><strong>{value(profile.life)}</strong></div><div><span>CHAOS RES</span><strong className={(profile.chaos_resistance ?? 0) < 0 ? 'danger-value' : ''}>{profile.chaos_resistance == null ? '—' : `${profile.chaos_resistance}%`}</strong></div></div>
        <div className="stat-chip-grid">{statRows(profile).map(([label, detail, explanation]) => <PoeTooltip key={label} title={label} body={explanation} className="stat-chip"><span>{label}</span><strong>{detail}</strong></PoeTooltip>)}</div>
      </div>
      <div className="build-signals">
        <div className="build-signals__heading"><span className="panel-kicker">BUILD PROFILE</span><h3>Combat signals</h3><p>A quick reading of the saved PoB values, not a full simulation.</p></div>
        <Signal title="Damage focus" value={profile.damage_type === 'unknown' ? 'Needs review' : profile.damage_type} width={profile.damage_type === 'unknown' ? 24 : 86} tone={profile.damage_type.includes('chaos') ? 'chaos' : profile.damage_type.includes('physical') ? 'physical' : 'cold'} />
        <Signal title="Defence pool" value={esShare > 70 ? 'Energy Shield' : esShare > 30 ? 'Hybrid' : 'Life'} width={Math.max(esShare, 18)} tone="energy" />
        <Signal title="Recovery reliance" value={leechValue > 0 ? 'Leech present' : 'No leech saved'} width={leechValue > 0 ? 82 : 18} tone="green" />
        <Signal title="Reflect risk" value={profile.reflect_protection_detected ? 'Protection mentioned' : 'Review needed'} width={profile.reflect_protection_detected ? 38 : 78} tone="break" />
        <div className="build-flags"><span>{profile.uses_auras ? 'AURAS ACTIVE' : 'NO AURAS DETECTED'}</span><span>{profile.uses_hexes ? 'HEXES ACTIVE' : 'NO HEXES DETECTED'}</span><span>{profile.has_minion_skills ? 'MINIONS PRESENT' : 'NO MINIONS DETECTED'}</span></div>
        <details className="why-details"><summary>Why this matters <span aria-hidden="true">+</span></summary><p>Map mods can remove recovery, lower defences, or reflect your damage. This profile guides the initial ratings, but conditional effects and secondary skills still need your review.</p></details>
      </div>
    </Panel>
  </section>;
}
