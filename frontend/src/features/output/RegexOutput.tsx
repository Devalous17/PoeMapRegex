import { Sprite } from '../../components/Sprite';
import { Icon } from '../../components/Icon';
import { useModHighlight } from '../../components/HighlightContext';
import { useMemo, useState } from 'react';
import { Button } from '../../components/UI';
import { buildRegex, rollSamples } from '../../services/regexBuilder';
import { useAppStore } from '../../store/useAppStore';
import type { ClassifiedMod, RegexPart } from '../../types';

// Presentation only: retain every character, splitting top-level alternatives for source hints.
function RegexTerm({ part, mods }: { part: RegexPart; mods: ClassifiedMod[] }) {
  const { ids, setIds } = useModHighlight();
  if (part.kind === 'preference') return <span className="regex-code__preference">{part.text}</span>;
  const prefix = part.kind === 'exclude' ? '"!' : '"';
  const inner = part.text.slice(prefix.length, -1);
  const pieces: string[] = [];
  let start = 0, depth = 0, inClass = false, escaped = false;
  for (let i = 0; i < inner.length; i++) {
    const c = inner[i];
    if (escaped) { escaped = false; continue; }
    if (c === '\\') { escaped = true; continue; }
    if (c === '[') inClass = true;
    if (c === ']') inClass = false;
    if (inClass) continue;
    if (c === '(') depth++;
    if (c === ')') depth--;
    if (c === '|' && depth === 0) { pieces.push(inner.slice(start, i)); start = i + 1; }
  }
  pieces.push(inner.slice(start));
  return <>{prefix}{pieces.map((piece, index) => {
    let sources: ClassifiedMod[] = [];
    try { const pattern = new RegExp(piece, 'i'); sources = mods.filter(mod => rollSamples(mod.matchText ?? mod.name).some(sample => pattern.test(sample))); } catch { /* Invalid output is already guarded by the core builder. */ }
    const sourceIds = sources.map(mod => mod.id);
    return <span key={index}>{index > 0 ? '|' : ''}<span className={`regex-code__${part.kind} ${sourceIds.some(id => ids.includes(id)) ? 'is-linked' : ''}`} title={sources.map(mod => mod.name).join(' · ')} onMouseEnter={() => setIds(sourceIds)} onMouseLeave={() => setIds([])}>{piece}</span></span>;
  })}"</>;
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
    <Sprite name="regexPanel" /><div className="regex-dock__inner">
      <div className="regex-dock__heading"><Sprite name="title" /><h2>Generated Regex</h2></div>
      <div className="regex-dock__main"><div className="regex-code" tabIndex={0} aria-label="Generated regex"><Sprite name="regexField" />
        {output.regex ? <code key={output.regex} className="regex-code__live">{output.parts.map((part, index) => <span key={`${index}-${part.text}`}>{index > 0 ? ' ' : ''}<RegexTerm part={part} mods={part.kind === 'exclude' ? output.blocked : output.wanted} /></span>)}</code> : <span className="regex-placeholder">Click modifiers or set map values to build a search.</span>}
      </div><div className="regex-meter"><span className={tooLong ? 'is-over' : ratio >= 80 ? 'is-near' : ''}>{output.length} / {limit}</span><div className="regex-meter__track"><span className={tooLong ? 'is-over' : ratio >= 80 ? 'is-near' : ''} style={{ width: `${ratio}%` }} /></div></div></div>
      <Button type="button" variant="primary" className="regex-copy" disabled={!output.regex || tooLong || !output.valid} onClick={() => void copy(output.regex, mode === 'example' ? 'Example regex copied. Analyze your own build before use.' : 'Regex copied to clipboard')}>
        <Icon name="copy" />{copied ? 'Copied!' : 'Copy Regex'} <span aria-hidden="true">{copied ? '✓' : '↗'}</span>
      </Button>
    </div>
    <div className="regex-dock__details"><div className="regex-dock__summary"><span><strong>Blocks:</strong> {output.blocked.length}</span><span><strong>Wants:</strong> {output.wanted.length}</span>{preferenceCount > 0 && <span><strong>Applied filters:</strong> {preferenceCount}</span>}</div>
    </div>
    {(output.warnings.length > 0 || !!coverage?.issues.length || mode !== 'live') && <details className="regex-notes"><summary>Search notes & limitations</summary><div className="regex-dock__warnings" role="status">{mode === 'manual' && <span>Manual selection · import a build for recommendations.</span>}{mode === 'example' && <span>Example profile: ratings are illustrative.</span>}{mode === 'live' && !!coverage?.issues.length && <span>Build coverage incomplete · {coverage.issues.length} checks need review. <a href="#build-profile">Review build dependencies</a>. This search is a baseline, not a guarantee.</span>}{output.warnings.map(warning => <span key={warning}>{warning}</span>)}{tooLong && output.split.length > 0 && <button type="button" onClick={() => setShowSplit(value => !value)}>{showSplit ? 'Hide' : 'View'} partial search batches</button>}</div></details>}
    {showSplit && tooLong && <div className="regex-split"><p>Each batch covers only part of the selection. The full set cannot be used in one in-game search.</p>{output.split.map((piece, index) => <div key={`${index}-${piece.length}`}><span>BATCH {index + 1} / {output.split.length}</span><code>{piece}</code><button type="button" onClick={() => void copy(piece, `Batch ${index + 1} copied`)}>Copy</button></div>)}</div>}
  </section>;
}
