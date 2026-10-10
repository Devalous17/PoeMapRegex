import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

const HighlightContext = createContext<{ ids: string[]; setIds: (ids: string[]) => void }>({ ids: [], setIds: () => {} });
export function HighlightProvider({ children }: { children: ReactNode }) {
  const [ids, setIds] = useState<string[]>([]);
  return <HighlightContext.Provider value={{ ids, setIds }}>{children}</HighlightContext.Provider>;
}
export const useModHighlight = () => useContext(HighlightContext);
