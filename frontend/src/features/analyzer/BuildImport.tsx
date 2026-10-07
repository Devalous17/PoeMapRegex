import type { FormEvent, KeyboardEvent } from 'react';
import { Button, OrnamentDivider, Panel, Sigil } from '../../components/UI';
import { useAppStore } from '../../store/useAppStore';

export function BuildImport() {
  const source = useAppStore(state => state.source);
  const setSource = useAppStore(state => state.setSource);
  const analyze = useAppStore(state => state.analyze);
  const loadExample = useAppStore(state => state.loadExample);
  const loading = useAppStore(state => state.loading);
  const error = useAppStore(state => state.error);
  const analysis = useAppStore(state => state.analysis);

  function submit(event: FormEvent) { event.preventDefault(); void analyze(); }
  function shortcut(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); void analyze(); }
  }

  return <section id="generator" className="hero-section">
    <div className="hero-halo" aria-hidden="true" />
    <div className="hero-heading">
      <p className="eyebrow hero-overline"><span className="eyebrow-rule" /> PATH OF EXILE 1 · MAP SEARCH TOOL <span className="eyebrow-rule" /></p>
      <h1>Know Your <em>Maps.</em></h1>
      <p>Paste a pobb.in link. We find the mods that could stop your build and write the regex for you.</p>
    </div>
    <Panel className="import-panel">
      <div className="import-panel__head">
        <div className="import-title"><Sigil className="import-title__sigil" /><div><span className="panel-kicker">BUILD IMPORT</span><strong>Path of Building profile</strong></div></div>
        <span className="import-panel__edition">POE 1 / ENGLISH</span>
      </div>
      <OrnamentDivider />
      <form onSubmit={submit}>
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
          <button className="text-link" type="button" onClick={() => void loadExample()} disabled={loading}>Try an example build <span aria-hidden="true">↗</span></button>
        </div>
      </form>
      <div id="import-error" className={`import-message ${error ? 'import-message--error' : ''}`} role={error ? 'alert' : 'status'} aria-live="polite">
        {error || (analysis ? `${analysis.mode === 'example' ? 'Example profile' : 'Build'} loaded. ${analysis.mods.length} map modifiers ready to review.` : '')}
      </div>
      {loading && <div className="loading-skeleton" aria-hidden="true"><span /><span /><span /></div>}
    </Panel>
    <div className="hero-bottom"><span>01 / IMPORT</span><span className="hero-bottom__line" /><span>ANALYZE · REVIEW · COPY</span></div>
  </section>;
}
