import { useEffect, useState } from 'react';
import { useReducedMotion } from 'framer-motion';
import { Button, Toast } from './components/UI';
import { Reveal } from './components/Ornaments';
import { FAQ, HowToUse, Tour } from './components/Guide';
import { HighlightProvider } from './components/HighlightContext';
import { BuildImport } from './features/analyzer/BuildImport';
import { BuildSummary } from './features/analyzer/BuildSummary';
import { ModAnalysis } from './features/mods/ModAnalysis';
import { Presets } from './features/presets/Presets';
import { Preferences } from './features/preferences/Preferences';
import { RegexOutput } from './features/output/RegexOutput';
import { useAppStore } from './store/useAppStore';
import { mapCatalogue } from './data/mapCatalogue';
import type { ClassifiedMod } from './types';

const manualMods: ClassifiedMod[] = mapCatalogue.map(mod => ({ ...mod, manual: true, rating: 'review', reason: 'Not assessed. Import a build for personalised recommendations.' }));
const navigation = [['generator', 'Generator'], ['how-it-works', 'How it works'], ['mods', 'Mod Database'], ['about', 'About']];

export default function App() {
  const analysis = useAppStore(state => state.analysis);
  const source = useAppStore(state => state.analysisSource);
  const mapPool = useAppStore(state => state.mapPool);
  const [tour, setTour] = useState(false);
  const [menu, setMenu] = useState(false);
  const reducedMotion = useReducedMotion();
  const [active, setActive] = useState('generator');
  const visibleMods = (analysis?.mods ?? manualMods).filter(mod => !mod.mapPool || mod.mapPool === mapPool);
  const importKey = analysis ? source : '';
  useEffect(() => {
    const dock = document.getElementById('output');
    if (!dock) return;
    const observer = new ResizeObserver(() => document.documentElement.style.setProperty('--regex-scroll-offset', `${dock.offsetHeight + 24}px`));
    observer.observe(dock);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!importKey) return;
    document.getElementById('presets')?.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'start' });
  }, [importKey, reducedMotion]);
  useEffect(() => {
    const onScroll = () => {
      let section = 'generator';
      for (const [id] of [['how-it-works'], ['generator'], ['mods'], ['about']]) {
        const element = document.getElementById(id);
        if (element && element.getBoundingClientRect().top <= window.innerHeight * .35) section = id;
      }
      setActive(section);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  useEffect(() => {
    try { if (localStorage.getItem('mapregex-tour-v1')) return; } catch { return; }
    const timer = window.setTimeout(() => setTour(true), 1600); return () => clearTimeout(timer);
  }, []);
  return <HighlightProvider><div className="site-shell site-shell--has-results" id="top">

    <div className="utility-bar page-wrap"><button type="button" className="utility-tour" onClick={() => setTour(true)}>Quick guide ›</button><span>PATH OF EXILE 1 · ENGLISH MAP SEARCH</span><a href="https://github.com/Devalous17/PoeMapRegex" target="_blank" rel="noreferrer">Community project ↗</a></div>
    <a className="skip-link" href="#generator">Skip to generator</a>
    <header className="site-header"><div className="site-header__inner page-wrap">
      <a className="brand" href="#top" aria-label="MapRegex home"><span>MAP<span>REGEX</span></span><small>THE CARTOGRAPHER'S COMPANION</small></a>
      <button type="button" className="mobile-menu poe-button" aria-expanded={menu} aria-controls="main-navigation" onClick={() => setMenu(!menu)}>Menu {menu ? "−" : "+"}</button><nav id="main-navigation" className={`main-nav ${menu ? "is-open" : ""}`} aria-label="Main navigation">{navigation.map(([id, label]) => <a key={id} href={`#${id}`} className={active === id ? 'is-active' : ''} aria-current={active === id ? 'location' : undefined} onClick={event => { event.preventDefault(); setMenu(false); document.getElementById(id)?.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'start' }); history.replaceState(null, '', `#${id}`); setActive(id); }}>{label}</a>)}</nav>
      <div className="league-indicator"><span className="league-indicator__dot" /><span>POE 1</span><span className="league-indicator__divider">/</span><span>STANDARD</span></div>
    </div></header>
    <main className="page-wrap">
      <section className="atlas-hero" aria-labelledby="hero-title"><div className="hero-copy"><p className="eyebrow">READ YOUR BUILD. CHART YOUR ATLAS.</p><h1 id="hero-title">Know Your <em>Maps.</em></h1><p>Turn your Path of Building into a map search that avoids the modifiers that could break your character.</p><Button variant="primary" onClick={() => document.getElementById('generator')?.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth' })}>Import your build <span aria-hidden="true">›</span></Button><a className="text-link" href="#how-it-works">New here? See how it works</a><div className="hero-plates">{[['generator','01','Import'],['mods','02','Review'],['output','03','Copy']].map(([id,n,label]) => <button key={id} type="button" onClick={() => document.getElementById(id)?.scrollIntoView({behavior: reducedMotion ? 'instant' : 'smooth'})}>{n} <b>{label}</b></button>)}</div><p className="hero-note">Free to use · No account needed · A baseline, never a guarantee</p></div></section>
      <Reveal><HowToUse onTour={() => setTour(true)} /></Reveal><Reveal><BuildImport /></Reveal>
      <RegexOutput mods={visibleMods} limit={analysis?.regexLimit ?? 250} mode={analysis?.mode ?? 'manual'} />
      <div id="results">
        {analysis && <Presets mods={visibleMods} />}
        <ModAnalysis mods={visibleMods} mode={analysis?.mode ?? 'manual'} />
        <Preferences />
        {analysis && <BuildSummary analysis={analysis} />}
      </div>
      <Reveal><FAQ /></Reveal>
    </main>
    <footer id="about" className="site-footer"><div className="page-wrap site-footer__inner"><div><div className="footer-brand"><span>MAPREGEX</span></div><p>This is a fan-made tool and is not affiliated with or endorsed by Grinding Gear Games.</p></div><div className="footer-links"><a href="https://github.com/Devalous17/PoeMapRegex" target="_blank" rel="noreferrer">GitHub</a><button type="button" onClick={() => setTour(true)}>Replay guide</button><a href="#faq">Questions & privacy</a></div></div></footer>
    <Tour open={tour} onClose={() => setTour(false)} /><Toast />
  </div></HighlightProvider>;
}
