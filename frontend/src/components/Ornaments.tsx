import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

export function Crest({ className = '' }: { className?: string }) {
  return <svg className={`crest ${className}`} viewBox="0 0 400 80" fill="none" aria-hidden="true">
    <path d="M10 58h120l30-20 40 16 40-16 30 20h120M30 48h90l40-30 40 26 40-26 40 30h90" />
    <path d="m46 44 32-22 40 12-23 8m259 2-32-22-40 12 23 8M143 33l-9-18 39 9m84 9 9-18-39 9" />
    <path d="m200 4 16 25-16 37-16-37L200 4Zm0 13v36m-39-19-25 28h-32m135-28 25 28h32" />
    <circle cx="61" cy="55" r="5"/><circle cx="339" cy="55" r="5"/>
  </svg>;
}

export function Corners() {
  return <span className="frame-corners" aria-hidden="true">{[0, 1, 2, 3].map(i => <svg key={i} viewBox="0 0 48 48"><path d="M2 46V2h44M7 35V7h28M12 28c17 0 19-16 8-16-9 0-9 13-1 12M4 4l13 13m-6-6 8-7m-8 7-7 8" fill="none" stroke="currentColor"/><path d="m5 5 4-2-2 6Z" fill="currentColor"/></svg>)}</span>;
}

export function NavEnds() {
  return <span className="nav-ends" aria-hidden="true">{[0,1].map(i => <svg key={i} viewBox="0 0 76 80"><path d="M72 8H27C6 8 4 34 22 36c13 2 15-17 4-15M72 16H44L31 40l13 24h28M72 72H27C6 72 4 46 22 44c13-2 15 17 4 15M20 40 4 27 9 40 4 53l16-13Zm11 0h41" fill="none"/><path d="m44 40 10-9 10 9-10 9-10-9Z"/></svg>)}</span>;
}

export function Arch({ className = '' }: { className?: string }) {
  return <svg className={`gothic-arch ${className}`} viewBox="0 0 1000 700" preserveAspectRatio="none" fill="none" aria-hidden="true">
    <path d="M20 700V290Q20 140 180 130Q360 120 500 15Q640 120 820 130Q980 140 980 290V700M38 700V293Q38 155 183 149Q360 140 500 39Q640 140 817 149Q962 155 962 293V700"/>
    <path d="M95 700V300Q95 170 290 178Q425 180 500 80Q575 180 710 178Q905 170 905 300V700M180 130q-50 120 60 130t100-100M820 130q50 120-60 130t-100-100M500 16v127m-80-70 80 70 80-70"/>
    <path d="M20 350h75m810 0h75M20 580h75m810 0h75M52 700V350m896 350V350"/>
  </svg>;
}

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

export function Atmosphere() {
  const [paused, setPaused] = useState(document.hidden);
  useEffect(() => { const update = () => setPaused(document.hidden); document.addEventListener('visibilitychange', update); return () => document.removeEventListener('visibilitychange', update); }, []);
  return <div className={`atmosphere ${paused ? 'is-paused' : ''}`} aria-hidden="true"><div className="mist mist--one"/><div className="mist mist--two"/>{Array.from({ length: 12 }, (_, i) => <i key={i} style={{ left: `${8 + i * 7.2}%`, animationDelay: `${i * -1.7}s`, animationDuration: `${15 + i % 4 * 3}s` }} />)}</div>;
}

export function AtlasArt() {
  return <div className="atlas-art" aria-hidden="true"><Arch /><svg className="atlas-constellation" viewBox="0 0 600 600" fill="none">
    <circle cx="300" cy="300" r="235"/><circle cx="300" cy="300" r="215"/><circle cx="300" cy="300" r="150"/>
    <path d="m300 35 65 165 174 24-122 123 30 175-147-83-147 83 30-175L61 224l174-24 65-165ZM300 125v350M125 300h350m-299-124 248 248m0-248L176 424"/>
    <path d="m300 190 70 110-70 110-70-110 70-110Zm0 40 40 70-40 70-40-70 40-70Z"/>
    {[[300,65],[505,225],[425,475],[175,475],[95,225]].map(([x,y],i) => <g key={i}><circle cx={x} cy={y} r="18"/><circle cx={x} cy={y} r="6" fill="currentColor"/></g>)}
  </svg><span className="atlas-art__caption">THE ATLAS, UNDERSTOOD</span></div>;
}
