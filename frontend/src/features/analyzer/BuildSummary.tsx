import { Panel, SectionHeading } from '../../components/UI';
import type { AnalysisResult, BuildProfile } from '../../types';
import { BuildConfirmations } from './BuildConfirmations';

const number = (value: number) => Math.round(value).toLocaleString();
const present = (value: number | null | undefined): value is number => typeof value === 'number' && Number.isFinite(value) && value > 0;

function defenceRows(profile: BuildProfile): [string, string][] {
  const rows: [string, string][] = [];
  const layers = profile.defence_archetypes ?? [];
  const signals = new Set((profile.signals ?? []).map(signal => signal.id));
  if ((signals.has('armour') || layers.includes('Armour')) && present(profile.armour)) rows.push(['Armour', number(profile.armour)]);
  if ((signals.has('evasion') || layers.includes('Evasion')) && present(profile.evasion)) rows.push(['Evasion', number(profile.evasion)]);
  if (signals.has('block') || layers.some(layer => /block/i.test(layer))) {
    if (present(profile.effective_attack_block)) rows.push(['Attack block', `${profile.effective_attack_block.toFixed(1)}%`]);
    if (present(profile.effective_spell_block)) rows.push(['Spell block', `${profile.effective_spell_block.toFixed(1)}%`]);
  }
  if ((signals.has('suppression') || layers.includes('Spell suppression')) && present(profile.spell_suppression)) rows.push(['Spell suppression', `${profile.spell_suppression.toFixed(1)}%`]);
  if (profile.mana_defence_detected && present(profile.mana)) rows.push(['Mind over Matter · Mana', number(profile.mana)]);
  if (present(profile.ward)) rows.push(['Ward', number(profile.ward)]);
  for (const element of ['Fire', 'Cold', 'Lightning']) {
    const resistance = profile.elemental_resistances?.[element];
    if (resistance != null && Number.isFinite(resistance)) rows.push([`${element} resistance`, `${resistance}%`]);
  }
  if (profile.chaos_immune) rows.push(['Chaos damage', 'Immune']);
  else if (profile.chaos_resistance != null) rows.push(['Chaos resistance', `${profile.chaos_resistance}%`]);
  const pool = (profile.life ?? 0) <= 1 && (profile.energy_shield ?? 0) > 0 ? 'EnergyShield' : 'Life';
  for (const row of profile.recovery_channels ?? []) {
    if (row.pool === pool && ['regeneration', 'leech', 'recharge'].includes(row.channel) && present(row.value)) rows.push([`${pool === 'Life' ? 'Life' : 'ES'} ${row.channel}`, `${number(row.value)} /s`]);
  }
  if (present(profile.mana_regen)) rows.push(['Mana regeneration', `${number(profile.mana_regen)} /s`]);
  return rows;
}

export function BuildSummary({ analysis }: { analysis: AnalysisResult }) {
  const profile = analysis.profile;
  const known = (value: string) => value && !/unknown|unclear|not classified/i.test(value);
  const hits = Object.entries(profile.maximum_hit_taken ?? {}).filter(([kind, amount]) => present(amount) && !(kind === 'Chaos' && profile.chaos_immune));
  return <section id="build-profile" className="content-section">
    <SectionHeading number="05" title="The exile behind the regex" subtitle="The defensive layers found in your saved build." aside={<span className="edition-tag">{analysis.mode === 'example' ? 'EXAMPLE PROFILE' : 'SAVED POB PROFILE'}</span>} />
    <Panel className="defence-profile">
      <div className="defence-profile__identity"><div><p className="character-class">{[profile.class, profile.ascendancy].filter(known).join(' / ')} · Level {profile.level}</p>{known(profile.main_skill) && <h3>{profile.main_skill}</h3>}{known(profile.damage_type) && <p className="gem-line">{profile.damage_type === 'fire dot' ? 'Fire damage over time' : profile.damage_type}</p>}{profile.uses_totems && <p className="gem-line">{profile.attack_archetype}{profile.active_totem_limit ? ` · ${profile.active_totem_limit} totems` : ''}{profile.ancestral_bond ? ' · Ancestral Bond' : ''}</p>}</div><div className="defence-profile__pools">{present(profile.life) && profile.life > 1 && <div><span>Life</span><strong>{number(profile.life)}</strong></div>}{present(profile.energy_shield) && <div><span>Energy Shield</span><strong className="energy-value">{number(profile.energy_shield)}</strong></div>}</div></div>
      <div className="defence-profile__columns"><div><h4>Defensive layers</h4><dl className="defence-stats">{defenceRows(profile).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl><p className="profile-note">Recovery depends on its source: leech needs a target; recharge needs uptime.</p></div>{hits.length > 0 && <div><h4>Maximum hit taken</h4><p className="profile-note">Saved PoB estimates. Configuration, flasks and conditional effects may affect these values.</p><dl className="defence-stats">{hits.map(([kind, amount]) => <div key={kind}><dt>{kind}</dt><dd>{number(amount!)}</dd></div>)}{profile.chaos_immune && <div><dt>Chaos</dt><dd>Immune</dd></div>}</dl></div>}</div>
      {profile.assessment_summary && <details className="why-details"><summary>How recommendations were made <span aria-hidden="true">+</span></summary><p className="profile-note">Saved-build estimates, not a full PoB recalculation. Conservative exclusions protect usual play; policy allowances have not been verified for every build.</p><ul>{Object.entries(profile.assessment_summary.by_basis).filter(([,count]) => !!count).map(([basis,count]) => <li key={basis}>{({ snapshot_model: 'Calculated estimates', dependency_rule: 'Dependency rules', user_confirmation: 'Your confirmations', conservative_policy: 'Conservative exclusions', policy_allowance: 'Unverified policy allowances', unknown: 'Interactions needing review' } as Record<string,string>)[basis]}: {count}</li>)}</ul></details>}
      {!!profile.dependencies?.length && <details className="why-details"><summary>What makes this build work <span aria-hidden="true">+</span></summary><ul>{profile.dependencies.filter(row => ['delivery', 'scaling', 'activation'].includes(row.axis)).map(row => <li key={row.id}><strong>{row.label}</strong> · {row.evidence}</li>)}</ul></details>}
      {!!profile.coverage?.issues.length && <div className="dependency-notice" role="status"><strong>Some interactions need review</strong><ul>{profile.coverage.issues.map(issue => <li key={issue}>{issue}</li>)}</ul></div>}
      {!!profile.signals?.length && <details className="why-details"><summary>Evidence behind recommendations <span aria-hidden="true">+</span></summary><ul>{profile.signals.map(signal => <li key={signal.id}>{signal.evidence}</li>)}</ul></details>}
    </Panel>
    <BuildConfirmations analysis={analysis} />
  </section>;
}
