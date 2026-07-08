// Design tokens + light/dark themes. Consumed through ThemeContext (useTheme).
export const spacing = { xs: 6, sm: 10, md: 14, lg: 20, xl: 28 } as const;
export const radius = { sm: 12, md: 16, lg: 22, pill: 999 } as const;

export type ThemeColors = {
  bg: string;
  surface: string;
  card: string;
  text: string;
  subtext: string;
  border: string;
  accent: string;
  accentDark: string;
  accentSoft: string;
  green: string;
  gold: string;
  goldText: string; // readable amber for TEXT (gold is too light on light bg); use gold only for fills/bars
  chip: string;
  chipText: string;
  danger: string;
  track: string;
  good: string;
  near: string;
  bad: string;
};

const light: ThemeColors = {
  bg: '#F7F4EF',
  surface: '#FBF8F3',
  card: '#FFFFFF',
  text: '#211F1F',
  subtext: '#5A534D',
  border: '#E6DED7',
  accent: '#E36F4C',
  accentDark: '#B94E32',
  accentSoft: '#FBEDE7',
  green: '#4B9A68',
  gold: '#E0A12E',
  goldText: '#8A5E10',
  chip: '#F1EBE4',
  chipText: '#B94E32',
  danger: '#C8463C',
  track: '#ECE4DC',
  good: '#4B9A68',
  near: '#E0A12E',
  bad: '#C8463C',
};

const dark: ThemeColors = {
  bg: '#16140F',
  surface: '#1E1B16',
  card: '#241F19',
  text: '#F3EDE4',
  subtext: '#BCB2A6',
  border: '#352E25',
  accent: '#F08A66',
  accentDark: '#F5A988',
  accentSoft: '#3A271E',
  green: '#6FBE8A',
  gold: '#E8B450',
  goldText: '#E8B450',
  chip: '#2C2620',
  chipText: '#F5A988',
  danger: '#E8675C',
  track: '#2C2620',
  good: '#6FBE8A',
  near: '#E8B450',
  bad: '#E8675C',
};

export type Theme = {
  mode: 'light' | 'dark';
  colors: ThemeColors;
  spacing: typeof spacing;
  radius: typeof radius;
};

export const lightTheme: Theme = { mode: 'light', colors: light, spacing, radius };
export const darkTheme: Theme = { mode: 'dark', colors: dark, spacing, radius };

// Backward-compatible default (light) for any non-hook usage.
export const theme = lightTheme.colors;
