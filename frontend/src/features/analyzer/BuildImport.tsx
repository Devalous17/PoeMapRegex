import { Icon } from '../../components/Icon';
import exampleExport from '../../../../fixtures/test-build.pob.txt?raw';
import type { FormEvent, KeyboardEvent } from 'react';
import { Button, OrnamentDivider, Panel, SectionHeading } from '../../components/UI';
import { useAppStore } from '../../store/useAppStore';

export function BuildImport() {
  const source = useAppStore(state => state.source);
  const setSource = useAppStore(state => state.setSource);
  const analyze = useAppStore(state => state.analyze);
  const loading = useAppStore(state => state.loading);
  const error = useAppStore(state => state.error);
  const analysis = useAppStore(state => state.analysis);

  function submit(event: FormEvent) { event.preventDefault(); void analyze(); }
  function shortcut(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); void analyze(); }
  }

  return <section id="generator" className="content-section import-section">
    <SectionHeading number="02" title="Bring your build" subtitle="Paste a pobb.in link or your Path of Building export. We will read the saved snapshot." />
    <Panel className="import-panel">
      <div className="import-panel__head">
        <div className="import-title"><Icon name="import" className="import-title__sigil" /><div><span className="panel-kicker">BUILD IMPORT</span><strong>Path of Building profile</strong></div></div>
        <span className="import-panel__edition">POE 1 / ENGLISH</span>
      </div>
      <OrnamentDivider />
      <form onSubmit={submit} aria-busy={loading}>
        <label htmlFor="build-source" className="field-label">POBB.IN LINK OR EXPORT CODE</label>
        <div className="import-control">
          <textarea id="build-source" value={source} onChange={event => setSource(event.target.value)} onKeyDown={shortcut}
            placeholder="https://pobb.in/your-build-id" spellCheck={false} rows={2} aria-invalid={Boolean(error)} aria-describedby="import-help import-error" />
          <Button type="submit" variant="primary" className="analyze-button" disabled={loading}>
            {loading ? <><span className="loading-rune" aria-hidden="true" /> Reading build…</> : <><span>Analyze Build</span><span className="button-arrow" aria-hidden="true">›</span></>}
          </Button>
        </div>
        <div className="import-foot">
          <span id="import-help">Raw Path of Building export codes also work. Press Ctrl+Enter to analyze.</span>
          <button className="text-link" type="button" onClick={() => { setSource(exampleExport.trim()); void analyze(); }} disabled={loading}>Try an example build <span aria-hidden="true">↗</span></button>
        </div>
      </form>
      <div id="import-error" className={`import-message ${error ? 'import-message--error' : ''}`} role={error ? 'alert' : 'status'} aria-live="polite">
        {error || (analysis ? `${analysis.mode === 'example' ? 'Example profile' : 'Build'} loaded. ${analysis.mods.length} map modifiers ready to review.` : '')}
      </div>
      {loading && <div className="loading-skeleton" aria-hidden="true"><span /><span /><span /></div>}
    </Panel>
    <p className="import-privacy">Your export is sent to our analyzer. No account or build database. <a href="#faq">How your data is handled</a>.</p><div className="hero-bottom"><span>01 / IMPORT</span><span className="hero-bottom__line" /><span>ANALYZE · REVIEW · COPY</span></div>
  </section>;
}
