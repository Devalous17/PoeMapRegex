import type { CSSProperties } from 'react';
export function Icon({ name, className = '' }: { name: string; className?: string }) {
  return <span aria-hidden="true" className={`game-icon ${className}`} style={{ '--icon': `url("/icons/${name}.svg")` } as CSSProperties} />;
}
