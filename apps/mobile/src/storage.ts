import AsyncStorage from '@react-native-async-storage/async-storage';

// Single typed wrapper around AsyncStorage. Everything new the app stores
// (settings, streak, SRS cards, XP, persona memory) lives here - contract-safe
// local persistence, no backend.
const PREFIX = 'alp:'; // ai-language-partner

// Bump when the shape of any persisted value changes; migrate() runs on boot.
export const SCHEMA_VERSION = 1;

export const KEYS = {
  onboarded: 'onboarded',
  settings: 'settings',
  srsCards: 'srsCards',
  gamification: 'gamification',
  personaMemory: 'personaMemory',
  selectedPersona: 'selectedPersona',
  progress: 'progress',
  courseProgress: 'courseProgress',
  schemaVersion: 'schemaVersion',
} as const;

export async function loadJSON<T>(key: string, fallback: T): Promise<T> {
  try {
    const raw = await AsyncStorage.getItem(PREFIX + key);
    if (raw == null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export async function saveJSON<T>(key: string, value: T): Promise<void> {
  try {
    await AsyncStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    // best-effort; never crash UI on a storage error
  }
}

export async function clearAll(): Promise<void> {
  try {
    const keys = (await AsyncStorage.getAllKeys()).filter((k) => k.startsWith(PREFIX));
    await AsyncStorage.multiRemove(keys);
  } catch {
    // ignore
  }
}

// Run once on boot: stamp/upgrade the persisted schema version. Migrations for
// future versions are added here so an app update never reads stale-shaped data.
export async function migrate(): Promise<void> {
  const stored = await loadJSON<number>(KEYS.schemaVersion, 0);
  if (stored === SCHEMA_VERSION) return;
  // (no migrations needed yet for v1 -> just stamp)
  await saveJSON(KEYS.schemaVersion, SCHEMA_VERSION);
}

// Dev helper: dump all persisted app data as JSON (used by the dev-only export).
export async function exportAll(): Promise<string> {
  try {
    const keys = (await AsyncStorage.getAllKeys()).filter((k) => k.startsWith(PREFIX));
    const entries = await AsyncStorage.multiGet(keys);
    const obj: Record<string, unknown> = { schemaVersion: SCHEMA_VERSION };
    for (const [k, v] of entries) obj[k.slice(PREFIX.length)] = v ? JSON.parse(v) : null;
    return JSON.stringify(obj, null, 2);
  } catch {
    return '{}';
  }
}
