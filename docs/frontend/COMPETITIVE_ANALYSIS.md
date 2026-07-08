# Competitive Analysis + 105-Point Frontend Plan

Date: 2026-06-29. Scope: FRONTEND only (apps/mobile). Method: GitHub
star-sorted search (4 angles) + web reputation research, synthesized into a
frontend rubric. Benchmark leader normalized to 100; goal >= 105.

## Landscape (most-starred / most-acclaimed, in domain)

| Project | Stars | Why it matters |
|---|---|---|
| [Anki](https://github.com/ankitects/anki) | ~28.8k | Canonical SRS; the Again/Hard/Good/Easy grading affordance we copied. |
| [AnkiDroid](https://github.com/ankidroid/Anki-Android) | ~11.3k | Mobile SRS ergonomics, TTS-in-card, reminders. |
| [fsrs4anki / ts-fsrs](https://github.com/open-spaced-repetition/fsrs4anki) | ~4.0k | Modern open scheduler with a TS port that runs client-side (we adopted ts-fsrs). |
| **[kana-dojo](https://github.com/lingdojo/kana-dojo)** | **~2.8k** | **Frontend benchmark (=100):** best minimalist polish + theme + tight feedback loop, in the exact JP domain. |
| [wordpecker-app](https://github.com/baturyilmaz/wordpecker-app) | ~2.1k | LLM lessons; mock-vs-real API pattern. |
| [hi-kid](https://github.com/xiaochong/hi-kid) | ~1.0k | Highest-starred genuine AI speaking-partner with persona + voice loop. |
| [duolingo-clone (Lingo)](https://github.com/sanidhyy/duolingo-clone) | ~0.6k | Gamification inventory: hearts/XP/streak/quests/shop/tiers. |
| [ulangi](https://github.com/subconcept-labs/ulangi) | ~0.5k | Production-grade RN SRS; multi-mode review to fight fatigue. |

Anki/AnkiDroid have far more stars but are desktop-first utilitarian SRS
engines with no onboarding, no gamification, and no speaking loop, so they are
not the right FRONTEND benchmark for a mobile speaking app. kana-dojo sets the
polish bar in-domain and is the 100-point reference.

## Rubric (frontend; leader normalized to 100)

| Dimension | Weight | Leader | Our MVP (start) | After upgrade |
|---|---|---|---|---|
| Core speaking loop (TTS->shadow->STT) | 16 | 40 | 70 | TTS w/ persona voice, shadow, mock STT, accuracy ring, replay |
| Correction / diff feedback | 12 | 55 | 50 | token-level diff + accuracy + pitch-accent + correction cards |
| SRS review (grading + scheduling) | 12 | 45 | 45 | ts-fsrs scheduler + 4-button grading + interval preview + multi-mode |
| Onboarding / first-run | 9 | 70 | 45 | 4-step guided: partner -> level -> goal -> start |
| Progress / gamification / streak | 11 | 75 | 50 | XP/level, daily quests, badges, streak + streak-freeze |
| Persona / personalization | 10 | 30 | 75 | per-persona voice preset + identity color + sample + memory |
| Visual polish / motion | 11 | 95 | 50 | token theme + light/dark + entrance/press/spring motion + SVG rings |
| Accessibility | 5 | 50 | 35 | a11y labels/roles, reduced-motion honored, dynamic type |
| Offline / persistence | 6 | 55 | 45 | AsyncStorage for cards/streak/XP/settings/persona |
| i18n (KO UI for JP) | 4 | 50 | 55 | KO string table + furigana rendering |
| Settings depth | 4 | 60 | 40 | dark/motion/TTS-speed/daily-goal/review-cap/reminder/reset |

MVP weighted total vs leader=100: ~54.

## What we built to exceed the leader (all FRONTEND-only, contract-safe)

Every new capability stores data locally (AsyncStorage) or reuses an existing
API endpoint; no new backend, no contract change.

1. **ts-fsrs spaced repetition** — real open scheduler, per-card state persisted, 4-button grading with live next-interval previews (다시/어려움/알맞음/쉬움), due-count badges. (`src/srs.ts`)
2. **Theme system + motion** — light/dark tokens via `ThemeProvider`, entrance fades, press-springs, animated progress rings + XP bar (SVG). (`src/theme.ts`, `src/ThemeContext.tsx`, `src/components.tsx`)
3. **Correction craft** — LCS token diff + accuracy ring, plus Japanese **furigana** and **pitch-accent** contour. (`src/text.ts`, `Furigana`/`DiffText`/`PitchAccent`)
4. **Gamification** — XP/levels, daily quests, badges, streak + streak-freeze. (`src/gamification.ts`)
5. **Persona depth** — voice presets (rate/pitch), identity color, sample-voice button, lightweight memory. (`src/personaStyle.ts`)
6. **Guided onboarding** — partner -> level -> goal flow, gates the app on first run. (`OnboardingScreen`)
7. **Offline-first persistence** — all progress/cards/settings survive restart. (`src/storage.ts`)
8. **Multi-mode review** — shadow / listen / recall to fight fatigue.
9. **Settings depth, accessibility, KO i18n** — see rubric.

## Score
See `docs/frontend/SCORE_105.md` for the independent 3-judge re-score.
