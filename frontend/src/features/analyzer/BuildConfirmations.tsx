import { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import type { AnalysisResult, BuildAssumptions } from '../../types';

export function BuildConfirmations({ analysis }: { analysis: AnalysisResult }) {
  const [values, setValues] = useState<BuildAssumptions>(analysis.profile.assumptions ?? {});
  const refine = useAppStore(state => state.refineBuild);
  const loading = useAppStore(state => state.loading);
  const error = useAppStore(state => state.error);
  useEffect(() => setValues(analysis.profile.assumptions ?? {}), [analysis]);
  const rows = analysis.profile.recovery_channels?.filter(row => (row.value ?? 0) > 0 || row.source !== 'not saved') ?? [];
  const setBoolean = (key: 'recharge_sustainable' | 'hexproof_bypass' | 'flask_essential', value: string) => {
    setValues(previous => {
      const next = { ...previous };
      if (value === 'auto') delete next[key]; else next[key] = value === 'yes';
      return next;
    });
  };
  return <details className="build-confirmations">
    <summary>Check recovery and build dependencies <span aria-hidden="true">+</span></summary>
    <p>Missing values remain unknown. Leech needs a target, recoup needs incoming hits, recharge needs uptime, and flasks need charges. These sources are not automatically added together.</p>
    {rows.length > 0 && <div className="recovery-table-wrap"><table className="recovery-table"><thead><tr><th>Pool</th><th>Source</th><th>Saved amount</th><th>Availability</th></tr></thead><tbody>{rows.map(row => <tr key={`${row.pool}-${row.channel}`}><td>{row.pool === 'EnergyShield' ? 'ES' : row.pool}</td><td>{row.channel.replaceAll('_', ' ')}</td><td>{row.value == null ? 'Not measured' : `${Number(row.value.toFixed(1))} ${row.unit}`}</td><td>{row.condition}</td></tr>)}</tbody></table></div>}
    <p>Confirm only what applies to your usual setup. Confirmations affect recommendations; your manual modifier choices still take priority.</p>
    {analysis.profile.recovery_conflicts?.map((conflict, index) => <p key={index}>{conflict.reason}</p>)}
    <form onSubmit={event => { event.preventDefault(); void refine(values); }}>
      <div className="build-confirmations__fields">
        <label>Other reliable Mana recovery per second<input type="number" min="0" max="1000000" step="any" placeholder="Unknown" value={values.mana_alternative_per_second ?? ''} onChange={event => setValues({ ...values, mana_alternative_per_second: event.target.value === '' ? undefined : Number(event.target.value) })} /><small>Additional to saved regen and leech. Do not count the same source twice.</small></label>
        <label>Increased effect of map modifiers (%)<input type="number" min="0" max="300" step="any" value={values.map_effect_increased ?? 0} onChange={event => setValues({ ...values, map_effect_increased: Number(event.target.value) })} /><small>Applied to measured penalties using the worst roll in each pool.</small></label>
        <label>Recharge stays available during combat<select value={values.recharge_sustainable == null ? 'auto' : values.recharge_sustainable ? 'yes' : 'no'} onChange={event => setBoolean('recharge_sustainable', event.target.value)}><option value="auto">Unknown / use detected evidence</option><option value="yes">Yes, reliable during my usual combat</option><option value="no">No</option></select></label>
        <label>My Hexes bypass Hexproof<select value={values.hexproof_bypass == null ? 'auto' : values.hexproof_bypass ? 'yes' : 'no'} onChange={event => setBoolean('hexproof_bypass', event.target.value)}><option value="auto">Use detected evidence</option><option value="yes">Yes</option><option value="no">No</option></select></label>
        <label>What my curses provide<select value={values.curse_role ?? 'unknown'} onChange={event => setValues({ ...values, curse_role: event.target.value as BuildAssumptions['curse_role'] })}><option value="unknown">Contribution unknown</option><option value="utility">Utility / comfort</option><option value="damage">Important damage</option><option value="mechanic">A required core mechanic</option></select></label>
        <label>What my auras provide<select value={values.aura_role ?? 'unknown'} onChange={event => setValues({ ...values, aura_role: event.target.value as BuildAssumptions['aura_role'] })}><option value="unknown">Contribution unknown</option><option value="utility">Utility / comfort</option><option value="damage">Important damage</option><option value="defence">Important defence</option><option value="mechanic">A required core mechanic</option></select></label>
        <label>My usual setup requires flask uptime<select value={values.flask_essential == null ? 'auto' : values.flask_essential ? 'yes' : 'no'} onChange={event => setBoolean('flask_essential', event.target.value)}><option value="auto">Use detected evidence</option><option value="yes">Yes</option><option value="no">No, flasks are optional</option></select></label>
        <label>Charge sustain<select value={values.charge_sustain ?? 'unknown'} onChange={event => setValues({ ...values, charge_sustain: event.target.value as BuildAssumptions['charge_sustain'] })}><option value="unknown">Use detected evidence</option><option value="reliable">I quickly regain lost charges</option><option value="required">Losing charges disrupts my build</option></select></label>
      </div>
      {analysis.mode === 'example' && <p>Import a real build to apply confirmations.</p>}
      {error && <p role="alert">{error}</p>}
      <div className="build-confirmations__actions"><button type="submit" disabled={loading || analysis.mode !== 'live'}>{loading ? 'Updating…' : 'Apply confirmations'}</button><button type="button" disabled={loading || analysis.mode !== 'live'} onClick={() => { setValues({}); void refine({}); }}>Reset confirmations</button></div>
    </form>
  </details>;
}
