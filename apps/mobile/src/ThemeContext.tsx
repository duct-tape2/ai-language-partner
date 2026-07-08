import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { lightTheme, darkTheme, type Theme } from './theme';
import { loadJSON, saveJSON } from './storage';

type ThemeMode = 'light' | 'dark';

type ThemeCtx = {
  theme: Theme;
  mode: ThemeMode;
  setMode: (m: ThemeMode) => void;
  toggleMode: () => void;
  reducedMotion: boolean;
  setReducedMotion: (v: boolean) => void;
};

const Ctx = createContext<ThemeCtx | null>(null);

type Persisted = { mode: ThemeMode; reducedMotion: boolean };

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>('light');
  const [reducedMotion, setReducedMotionState] = useState(false);

  useEffect(() => {
    loadJSON<Persisted>('themePrefs', { mode: 'light', reducedMotion: false }).then((p) => {
      setModeState(p.mode);
      setReducedMotionState(p.reducedMotion);
    });
  }, []);

  const persist = (next: Persisted) => saveJSON('themePrefs', next);

  const setMode = (m: ThemeMode) => {
    setModeState(m);
    persist({ mode: m, reducedMotion });
  };
  const toggleMode = () => setMode(mode === 'light' ? 'dark' : 'light');
  const setReducedMotion = (v: boolean) => {
    setReducedMotionState(v);
    persist({ mode, reducedMotion: v });
  };

  const value = useMemo<ThemeCtx>(
    () => ({
      theme: mode === 'dark' ? darkTheme : lightTheme,
      mode,
      setMode,
      toggleMode,
      reducedMotion,
      setReducedMotion,
    }),
    [mode, reducedMotion],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTheme(): ThemeCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error('useTheme must be used within ThemeProvider');
  return v;
}
