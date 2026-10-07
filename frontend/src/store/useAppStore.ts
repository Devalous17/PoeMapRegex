import { create } from 'zustand';
import { analyzeBuild, exampleAnalysis } from '../services/analyzer';
import { EMPTY_PREFERENCES } from '../types';
import type { AnalysisResult, Category, Decision, Preferences, Preset, Rating } from '../types';

type RatingFilter = Rating | 'all';

interface AppState {
  source: string;
  analysis: AnalysisResult | null;
  loading: boolean;
  error: string;
  preset: Preset;
  mapPool: 'normal' | 'nightmare';
  overrides: Record<string, Decision>;
  ratingFilter: RatingFilter;
  search: string;
  categories: Category[];
  preferences: Preferences;
  toast: string;
  setSource: (value: string) => void;
  analyze: () => Promise<void>;
  loadExample: () => Promise<void>;
  setPreset: (preset: Preset) => void;
  setMapPool: (pool: 'normal' | 'nightmare') => void;
  applySuppliedAvoid: (mods: AnalysisResult['mods']) => void;
  setDecision: (id: string, decision: Decision) => void;
  clearDecisions: (mods: AnalysisResult['mods']) => void;
  resetDecisions: () => void;
  setRatingFilter: (filter: RatingFilter) => void;
  setSearch: (value: string) => void;
  toggleCategory: (category: Category) => void;
  setPreferences: (preferences: Preferences) => void;
  resetPreferences: () => void;
  showToast: (message: string) => void;
  dismissToast: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  source: '',
  analysis: null,
  loading: false,
  error: '',
  preset: 'balanced',
  mapPool: 'normal',
  overrides: {},
  ratingFilter: 'all',
  search: '',
  categories: [],
  preferences: { ...EMPTY_PREFERENCES },
  toast: '',
  setSource: source => set({ source, error: '' }),
  analyze: async () => {
    const source = get().source.trim();
    if (!source) { set({ error: 'Paste a pobb.in link or a Path of Building export first.' }); return; }
    set({ loading: true, error: '' });
    try {
      const analysis = await analyzeBuild(source);
      set({ analysis, loading: false, overrides: {}, ratingFilter: 'all', categories: [], search: '' });
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Could not analyze this build.' });
    }
  },
  loadExample: async () => {
    set({ loading: true, error: '', source: 'https://pobb.in/cLFx01vDz_iz' });
    const analysis = await exampleAnalysis();
    set({ analysis, loading: false, overrides: {}, ratingFilter: 'all', categories: [], search: '' });
  },
  setPreset: preset => set({ preset }),
  setMapPool: mapPool => set({ mapPool, ratingFilter: 'all', categories: [], search: '' }),
  applySuppliedAvoid: mods => set(state => ({ overrides: {
    ...state.overrides,
    ...Object.fromEntries(mods.map(mod => [mod.id, mod.suppliedAvoid ? 'block' : 'allow'])),
  } })),
  setDecision: (id, decision) => set(state => ({ overrides: { ...state.overrides, [id]: decision } })),
  clearDecisions: mods => set(state => ({ overrides: {
    ...state.overrides,
    ...Object.fromEntries(mods.map(mod => [mod.id, 'allow' as Decision])),
  } })),
  resetDecisions: () => set({ overrides: {} }),
  setRatingFilter: ratingFilter => set({ ratingFilter }),
  setSearch: search => set({ search }),
  toggleCategory: category => set(state => ({ categories: state.categories.includes(category)
    ? state.categories.filter(item => item !== category) : [...state.categories, category] })),
  setPreferences: preferences => set({ preferences }),
  resetPreferences: () => set({ preferences: { ...EMPTY_PREFERENCES, minimums: {}, rarities: [], chisels: [] } }),
  showToast: toast => set({ toast }),
  dismissToast: () => set({ toast: '' }),
}));
