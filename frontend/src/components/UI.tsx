import { useEffect, useId } from 'react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import type { Rating } from '../types';
import { useAppStore } from '../store/useAppStore';

export function Sigil({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 42 42" fill="none" aria-hidden="true">
    <path d="M5 10 15 5l12 5 10-5v27l-10 5-12-5-10 5V10Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    <path d="M15 5v8m12-3v3M15 29v3m12-3v8" stroke="currentColor" strokeWidth="1.5" />
    <circle cx="15" cy="23" r="2" fill="currentColor" />
    <path d="M27 16v12m-5-9 10 6m-10 0 10-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>;
}

export function Panel({ children, className = '', id }: { children: ReactNode; className?: string; id?: string }) {
  return <section id={id} className={`poe-panel ${className}`}>{children}</section>;
}

export function OrnamentDivider() {
  return <div className="ornament-divider" aria-hidden="true"><span /></div>;
}

export function SectionHeading({ number, title, subtitle, aside }: { number: string; title: string; subtitle?: string; aside?: ReactNode }) {
  return <div className="section-heading">
    <div><p className="eyebrow">{number} / MAPREGEX</p><h2>{title}</h2>{subtitle && <p className="section-subtitle">{subtitle}</p>}</div>
    {aside && <div className="section-heading-aside">{aside}</div>}
  </div>;
}

export function Button({ variant = 'secondary', className = '', children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'quiet' }) {
  return <button className={`poe-button poe-button--${variant} ${className}`} {...props}>{children}</button>;
}

export function SeverityOrb({ rating, small = false }: { rating: Rating; small?: boolean }) {
  return <span className={`severity-orb severity-orb--${rating} ${small ? 'severity-orb--small' : ''}`} aria-hidden="true" />;
}

export const ratingLabels: Record<Rating, string> = {
  brick: 'Build-breaking', dangerous: 'Dangerous', uncomfortable: 'Uncomfortable', free: 'Free', review: 'Needs review',
};

export function PoeTooltip({ title, children, body, rarity = 'magic', className = '' }: {
  title: string; children: ReactNode; body: ReactNode; rarity?: 'magic' | 'rare' | 'unique' | 'normal'; className?: string;
}) {
  const id = useId();
  return <span className={`tooltip-host ${className}`} tabIndex={0} aria-describedby={id}>
    {children}
    <span id={id} role="tooltip" className={`poe-tooltip poe-tooltip--${rarity}`}>
      <span className="poe-tooltip__title">{title}</span>
      <span className="poe-tooltip__divider" />
      <span className="poe-tooltip__body">{body}</span>
    </span>
  </span>;
}

export function Check({ checked, label, onChange, disabled = false }: { checked: boolean; label: string; onChange: (checked: boolean) => void; disabled?: boolean }) {
  return <label className={`check-row ${disabled ? 'is-disabled' : ''}`}>
    <input type="checkbox" checked={checked} onChange={event => onChange(event.target.checked)} disabled={disabled} />
    <span className="check-box" aria-hidden="true" />
    <span>{label}</span>
  </label>;
}

export function Toast() {
  const toast = useAppStore(state => state.toast);
  const dismiss = useAppStore(state => state.dismissToast);
  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(dismiss, 2600);
    return () => window.clearTimeout(timer);
  }, [toast, dismiss]);
  return <div className={`toast ${toast ? 'toast--visible' : ''}`} role="status" aria-live="polite">
    <Sigil className="toast__sigil" /><span>{toast}</span>
  </div>;
}
