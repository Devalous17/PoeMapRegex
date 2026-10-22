import { BuildImport } from '../features/analyzer/BuildImport';
import { LandingSprite, type LandingSkin } from './LandingSprite';
import { mapCatalogue } from '../data/mapCatalogue';
import { buildRegex } from '../services/regexBuilder';
import { useAppStore } from '../store/useAppStore';
import { EMPTY_PREFERENCES } from '../types';
import exampleExport from '../../../fixtures/test-build.pob.txt?raw';

const sampleMods = mapCatalogue.filter(mod => mod.mapPool === 'normal').map(mod => ({...mod, manual:false, rating: /physical thorns|cannot regenerate/i.test(mod.name) ? 'brick' as const : 'free' as const}));
const sample = buildRegex(sampleMods, 'greedy', {}, EMPTY_PREFERENCES);
const features: {icon:LandingSkin; title:string; text:string}[] = [
  {icon:'success',title:'Reads your whole build',text:'Skills, items, stats, offence, defence layers and recovery sources are checked against Normal and Nightmare map mods.'},
  {icon:'warning',title:'Blocks what actually hurts',text:'Mods that disable your build or threaten survival get flagged. Minor penalties stay allowed unless your build depends on that mechanic.'},
  {icon:'document',title:'Greedy, Balanced or Maximum',text:'Pick how aggressive the filter is, then block or allow any modifier by hand. Quantity, pack size and other preferences are included.'},
  {icon:'copyIcon',title:'One string for your stash',text:'The regex updates as you change anything. Copy it straight into the in-game stash search.'},
];
export function LandingPage() {
 const {setSource,analyze,loading,showToast}=useAppStore();
 function focusImport(){document.getElementById('generator')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});document.getElementById('build-source')?.focus();}
 function example(){setSource(exampleExport.trim());void analyze();}
 async function copyExample(){try{await navigator.clipboard.writeText(sample.regex);showToast('Example regex copied. Import your build for your own recommendations.');}catch{showToast('Select the example text and copy it manually.');}}
 return <div className="landing-page">
  <img className="landing-glow" src="/assets/figma/hero-glow.svg" width="900" height="760" alt=""/>
  <section className="landing-hero" aria-labelledby="landing-title">
   <div className="landing-pitch"><span className="landing-eyebrow"><LandingSprite name="eyebrow"/>Free · Path of Exile 1</span><h1 id="landing-title">Know your<br/><em>maps</em></h1><p className="landing-intro">Paste your Path of Building link. MapRegex reads your build, flags the map modifiers that could ruin it, and turns the result into one search string for your stash.</p><BuildImport/><ul className="landing-benefits"><li>Free to use</li><li>pobb.in or PoB code</li><li>Copy into stash search</li></ul></div>
   <aside className="landing-preview" aria-label="Illustrative build analysis example"><div className="landing-preview-title"><LandingSprite name="title"/><h2>Generated Regex</h2></div><div className="landing-preview-body"><LandingSprite name="preview"/><div className="landing-example-code"><LandingSprite name="field"/><code>{sample.regex}</code></div><p className="landing-example-meta">Example · {sample.length} / 250 characters · {sample.blocked.length} blocked mods</p><h3>Why these were flagged</h3>{[
    ['Block','Physical Thorns','Example hit build with weak mitigation'],['Block','No Regeneration','Regeneration is the main recovery'],['Allow','Increased Accuracy','Example build does not rely on evasion'],
   ].map(([status,title,text])=><div className="landing-example-row" key={title}><LandingSprite name="row"/><span className="landing-example-pill"><LandingSprite name="pill"/>{status}</span><div><strong>{title}</strong><p>{text}</p></div></div>)}<button className="landing-copy" onClick={()=>void copyExample()} type="button"><LandingSprite name="copy"/>Copy Regex</button></div></aside>
  </section>
  <section className="landing-stats" aria-label="MapRegex catalogue">{[[mapCatalogue.filter(m=>m.mapPool==='normal').length,'Normal map mods'],[mapCatalogue.filter(m=>m.mapPool==='nightmare').length,'Nightmare mods'],[3,'Filtering levels'],[1,'Search string']].map(([count,label])=><div key={label}><strong>{count}</strong><span>{label}</span></div>)}</section>
  <section className="landing-steps" id="how-it-works"><div className="landing-section-title"><h2>Your next map, in three steps</h2><p>Your build. Your choices. One search string.</p></div><div className="landing-step-grid">{[
   ['Export your build','In Path of Building: Import/Export Build → Generate → Copy. A pobb.in link works too.'],['Choose what to avoid','Import your build, choose a preset, then review the modifiers. Every choice is editable.'],['Copy into your stash','Paste your regex into the in-game stash search. Maps matching your filters will light up.'],
  ].map(([title,text],index)=><article className="landing-step" key={title}><LandingSprite name="step"/><span className="landing-step-number"><LandingSprite name="number"/>0{index+1}</span><h3>{title}</h3><p>{text}</p>{index<2&&<span className="landing-step-arrow" aria-hidden="true">›</span>}</article>)}</div></section>
  <section className="landing-features"><div className="landing-section-title"><h2>Built to be understood</h2><p>Every flag comes with a reason, and every call is yours to change.</p></div><div className="landing-feature-grid">{features.map(feature=><article className="landing-feature" key={feature.title}><LandingSprite name="feature"/><span className="landing-feature-icon"><LandingSprite name={feature.icon}/></span><div><h3>{feature.title}</h3><p>{feature.text}</p></div></article>)}</div></section>
  <section className="landing-honesty"><LandingSprite name="honesty"/><div><h3>A starting point, not a safety guarantee</h3><p>Saved PoB data can miss conditional mechanics and uptime, so give the final list a quick look before you run it.</p></div><div className="landing-legend"><h4>Rating legend</h4><ul>{[['brick','Build-breaking'],['dangerous','Dangerous'],['uncomfortable','Uncomfortable'],['review','Needs review'],['free','Free']].map(([rating,label])=><li key={rating}><span className={`severity-orb severity-orb--${rating}`}/>{label}</li>)}</ul></div></section>
  <section className="landing-cta"><LandingSprite name="cta"/><h2>Ready to search smarter?</h2><p>Import your build and get a personal map regex in seconds.</p><div><button type="button" onClick={focusImport}><LandingSprite name="ctaImport"/>Import your build</button><button type="button" disabled={loading} onClick={example}><LandingSprite name="ctaExample"/>{loading?'Analyzing…':'Try an example'}</button></div></section>
  <details id="faq" className="landing-privacy"><summary>Privacy & build data</summary><p>Your export is sent to the MapRegex analyzer. For a pobb.in link, the server retrieves the export from pobb.in. The app does not save your submitted build to a database; results stay in browser memory. Hosting providers may retain request logs.</p></details>
 </div>;
}
