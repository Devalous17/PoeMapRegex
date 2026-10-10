import { useEffect, useRef, useState } from 'react';
import { Button, Panel, SectionHeading, Sigil } from './UI';
import { DiamondPager } from './Ornaments';

const steps = [
  { target: 'generator', title: 'Bring your build', text: 'Paste a pobb.in link or export code. In Path of Building, open Import/Export Build, then Generate and Copy. No account is needed.' },
  { target: 'mods', title: 'Make the call', text: 'Recommendations are a starting point. Click a modifier to block or allow it. Open the explanations to see what was detected in your build.' },
  { target: 'preferences', title: 'Choose your rewards', text: 'Set the minimum quantity, pack size or other map values you want. The search updates immediately. Quantity starts at 40%; you can change or clear it.' },
  { target: 'output', title: 'Copy, then map', text: 'Copy the search into your in-game stash search. Matching maps pass your selected filters. Missing build data still needs your judgment.' },
];

export function Tour({ open, onClose }: { open: boolean; onClose: () => void }) {
  const previousFocus = useRef<HTMLElement | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const [step, setStep] = useState(0);
  const [spot, setSpot] = useState({ top: 0, left: 0, width: 0, height: 0 });
  useEffect(() => {
    if (!open) { dialog.current?.close(); return; }
    previousFocus.current = document.activeElement as HTMLElement;
    setStep(0); dialog.current?.showModal();
    return () => { dialog.current?.close(); previousFocus.current?.focus(); };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const target = document.getElementById(steps[step].target);
    target?.scrollIntoView({ behavior: 'instant', block: 'start' });
    let frame = 0;
    const measure = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => { if (target) { const r = target.getBoundingClientRect(); setSpot({ top: Math.max(8, r.top), left: Math.max(8, r.left), width: Math.min(r.width, innerWidth - 16), height: Math.min(r.height, innerHeight - 24) }); } });
    };
    measure(); window.addEventListener('resize', measure); window.addEventListener('scroll', measure, { passive: true });
    return () => { cancelAnimationFrame(frame); window.removeEventListener('resize', measure); window.removeEventListener('scroll', measure); };
  }, [open, step]);
  function finish() { try { localStorage.setItem('mapregex-tour-v1', 'done'); } catch { /* Tour remains usable when storage is unavailable. */ } onClose(); }
  return <dialog ref={dialog} className="tour-dialog" aria-labelledby="tour-title" aria-describedby="tour-description" onCancel={finish}>
    <div className="tour-spotlight" style={spot} aria-hidden="true" />
    <div className="tour-card"><Sigil /><p className="panel-kicker">A QUICK GUIDE · {step + 1} OF {steps.length}</p><h2 id="tour-title">{steps[step].title}</h2><p id="tour-description">{steps[step].text}</p>
      <DiamondPager count={steps.length} current={step} onSelect={setStep}/>
      <div className="tour-actions"><button type="button" className="text-link" onClick={finish}>Skip tour</button>{step > 0 && <Button type="button" onClick={() => setStep(step - 1)}>Back</Button>}<Button autoFocus type="button" variant="primary" onClick={() => step === steps.length - 1 ? finish() : setStep(step + 1)}>{step === steps.length - 1 ? 'Start mapping' : 'Next'} <span aria-hidden="true">›</span></Button></div>
    </div>
  </dialog>;
}

export function HowToUse({ onTour }: { onTour: () => void }) {
  return <section id="how-it-works" className="content-section how-section">
    <SectionHeading number="01" title="Your next map, in three steps" subtitle="Your build. Your choices. One search string."/>
    <div className="how-steps">{[
      ['01', 'Export your build', 'In Path of Building: Import/Export Build → Generate → Copy. A pobb.in link works too.'],
      ['02', 'Choose what to avoid', 'Import your build, choose a preset, then review the modifiers. Every choice is editable.'],
      ['03', 'Copy into your stash', 'Paste your regex into the in-game stash search. Maps matching your filters will light up.'],
    ].map(([n,title,text]) => <Panel key={n}><span className="step-seal">{n}</span><h3>{title}</h3><p>{text}</p></Panel>)}</div>
    <button type="button" className="text-link guide-replay" onClick={onTour}>Show me around <span aria-hidden="true">›</span></button>
  </section>;
}

export function FAQ() {
  return <section id="faq" className="content-section faq-section"><SectionHeading number="06" title="Before you enter the map" subtitle="A few things worth knowing."/><div className="faq-grid">{[
    ['What is a regex?', 'Here, it is a short search string for Path of Exile 1. It tells the stash which map modifiers to exclude and which values to match. You do not need to learn the syntax—choose your filters and copy.'],
    ['Does this guarantee a safe map?', 'No. Recommendations use the stats and mechanics saved in your PoB. Conditional defences, flask uptime and unusual interactions may be missing. Review the reasons and adjust the selections for your character.'],
    ['Which preset should I use?', 'Greedy blocks mods rated build-breaking. Balanced also blocks substantial damage, defence and sustain risks. Maximum Filtering adds specific dependencies and reviewed Nightmare exclusions. Marginal penalties are not automatically blocked.'],
    ['Where does my build go?', 'Your link or export is sent to the MapRegex Python analyzer. For a pobb.in link, the server downloads the export from pobb.in. The app does not save your submitted build to a database; your current results live in browser memory. Your hosting provider may retain request logs. Only the tour dismissal is saved locally.'],
    ['Why are some modifiers marked “Needs review”?', 'The saved build does not provide enough information for a conclusion. These modifiers are not automatically blocked or declared Free. Check them yourself or confirm the relevant dependencies in the build section.'],
    ['Does this support Path of Exile 2?', 'MapRegex currently supports English Path of Exile 1 map modifiers. This visual design takes inspiration from dark fantasy, but the game data and search syntax are for PoE 1.'],
  ].map(([q,a]) => <details key={q} className="faq-entry"><summary>{q}<span aria-hidden="true">+</span></summary><p>{a}</p></details>)}</div></section>;
}
