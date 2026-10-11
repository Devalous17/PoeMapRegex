import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

export function DiamondPager({ count, current, onSelect }: { count: number; current: number; onSelect?: (index: number) => void }) {
  return <div className="diamond-pager" role="group" aria-label="Tour steps">{Array.from({ length: count }, (_, i) => <button type="button" key={i} aria-label={`Tour step ${i + 1}`} aria-current={current === i ? 'step' : undefined} className={current === i ? 'is-active' : ''} disabled={!onSelect} onClick={() => onSelect?.(i)} />)}</div>;
}

export function Reveal({ children, className = '' }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || !('IntersectionObserver' in window)) { setVisible(true); return; }
    const observer = new IntersectionObserver(entries => { if (entries.some(e => e.isIntersecting)) { setVisible(true); observer.disconnect(); } }, { threshold: .08 });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return <div ref={ref} className={`reveal ${visible ? 'is-visible' : ''} ${className}`}>{children}</div>;
}
