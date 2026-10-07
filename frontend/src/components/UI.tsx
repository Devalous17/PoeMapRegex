import { useEffect, useId } from 'react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import type { Rating } from '../types';
import { useAppStore } from '../store/useAppStore';

export function Sigil({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 42 42" fill="none" aria-hidden="true">
    <path d="M21 2 31 11 40 21 31 31 21 40 11 31 2 21 11 11Z" stroke="currentColor" strokeWidth="1.3" />
    <path d="M21 7 27 15 35 21 27 27 21 35 15 27 7 21 15 15Z" stroke="currentColor" strokeWidth=".8" opacity=".65" />
    <path d="M21 11 24 18 31 21 24 24 21 31 18 24 11 21 18 18Z" fill="currentColor" opacity=".75" />
    <circle cx="21" cy="21" r="2.4" fill="#0b0a08" />
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
  brick: 'Build-breaking', dangerous: 'Dangerous', uncomfortable: 'Uncomfortable', free: 'Safe', review: 'Needs review',
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
