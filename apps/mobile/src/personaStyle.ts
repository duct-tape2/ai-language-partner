// Per-persona voice presets (for expo-speech) and a stable identity color.
// Maps the abstract persona ids onto concrete frontend behaviour. No backend.
export type VoicePreset = { rate: number; pitch: number };

const VOICE: Record<string, VoicePreset> = {
  yui: { rate: 0.96, pitch: 1.18 }, // bright, gentle 20s friend
  haruka: { rate: 0.88, pitch: 1.0 }, // calm, clear teacher
  ren: { rate: 1.02, pitch: 0.9 }, // crisp, confident senpai
};

const COLOR: Record<string, string> = {
  yui: '#E36F4C',
  haruka: '#4B7BA8',
  ren: '#E0A12E',
};

export function personaVoice(id: string): VoicePreset {
  return VOICE[id] ?? { rate: 0.95, pitch: 1.0 };
}

export function personaColor(id: string): string {
  return COLOR[id] ?? '#E36F4C';
}

// 시로쿠마 character art per persona (matched to each voice/personality).
const IMAGE: Record<string, number> = {
  yui: require('../assets/persona_yui.png'),
  haruka: require('../assets/persona_haruka.png'),
  ren: require('../assets/persona_ren.png'),
};

export function personaImage(id: string): number | undefined {
  return IMAGE[id];
}
