// Developer/diagnostic UI (API mode, base URL, backend health, raw entitlement)
// is shown ONLY in dev builds. Production builds and the web export have
// __DEV__ === false, so this content never renders for end users.
export const SHOW_DEV_TOOLS: boolean = typeof __DEV__ !== 'undefined' ? __DEV__ : false;

// When STT/TTS/LLM are mock (no backend yet), the app is in demo mode. Used to
// honestly disclose that recognition results are illustrative, not real.
export const DEMO_MODE: boolean = (process.env.EXPO_PUBLIC_USE_MOCK_API ?? 'true') !== 'false';
