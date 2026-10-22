import { useRef } from 'react';
import exampleExport from '../../../../fixtures/test-build.pob.txt?raw';
import { Button } from '../../components/UI';
import { Sprite } from '../../components/Sprite';
import { useAppStore } from '../../store/useAppStore';
export function BuildImport() {
  const {source,setSource,analyze,loading,error,analysis,resetBuild,resetPreferences} = useAppStore();
  const input = useRef<HTMLTextAreaElement>(null);
  return <section id="generator" className="import-section" aria-labelledby="import-heading"><h1 id="import-heading">Import Build</h1>
    <form className="figma-import" aria-busy={loading} onSubmit={e=>{e.preventDefault();void analyze();}}>
      <div className="import-input"><Sprite name="input" /><textarea ref={input} id="build-source" aria-label="pobb.in link or Path of Building export code" value={source} onChange={e=>setSource(e.target.value)} placeholder="Paste pobb.in link or Path of Building export code…" rows={1} spellCheck={false} aria-invalid={Boolean(error)} aria-describedby="import-error" onKeyDown={e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();void analyze();}}} /></div>
      <Button type="submit" variant="primary" disabled={loading}>{loading ? 'Analyzing…' : 'Import / Analyze'}</Button>
    </form>
    <div className="import-extra"><button id="open-build-import" type="button" onClick={()=>input.current?.focus()}>Paste PoB</button><button type="button" disabled={loading} onClick={()=>{resetBuild();resetPreferences();}}>Reset</button><button type="button" disabled={loading} onClick={()=>{setSource(exampleExport.trim());void analyze();}}>Try an example build</button><a href="#faq">Privacy</a></div>
    <div id="import-error" className={`import-message ${error ? 'import-message--error' : ''}`} role={error ? 'alert' : 'status'}>{error || (analysis ? `${analysis.profile.main_skill || 'Build'} loaded · ${analysis.mods.length} modifiers assessed` : '')}</div>
  </section>;
}
