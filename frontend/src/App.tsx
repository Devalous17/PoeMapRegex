import { useEffect, useState } from 'react';
import { useReducedMotion } from 'framer-motion';
import { Sigil, Toast } from './components/UI';
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
  const showToast = useAppStore(state => state.showToast);
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
      for (const [id] of [['generator'], ['mods'], ['how-it-works'], ['about']]) {
        const element = document.getElementById(id);
        if (element && element.getBoundingClientRect().top <= window.innerHeight * .35) section = id;
      }
      setActive(section);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  return <div className="site-shell site-shell--has-results" id="top">
    <div className="page-grain" aria-hidden="true" />
    <a className="skip-link" href="#generator">Skip to generator</a>
    <header className="site-header"><div className="site-header__inner page-wrap">
      <a className="brand" href="#top" aria-label="MapRegex home"><Sigil /><span>MAP<span>REGEX</span></span></a>
      <nav className="main-nav" aria-label="Main navigation">{navigation.map(([id, label]) => <a key={id} href={`#${id}`} className={active === id ? 'is-active' : ''} aria-current={active === id ? 'location' : undefined} onClick={event => { event.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'start' }); history.replaceState(null, '', `#${id}`); setActive(id); }}>{label}</a>)}</nav>
      <div className="league-indicator"><span className="league-indicator__dot" /><span>POE 1</span><span className="league-indicator__divider">/</span><span>STANDARD</span></div>
    </div></header>
    <main className="page-wrap"><BuildImport />
      <RegexOutput mods={visibleMods} limit={analysis?.regexLimit ?? 250} mode={analysis?.mode ?? 'manual'} />
      <div id="results">
        {analysis && <Presets mods={visibleMods} />}
        <ModAnalysis mods={visibleMods} mode={analysis?.mode ?? 'manual'} />
        <Preferences />
        {analysis && <BuildSummary analysis={analysis} />}
      </div>
      <section id="how-it-works" className="how-section"><div className="how-section__header"><span className="panel-kicker">THE METHOD</span><h2>Read the build. <em>Review the map.</em></h2></div><div className="how-steps"><div><span>01</span><h3>Import</h3><p>Paste a pobb.in link or your Path of Building export.</p></div><div><span>02</span><h3>Review</h3><p>See which map mods can break or strain this saved build.</p></div><div><span>03</span><h3>Copy</h3><p>Choose a preset, refine decisions, then copy the search string.</p></div></div></section>
    </main>
    <footer id="about" className="site-footer"><div className="page-wrap site-footer__inner"><div><div className="footer-brand"><Sigil /><span>MAPREGEX</span></div><p>This is a fan-made tool and is not affiliated with or endorsed by Grinding Gear Games.</p></div><div className="footer-links"><a href="https://github.com/Devalous17/PoeMapRegex" target="_blank" rel="noreferrer">GitHub</a><button type="button" onClick={() => showToast('Discord community coming later.')}>Discord</button><button type="button" onClick={() => showToast('Changelog coming later.')}>Changelog</button></div></div></footer>
    <Toast />
  </div>;
}
