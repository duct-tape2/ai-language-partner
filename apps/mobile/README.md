# AI Language Partner Mobile (apps/mobile)

Expo React Native (TypeScript) phone app. Korean learners practice speaking
Japanese with an AI partner. Frontend owner: Claude. First vertical slice:
`tired_today`.

## Run

```bash
cd apps/mobile
npm install
npx expo start        # then press i (iOS), a (Android), or scan the QR in Expo Go
```

## API modes

```bash
# mock mode (default) - uses packages/shared fixtures, no backend needed
npx expo start

# real mode - talks to the Codex backend, falls back to fixtures on failure
EXPO_PUBLIC_USE_MOCK_API=false EXPO_PUBLIC_API_BASE_URL=http://localhost:8000 npx expo start
```

Copy `.env.example` to `.env` to set these persistently.

## Structure

```text
index.js              registerRootComponent entry (native + web)
App.tsx               navigator (screen switch) + bottom tab bar
babel.config.js       babel-preset-expo
metro.config.js       monorepo: watches workspace root for packages/shared
app.json              Expo config (icon, splash, adaptive icon, web)
src/
  theme.ts            color tokens (light/dark) + spacing/radius
  ThemeContext.tsx    ThemeProvider + useTheme (dark mode, reduced motion)
  components.tsx      themed primitives + ProgressRing/XPBar/Furigana/DiffText/
                      PitchAccent/GradeButtons/Segmented/StreakFlame + motion
  store.ts            useApp() - state, nav, actions, persistence, events
  storage.ts          typed AsyncStorage wrapper
  srs.ts              ts-fsrs spaced-repetition engine (client-side)
  gamification.ts     XP / levels / quests / badges / streak logic
  personaStyle.ts     per-persona voice preset + identity color
  text.ts             pronunciation token-diff + accuracy
  i18n.ts             KO string table + furigana / pitch-accent data
  api/client.ts       contract-shaped API client (mock + real + fallback)
  screens/
    OnboardingScreen.tsx   HomeTodayScreen.tsx   PersonaSelectScreen.tsx
    PracticeRoomScreen.tsx VoicePracticeScreen.tsx ReviewCardsScreen.tsx
    ProgressScreen.tsx     SettingsScreen.tsx
assets/               icon.png, adaptive-icon.png, splash.png, favicon.png
```

## Competitive standing

Benchmarked against the most-starred in-domain open-source app
([kana-dojo](https://github.com/lingdojo/kana-dojo), normalized to 100); an
independent 3-judge re-score puts this frontend at ~130. See
`docs/frontend/COMPETITIVE_ANALYSIS.md`.

## Contract

API client function names and DTO shapes follow
`contracts/openapi_v0.yaml` and `packages/shared/src/types.ts`. The app
never invents endpoints or renames fields. Shared/contract files are
read-only for frontend-only PRs; proposed contract changes should update the
OpenAPI spec and backend implementation in the same PR.

## Voice

TTS uses `expo-speech` (device speech, `ja-JP`) plus the
`/v1/tts/synthesize` contract call. STT is mock in this slice
(`今日めっちゃ疲れた`) via `/v1/stt/transcribe`.

## Verification

No iOS Simulator runtime was available in the build environment, so the
app was verified by: `tsc --noEmit` (0 errors), `expo export --platform
web` (clean Metro bundle), and headless viewport checks. Regenerate screenshots
locally when reviewing visual changes; do not commit generated screenshots.
