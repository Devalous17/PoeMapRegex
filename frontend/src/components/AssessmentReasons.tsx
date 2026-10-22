import { ModText } from './ModText';
import { assessmentSummary } from './assessmentText';
import { Sprite } from './Sprite';
import { useAppStore } from '../store/useAppStore';
import { recommendedDecision } from '../services/regexBuilder';
import type { ClassifiedMod } from '../types';
export function AssessmentReasons({mods}:{mods:ClassifiedMod[]}) {
  const {analysis,preset,overrides}=useAppStore();
  const ranked=mods.filter(m=>!m.manual).slice().sort((a,b)=>Number((overrides[b.id]??recommendedDecision(b,preset))==='block')-Number((overrides[a.id]??recommendedDecision(a,preset))==='block'));
  return <section className="assessment-reasons"><h2>Assessment Reasons</h2><div className="assessment-panel"><Sprite name="assessment" />{!analysis ? <p>Import a build to see why modifiers are recommended for this character.</p> : ranked.map(mod=>{const decision=overrides[mod.id]??recommendedDecision(mod,preset);const skin=decision==='block'?'block':mod.rating==='free'?'allow':'warn';return <article key={mod.id} className="assessment-row"><Sprite name="reasonRow" /><span className="assessment-badge"><Sprite name={skin} />{skin==='block'?'BLOCK':skin==='allow'?'ALLOW':'REVIEW'}</span><div><strong><ModText text={mod.name} /></strong><p title={mod.reason}>{assessmentSummary(mod.reason)}</p></div></article>;})}</div></section>;
}
