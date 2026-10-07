import { useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Sigil, Toast } from './components/UI';
import { BuildImport } from './features/analyzer/BuildImport';
import { BuildSummary } from './features/analyzer/BuildSummary';
import { ModAnalysis } from './features/mods/ModAnalysis';
import { Presets } from './features/presets/Presets';
import { Preferences } from './features/preferences/Preferences';
import { RegexOutput } from './features/output/RegexOutput';
import { useAppStore } from './store/useAppStore';

export default function App() {
  const analysis = useAppStore(state => state.analysis);
  const mapPool = useAppStore(state => state.mapPool);
  const showToast = useAppStore(state => state.showToast);
  const reducedMotion = useReducedMotion();
  const visibleMods = analysis?.mods.some(mod => mod.mapPool) ? analysis.mods.filter(mod => mod.mapPool === mapPool) : analysis?.mods ?? [];
  useEffect(() => {
    if (!analysis) return;
    const timer = window.setTimeout(() => document.getElementById('presets')?.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'start' }), 120);
    return () => window.clearTimeout(timer);
  }, [analysis, reducedMotion]);

  return <div className={`site-shell ${analysis ? 'site-shell--has-results' : ''}`} id="top">
    <div className="page-grain" aria-hidden="true" />
    <a className="skip-link" href="#generator">Skip to generator</a>
    <header className="site-header"><div className="site-header__inner page-wrap">
      <a className="brand" href="#top" aria-label="MapRegex home"><Sigil /><span>MAP<span>REGEX</span></span></a>
      <nav className="main-nav" aria-label="Main navigation"><a className="is-active" href="#generator">Generator</a><a href="#how-it-works">How it works</a><a href="#mods">Mod Database</a><a href="#about">About</a></nav>
      <div className="league-indicator"><span className="league-indicator__dot" /><span>POE 1</span><span className="league-indicator__divider">/</span><span>STANDARD</span></div>
    </div></header>
    <main className="page-wrap"><BuildImport />
      {analysis && <RegexOutput mods={visibleMods} limit={analysis.regexLimit} mode={analysis.mode} />}
      {analysis && <motion.div id="results" initial={reducedMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .28, ease: 'easeOut' }}>
        <Presets mods={visibleMods} />
        <ModAnalysis mods={visibleMods} mode={analysis.mode} />
        <Preferences />
        <BuildSummary analysis={analysis} />
      </motion.div>}
      <section id="how-it-works" className="how-section"><div className="how-section__header"><span className="panel-kicker">THE METHOD</span><h2>Read the build. <em>Roll with confidence.</em></h2></div><div className="how-steps"><div><span>01</span><h3>Import</h3><p>Paste a pobb.in link or your Path of Building export.</p></div><div><span>02</span><h3>Review</h3><p>See which map mods can break or strain this saved build.</p></div><div><span>03</span><h3>Copy</h3><p>Choose a preset, refine decisions, then copy the search string.</p></div></div></section>
    </main>
    <footer id="about" className="site-footer"><div className="page-wrap site-footer__inner"><div><div className="footer-brand"><Sigil /><span>MAPREGEX</span></div><p>This is a fan-made tool and is not affiliated with or endorsed by Grinding Gear Games.</p></div><div className="footer-links"><button type="button" onClick={() => showToast('GitHub page coming later.')}>GitHub</button><button type="button" onClick={() => showToast('Discord community coming later.')}>Discord</button><button type="button" onClick={() => showToast('Changelog coming later.')}>Changelog</button></div></div></footer>
    <Toast />
  </div>;
}
