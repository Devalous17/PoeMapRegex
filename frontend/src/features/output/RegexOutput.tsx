import { useMemo, useState } from 'react';
import { Button, Sigil } from '../../components/UI';
import { buildRegex } from '../../services/regexBuilder';
import { useAppStore } from '../../store/useAppStore';
import type { ClassifiedMod } from '../../types';

function downloadPreset(data: object) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'mapregex-preset.json';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function RegexOutput({ mods, limit, mode }: { mods: ClassifiedMod[]; limit: number; mode: 'live' | 'example' | 'manual' }) {
  const coverage = useAppStore(state => state.analysis?.profile.coverage);
  const preset = useAppStore(state => state.preset);
  const overrides = useAppStore(state => state.overrides);
  const preferences = useAppStore(state => state.preferences);
  const showToast = useAppStore(state => state.showToast);
  const [showSplit, setShowSplit] = useState(false);
  const [copied, setCopied] = useState(false);
  const output = useMemo(() => buildRegex(mods, preset, overrides, preferences, limit), [mods, preset, overrides, preferences, limit]);
  const tooLong = output.length > limit;
  const ratio = Math.min(100, Math.round(output.length / limit * 100));
  const preferenceCount = output.parts.filter(part => part.kind === 'preference').length;

  async function copy(text: string, success = 'Regex copied to clipboard') {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      showToast(success);
      window.setTimeout(() => setCopied(false), 1900);
    } catch { showToast('Clipboard unavailable. Select the regex text and copy it manually.'); }
  }

  return <section id="output" className="regex-dock" aria-label="Generated map regex">
    <div className="regex-dock__inner">
      <div className="regex-dock__heading"><Sigil /><div><span className="panel-kicker">YOUR MAP SEARCH</span><strong>Regex output</strong></div></div>
      <div className="regex-dock__main"><div className="regex-code" tabIndex={0} aria-label="Generated regex">
        {output.regex ? <code key={output.regex} className="regex-code__live">{output.parts.map((part, index) => <span key={`${index}-${part.text}`} className={`regex-code__${part.kind}`}>{index > 0 ? ' ' : ''}{part.text}</span>)}</code> : <span className="regex-placeholder">Click modifiers or set map values to build a search.</span>}
      </div><div className="regex-meter"><span className={tooLong ? 'is-over' : ratio >= 80 ? 'is-near' : ''}>{output.length} / {limit}</span><div className="regex-meter__track"><span className={tooLong ? 'is-over' : ratio >= 80 ? 'is-near' : ''} style={{ width: `${ratio}%` }} /></div></div></div>
      <Button type="button" variant="primary" className="regex-copy" disabled={!output.regex || tooLong || !output.valid} onClick={() => void copy(output.regex, mode === 'example' ? 'Example regex copied. Analyze your own build before use.' : 'Regex copied to clipboard')}>
        {copied ? 'Copied' : 'Copy Regex'} <span aria-hidden="true">{copied ? '✓' : '↗'}</span>
      </Button>
    </div>
    <div className="regex-dock__details"><div className="regex-dock__summary"><span><strong>Blocks:</strong> {output.blocked.length}</span><span><strong>Wants:</strong> {output.wanted.length}</span>{preferenceCount > 0 && <span><strong>Applied filters:</strong> {preferenceCount}</span>}</div>
      <details className="regex-options"><summary>Options</summary><button type="button" onClick={() => { downloadPreset({ preset, overrides, preferences }); showToast('Preset exported'); }}>Export preset</button></details>
    </div>
    {(output.warnings.length > 0 || !!coverage?.issues.length || mode !== 'live') && <div className="regex-dock__warnings" role="status">{mode === 'manual' && <span>Manual selection · import a build for recommendations.</span>}{mode === 'example' && <span>Example profile: ratings are illustrative.</span>}{mode === 'live' && !!coverage?.issues.length && <span>Build coverage incomplete · {coverage.issues.length} checks need review. <a href="#build-profile">Review build dependencies</a>. This search is a baseline, not a guarantee.</span>}{output.warnings.map(warning => <span key={warning}>{warning}</span>)}{tooLong && output.split.length > 0 && <button type="button" onClick={() => setShowSplit(value => !value)}>{showSplit ? 'Hide' : 'View'} partial search batches</button>}</div>}
    {showSplit && tooLong && <div className="regex-split"><p>Each batch covers only part of the selection. The full set cannot be used in one in-game search.</p>{output.split.map((piece, index) => <div key={`${index}-${piece.length}`}><span>BATCH {index + 1} / {output.split.length}</span><code>{piece}</code><button type="button" onClick={() => void copy(piece, `Batch ${index + 1} copied`)}>Copy</button></div>)}</div>}
  </section>;
}
