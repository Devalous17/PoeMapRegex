import { LandingPage } from './components/LandingPage';
import { Sprite } from './components/Sprite';
import { AssessmentReasons } from './components/AssessmentReasons';
import { useEffect, useState } from 'react';
import { Button, Toast } from './components/UI';
import { Icon } from './components/Icon';
import { FAQ, HowToUse, Tour } from './components/Guide';
import { HighlightProvider } from './components/HighlightContext';
import { BuildImport } from './features/analyzer/BuildImport';
import { BuildSummary } from './features/analyzer/BuildSummary';
import { ModAnalysis, SelectionPanel } from './features/mods/ModAnalysis';
import { Presets } from './features/presets/Presets';
import { Preferences } from './features/preferences/Preferences';
import { RegexOutput } from './features/output/RegexOutput';
import { BuildStatus, Vulnerabilities, MapSearch } from './components/Workbench';
import { useAppStore } from './store/useAppStore';
import { mapCatalogue } from './data/mapCatalogue';
import type { ClassifiedMod } from './types';

const manualMods: ClassifiedMod[] = mapCatalogue.map(mod => ({ ...mod, manual: true, rating: 'review', reason: 'Not assessed. Import a build for personalised recommendations.' }));

export default function App() {
  const analysis = useAppStore(state => state.analysis);
  const mapPool = useAppStore(state => state.mapPool);
  const [tour, setTour] = useState(false);
  const [action, setAction] = useState<'block' | 'want'>('block');
  const mods = (analysis?.mods ?? manualMods).filter(mod => !mod.mapPool || mod.mapPool === mapPool);
  useEffect(() => {
    if (!analysis) return;
    try { if (localStorage.getItem('mapregex-tour-v1')) return; } catch { return; }
    const timer = window.setTimeout(() => setTour(true), 1600);
    return () => clearTimeout(timer);
  }, [analysis]);
  function importFocus() {
    document.getElementById('generator')?.scrollIntoView({ block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
    document.getElementById('open-build-import')?.click();
  }
  return <HighlightProvider><div className={`site-shell tool-shell figma-theme ${analysis ? '' : 'is-landing'}`} id="top">
    <a className="skip-link" href="#generator">Skip to build analyzer</a>
    <header className="tool-header"><div className="tool-header__inner">
      <a href="#top" className="tool-logo" aria-label="MapRegex home"><Sprite name="logo" />Map Regex</a>
      <nav aria-label="Main navigation"><a className="is-active" href="#generator">Build Analyzer</a>{analysis ? <><a href="#preferences">Preferences</a><a href="#mod-database">Mod Database</a></> : <a href="#how-it-works">How to use</a>}</nav>
      <div className="tool-header__actions"><Button className="header-import" onClick={importFocus}>PoB Import</Button><span className="game-indicator">{!analysis && <Sprite name="toggle"/>}PoE 1</span><button type="button" className="icon-button" aria-label="Open quick guide" onClick={() => analysis ? setTour(true) : document.getElementById('how-it-works')?.scrollIntoView({behavior:'smooth'})}>{analysis ? <Icon name="help" /> : <Sprite name="document"/>}</button><span className="language-indicator" title="English map modifiers" aria-label="English map modifiers">{!analysis && <Sprite name="toggleDark"/>}EN</span></div>
    </div><div className="header-divider"><Sprite name="divider" /></div></header>
    <main className={`tool-main page-wrap ${analysis ? 'has-build' : 'landing-main'}`}>
      {!analysis ? <LandingPage /> : <div className="figma-layout">
        <div className="figma-workspace">
          <BuildImport />
          <MapSearch />
          <Presets mods={mods} />
          <section id="mods" className="selection-section"><h2>Currently blocked / wanted mods</h2><div className="tool-panel selection-panel"><Sprite name="selection" /><SelectionPanel mods={mods} action={action} setAction={setAction} mode={analysis?.mode ?? 'manual'} /></div></section>
          <ModAnalysis mods={mods} mode={analysis?.mode ?? 'manual'} action={action} setAction={setAction} />
          <Preferences />
          {analysis && <BuildSummary analysis={analysis} />}
          <details className="tool-help"><summary>How MapRegex works</summary><HowToUse onTour={() => setTour(true)} /></details><FAQ />
        </div>
        <aside className="figma-sidebar">
          <RegexOutput mods={mods} limit={analysis?.regexLimit ?? 250} mode={analysis?.mode ?? 'manual'} />
          <BuildStatus mods={mods} />
          <AssessmentReasons mods={mods} />
          <details className="sidebar-vulnerabilities"><summary>Tag Filter / Vulnerabilities</summary><Vulnerabilities mods={mods} /></details>
        </aside>
      </div>}
    </main>
    <footer id="about" className="site-footer"><div className="page-wrap site-footer__inner"><div><strong>MapRegex</strong><p>Fan-made tool. Not affiliated with or endorsed by Grinding Gear Games.</p></div><div className="footer-links"><a href="https://github.com/Devalous17/PoeMapRegex" target="_blank" rel="noreferrer">GitHub</a><button type="button" onClick={() => analysis ? setTour(true) : document.getElementById('how-it-works')?.scrollIntoView({behavior:'smooth'})}>Quick guide</button><a href="/credits.html">Credits & fonts</a><a href="#faq">Questions & privacy</a></div></div></footer>
    <Tour open={tour} onClose={() => setTour(false)} /><Toast />
  </div></HighlightProvider>;
}
