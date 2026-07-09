# AI Language Partner — Japanese for Korean Learners

**Speak Japanese with a persona partner that answers like a real person — zero runtime LLM calls, all voices local.**

> 한국인 일본어 학습자를 위한 회화 앱 — 런타임 LLM 없이 사전 저작 대화은행 + 로컬 STT/TTS로 진짜 사람처럼 바로 대답합니다.

[![Repo Hygiene](https://github.com/duct-tape2/ai-language-partner/actions/workflows/repo-hygiene.yml/badge.svg)](https://github.com/duct-tape2/ai-language-partner/actions/workflows/repo-hygiene.yml)
[![Mobile Verify](https://github.com/duct-tape2/ai-language-partner/actions/workflows/mobile-verify.yml/badge.svg)](https://github.com/duct-tape2/ai-language-partner/actions/workflows/mobile-verify.yml)
[![API Docker Smoke](https://github.com/duct-tape2/ai-language-partner/actions/workflows/api-docker-smoke.yml/badge.svg)](https://github.com/duct-tape2/ai-language-partner/actions/workflows/api-docker-smoke.yml)

[Contributor page](https://duct-tape2.github.io/ai-language-partner/) ·
[Hosted web demo](https://duct-tape2.github.io/ai-language-partner/demo/) ·
[Call for contributors](https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html) ·
[Contributor discussion](https://github.com/duct-tape2/ai-language-partner/discussions/55) ·
[한국어](https://duct-tape2.github.io/ai-language-partner/ko/) ·
[日本語](https://duct-tape2.github.io/ai-language-partner/ja/) ·
[First issue matcher](docs/community/FIRST_ISSUE_MATCHER.md) ·
[Five-minute first PR](docs/community/FIVE_MINUTE_FIRST_PR.md) ·
[Starter issue index](docs/community/STARTER_ISSUE_INDEX.md) ·
[No-install first PRs](docs/community/NO_INSTALL_FIRST_PRS.md) ·
[First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53) ·
[Web demo release](https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09) ·
[Demo/release plan](docs/community/INSTALLABLE_DEMO_RELEASE_PLAN.md)

---

## Community sprint: first PRs welcome

This repo is building a real public contribution record for the Claude for OSS
community-builder route. Current evidence status is tracked in
[`docs/CLAUDE_FOR_OSS_APPLICATION.md`](docs/CLAUDE_FOR_OSS_APPLICATION.md):
only useful external PRs count, and maintainer PRs, bots, duplicate identities,
and metric-only changes are excluded.

| Lane | Best first link | Useful PR shape |
|---|---|---|
| Korean/Japanese docs | [docs good first issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22+label%3Adocs) | clearer setup notes, learner-facing Korean explanations |
| Japanese naturalness | [language-review issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22language-review%22) | beginner-safe dialogue wording, tone review |
| Dialogue content | [content issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Acontent) | reviewed `story.json` / `variants.csv` improvements |
| Mobile accessibility | [accessibility issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Aaccessibility) | labels, touch targets, contrast, layout fixes |
| Backend/API docs | [backend docs issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Abackend+label%3Adocs) | OpenAPI examples, local STT/TTS setup notes |
| Tests/tooling | [tests issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Atests) | small fixture tests or verification scripts |

Start with the [call for contributors](docs/community/CALL_FOR_CONTRIBUTORS.md),
the [first issue matcher](docs/community/FIRST_ISSUE_MATCHER.md),
the [five-minute first PR route](docs/community/FIVE_MINUTE_FIRST_PR.md),
the [starter issue index](docs/community/STARTER_ISSUE_INDEX.md),
the [no-install first PR board](docs/community/NO_INSTALL_FIRST_PRS.md),
the [contributor landing page](docs/community/CONTRIBUTOR_LANDING.md), the
[first PR walkthrough](docs/community/FIRST_PR_WALKTHROUGH.md), or the
[20 contributor sprint kickoff issue](https://github.com/duct-tape2/ai-language-partner/issues/52).
If you want a maintainer to suggest a task, ask in the
[First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53) or open a
[contributor interest issue](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml).

---

## Public OSS snapshot

This repository is the clean public source tree. It intentionally does **not**
vendor local speech engines, generated voice clips, generated zip packs,
SQLite files, simulator screenshots, or internal handoff notes. Those are
operator- or release-generated assets, not source code.

The tracked sample packs contain `story.json`, `manifest.json`, and
`variants.csv` so contributors can review dialogue structure and run backend
tests without large binary assets.

The first generated web demo artifact is published as a GitHub prerelease:
[`demo-web-2026-07-09`](https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09).
It is a downloadable Expo web build snapshot for contributors and directory
reviewers, not an app-store release.

A hosted mock-mode web demo is also available at
[`https://duct-tape2.github.io/ai-language-partner/demo/`](https://duct-tape2.github.io/ai-language-partner/demo/).
It runs from the public Pages tree, uses fixture-backed providers, and does not
require private API keys or local speech engines.

---

## Contribution guardrails

Useful first contributions include Korean/Japanese documentation fixes, JLPT
sample-content review, accessibility labels, OpenAPI examples, local STT/TTS
setup notes, and focused test fixtures.

Generated audio, local engines, SQLite files, private notes, screenshots, and
large binary packs should stay out of Git. The public repo is source-only so a
fresh clone can review, test, and contribute without private assets.

---

## One-line pitch

A React Native / Expo app + FastAPI backend that teaches Japanese to Korean speakers through a **pre-authored dialogue bank**: your speech is recognized locally (whisper.cpp), matched against the expected lines of the current scene, and answered instantly with **pre-synthesized native-quality voice** from a local TTS engine (AivisSpeech / VOICEVOX-compatible). No LLM runs at request time — every persona line was authored, reviewed, and voiced ahead of time, so responses are sub-second, always native-quality, and cost nothing per turn.

## The concept — why no runtime LLM

The product owner ruled out runtime LLM/API calls for three reasons: **cost, maintainability, and quality control**. Instead of generating replies on the fly, the system authors every persona utterance in advance, batch-synthesizes it to audio, and at runtime only does three cheap things:

1. **STT** — transcribe the learner's recording (local whisper.cpp).
2. **Match** — compare the transcription against the candidate lines of the current dialogue node.
3. **Play** — return the matching pre-synthesized audio clip.

Because the app holds the conversation state (which scene/node the learner is in) and the server is a thin STT + match layer, the backend scales to many concurrent users. The learner-facing UX wins: replies land in **under a second**, dialogue is always native-review quality (zero hallucination), and the UI can show **suggested-reply chips** — the things you *can* say in the current scene — so beginners never freeze up.

**What the learner gets**
- Pre-authored, native-reviewed **dialogue bank** across persona × topic × JLPT level.
- **Local whisper.cpp STT** (ggml-medium, Metal/CPU, ffmpeg 16 kHz normalization) — no cloud STT.
- **Local AivisSpeech / VOICEVOX-compatible TTS**, a **31-voice catalog**, **8 personas** with per-persona emotion styles.
- **FSRS** spaced repetition for review cards.
- **JLPT N4 content**: 570 items imported into courses / units / lessons / 622 practice rooms.
- **30+ learning screens**: kanji, grammar, vocab, kana chart, conjugation, counters, keigo, pitch accent, numbers/time, mock exam, placement test, reading, listening dictation, shadowing, and the new **Daily Talk** + **Voice Gallery** screens.

---

## Architecture — dialogue-bank runtime

```
                        AI LANGUAGE PARTNER — dialogue-bank runtime (no runtime LLM)

  ┌──────────────────────────── apps/mobile (Expo SDK 52, iOS / Android / Web) ────────────────────────────┐
  │                                                                                                          │
  │   DailyTalkScreen ──> dialogue/packManager  (GET packs, download {p}/{v}.zip, fflate unzip,             │
  │        │                                       audio index over dialogue|filler|confirm|fallback)        │
  │        │                                                                                                 │
  │        ├──> dialogue/runner  (node-graph walker: persona line -> user turn -> candidate lineIds)         │
  │        │                                                                                                 │
  │        ├──> record 16kHz mono ──(multipart)──────────────┐                                               │
  │        │                                                 │                                               │
  │        ├──> dialogue/audioQueue  (serialized play,       │   suggested-reply chips (chip-only mode)      │
  │        │      token cancel, barge-in, next-node preload) │                                               │
  │        └──> AsyncStorage snapshot (resume mid-dialogue)  │                                               │
  └─────────────────────────────────────────────────────────┼───────────────────────────────────────────────┘
                                                             │  HTTP (EXPO_PUBLIC_API_BASE_URL, X-Learner-Id)
                                                             ▼
  ┌──────────────────────────────────── apps/api (FastAPI, Python) ─────────────────────────────────────────┐
  │                                                                                                           │
  │   POST /v1/stt/transcribe ──> whisper.cpp (ggml-medium)  ──text──┐                                        │
  │                                                                  │                                        │
  │   POST /v1/dialogue/match ──> normalize + embedding cosine top-k │                                        │
  │        thresholds:  >=0.75 match | 0.55–0.75 confirm | <0.55 fallback | globalIntent repeat/hint/quit/slow│
  │                                                                  │                                        │
  │   GET  /v1/dialogue/packs, /v1/dialogue/packs/{p}/{v}.zip  <─────┘   (manifest.json + story.json + audio) │
  │   POST /v1/tts/synthesize, GET /v1/voices, GET /v1/voices/samples/{id}.wav                                │
  │        │                                                                                                  │
  │        ▼                                                                                                  │
  │   AivisSpeech / VOICEVOX-compatible engine  (local HTTP :10101, LGPL, SEPARATE PROCESS)                   │
  │        provider = voicevox_compat | aivis_speech_engine   (honest fallback label when engine is down)     │
  │                                                                                                           │
  │   SQLite (apps/api/data/language_partner.sqlite3): personas, courses, practice-rooms,                     │
  │        review-cards (FSRS), gamification, progress, auth/devices, experiments, content pipeline           │
  └───────────────────────────────────────────────────────────────────────────────────────────────────────┘

  Pre-authoring pipeline (offline, not on the request path):
    authoring/scenarios  ──>  packs/{persona}/{v}/{story.json, manifest.json, audio/*.wav, embeddings.npy}
```

The dialogue pack shipped on disk uses a **node-graph** story format (not ink). Each scenario has nodes with an `assistantLineId` + choices; each choice carries a `lineId` used as a match candidate. The manifest groups clips into `audio`, `filler`, `confirm`, and `fallback` categories.

---

## Features

| Area | What ships |
|---|---|
| Daily Talk (conversation) | Voice-recognized turns, 3-tier match/confirm/fallback UX, global intents (repeat/hint/quit/slow), barge-in, suggested-reply chips, chip-only fallback when mic is denied, session summary with streak/XP + review-card save |
| Voice Gallery | 31-voice catalog with character/style names, tap-to-preview samples, per-persona preview showing `voiceUsed`, credit text shown (license obligation) |
| Personas | 8 personas (yui, haruka, ren, akari, takeshi, sachiko, kota, shiro) with per-persona emotion styles (default/gentle/happy/excited/whisper/confirm/fallback) |
| Spaced repetition | FSRS review cards (`ts-fsrs` on client, FSRS scheduling on server) |
| JLPT N4 | 570 items imported into courses/units/lessons and 622 practice rooms |
| Explicit study modules | Kanji, grammar, vocab decks, kana chart, conjugation, counters, keigo, pitch accent, numbers/time |
| Assessment | Mock exam, placement test |
| Skills practice | Listening dictation, dialogue shadowing, roleplay, word bank, story reading |
| Gamification | Streaks, XP, leagues, achievements/badges, quests, gem shop |
| Habit loop | Home "today" mission, onboarding, progress analytics |
| Honesty | Mock/demo state is labeled in-UI; TTS falls back to an honest `voicevox_compat_fallback_*` label when the local engine is not running |

---

## Tech stack

| Layer | Stack |
|---|---|
| Mobile | React Native 0.76.9, Expo SDK 52.0.47, React 18.3.1, TypeScript 5.3 |
| Mobile audio/files | expo-av (record/play), expo-file-system (pack cache), fflate (zip unpack), expo-speech (device-TTS fallback), @react-native-async-storage/async-storage |
| SRS | ts-fsrs 5.4.1 |
| Backend | FastAPI, Uvicorn, Pydantic, PyYAML, python-multipart, genanki, redis (optional rate limit), edge-tts (optional provider) |
| STT (local) | whisper.cpp (ggml-medium), ffmpeg |
| TTS (local) | AivisSpeech / VOICEVOX-compatible engine over local HTTP |
| Match | text normalization + embedding cosine top-k |
| Storage | Runtime-created SQLite database, ignored by Git |
| Tests | pytest (API contract), tsc `--noEmit` (mobile typecheck) |

Navigation is **not** react-navigation — the app uses a `Screen` string-union state in `apps/mobile/src/store.ts` and renders `screen === 'x' && <XScreen/>` branches in `App.tsx`, with a 5-tab bottom bar (Home / Practice / Review / Progress / Settings).

---

## Monorepo layout

```
ai-language-partner/
├── apps/
│   ├── api/                         FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py              routes (health + /v1/*), ~6,900 lines
│   │   │   ├── providers.py         STT/TTS/pronunciation provider stack, voice catalog
│   │   │   ├── dialogue_match.py    DialogueMatcher, pack listing
│   │   │   ├── store.py             SQLite ApiStore
│   │   │   ├── seed.py              content seeding
│   │   │   ├── learner_model.py / reputation_model.py  offline models
│   │   │   ├── rate_limit.py, safety.py
│   │   │   ├── voice_catalog.json   31-voice catalog
│   │   │   └── persona_voices.json  8 personas × emotion styles
│   │   ├── scripts/                 setup_stt.sh, setup_voice_engine.sh, import_jlpt_pack.py, ...
│   │   ├── tests/test_api_contract.py   54 pytest cases
│   │   └── requirements.txt
│   └── mobile/                      React Native / Expo app
│       ├── App.tsx                  screen router + tab bar
│       ├── app.json                 Expo config ("AI 일본어 친구")
│       ├── src/
│       │   ├── screens/             30+ screens (index.ts registry)
│       │   ├── dialogue/            packManager, runner, audioQueue, matchMock, types
│       │   ├── api/                 client.ts (API_BASE, mock fallback, multipart upload)
│       │   ├── store.ts             app state, Screen union, tracking
│       │   ├── components.tsx       shared UI incl. FuriganaTokens
│       │   ├── i18n.ts, theme.ts, srs.ts, gamification.ts, ...
│       │   └── characters/          persona pose sheets
│       └── package.json
├── packages/shared/src/             shared TS types + fixtures
├── contracts/                       openapi_v0.yaml, events.yaml, API contract README
├── packs/{persona}/{v}/             sample dialogue source (story.json, manifest.json, variants.csv)
├── authoring/                       scenario authoring + weekly reports
├── docs/                            backend + frontend docs
└── scripts/                         repo-level scripts
```

---

## How to run

### 1. Backend (FastAPI)

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# health check:
curl http://localhost:8000/health   # -> {"ok": true, "projectId": "..."}
```

The backend runs standalone with mock providers; STT and TTS return honest fallback labels until the local engines are up.

### 2. Local STT engine (whisper.cpp)

```bash
# Install whisper.cpp + ffmpeg, and fetch the ggml-medium model.
# Then verify the environment:
bash apps/api/scripts/setup_stt.sh
# Configure (defaults shown):
export AI_LANGUAGE_PARTNER_STT_PROVIDER=whisper_cpp
export AI_LANGUAGE_PARTNER_WHISPER_CPP_BIN=/opt/homebrew/bin/whisper-cli
export AI_LANGUAGE_PARTNER_WHISPER_CPP_MODEL=$HOME/whisper-models/ggml-medium.bin
```

`setup_stt.sh` prints JSON and exits non-zero if the binary, model, or ffmpeg is missing.

### 3. Local TTS engine (AivisSpeech / VOICEVOX-compatible)

```bash
# Start AivisSpeech or VOICEVOX so it serves /speakers on 127.0.0.1:10101, then:
bash apps/api/scripts/setup_voice_engine.sh
export AI_LANGUAGE_PARTNER_VOICE_ENGINE_URL=http://127.0.0.1:10101
```

If the engine is not running, `/v1/tts/synthesize` honestly returns `voicevox_compat_fallback_*` instead of pretending to have produced a real voice.

### 4. Mobile (Expo)

```bash
cd apps/mobile
npm install
# Point at the backend and turn off mock mode to hit the real API:
export EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
export EXPO_PUBLIC_USE_MOCK_API=false      # default is mock mode
npm run start        # or: npm run ios | npm run android | npm run web
```

Client defaults: `API_BASE = http://localhost:8000`, mock mode ON unless `EXPO_PUBLIC_USE_MOCK_API=false`, learner scoping via the `X-Learner-Id` header. In mock mode every endpoint has a local fallback so the app is fully explorable with no backend.

---

## Testing

| Suite | Command | Result |
|---|---|---|
| Backend contract | `cd apps/api && python -m pytest` | Runs in mock mode; no speech engines or API keys required |
| Mobile verify | `cd apps/mobile && npm run verify` | TypeScript + frontend regression checks |
| Docker smoke | GitHub Action `API Docker Smoke` | Validates the backend container path |
| Secret/binary scan | See `docs/CLAUDE_FOR_OSS_APPLICATION.md` | Confirms generated/private assets are not tracked |

---

## API contract summary

Base URL defaults to `http://localhost:8000`. Learner scoping via `X-Learner-Id`. Full spec: `contracts/openapi_v0.yaml`; event names: `contracts/events.yaml`.

**Dialogue bank**
- `GET /v1/dialogue/packs` → bare array `[{personaId, packVersion, sizeBytes, topics, levels, scenarioCount, lineCount, audioCount}]`
- `GET /v1/dialogue/packs/{personaId}/{packVersion}.zip` → generated zip response from the tracked pack source
- `POST /v1/dialogue/match` → `{tier, matchedLineId, score, confirmLineId, globalIntent, latencyMs}` (thresholds 0.75 / 0.55; globalIntent ∈ repeat|hint|quit|slow|null)
- `POST /v1/dialogue/unmatched` → logs unmatched utterances for weekly bank expansion

**Voice / speech**
- `GET /v1/voices` → bare array of 31 `{voiceId, engine, characterName, styleName, sampleUrl, personaId, creditText}`
- `GET /v1/voices/samples/{voiceId}.wav`
- `POST /v1/tts/synthesize` → `{audioUrl, audioBase64, provider, voiceUsed, ...}`
- `POST /v1/stt/transcribe` (multipart: `file`, `language`, `hintLineIds[]`) → `{text, provider, confidence, latencyMs}`

**Everything else** (~140 `/v1/*` routes total): `GET /health`, `/v1/personas`, `/v1/practice-rooms`, `/v1/courses`, `/v1/review-cards` (+ `/due`, `/{id}/grade`), `/v1/gamification/me`, `/v1/reputation/me`, `/v1/progress`, `/v1/friends/*`, `/v1/achievements/me`, `/v1/leagues/me`, `/v1/entitlements/me`, auth/devices/sessions under `/v1/auth/*`, content pipeline under `/v1/content/*`, and A/B experiments under `/v1/experiments/*`.

---

## Data structure

**Dialogue pack source** (`packs/{persona}/{v}/`):

```
packs/{personaId}/{packVersion}/
├── story.json        dialogue_bank_story_v1:
│                       { scenarios: [ { topicId, level,
│                           nodes: [ { nodeId, assistantLineId, assistantText, assistantKo,
│                                       choices: [ { lineId, text, ko, nextNodeId } ] } ] } ] }
├── manifest.json     dialogue_bank_manifest_v1:
│                       { audio[], filler[], confirm[], fallback[] }
│                       each entry: { lineId, path, category, text, voiceUsed? }
└── variants.csv      accepted learner utterance variants for matching
```

Generated clips, embeddings, and bundled pack archives are intentionally not
tracked in this public source tree. Operators can regenerate or host them as
release assets when they run a real voice pipeline.

- **Personas** (`apps/api/app/persona_voices.json`): 8 personas, each with emotion styles (default/gentle/happy/excited/whisper/confirm/fallback) mapping to catalog voices.
- **Voice catalog** (`apps/api/app/voice_catalog.json`): 31 voices with engine, character/style names, sample paths, and credit text.
- **Relational data**: SQLite is created locally at runtime and is not committed.
- **Shared types** (`packages/shared/src/types.ts`) and mobile-side pack types (`apps/mobile/src/dialogue/types.ts`).

---

## Licensing note

The application code (this repo) is separate from the **local voice engines**. AivisSpeech / VOICEVOX-compatible engines are **LGPL** and run as a **separate process** over local HTTP (`127.0.0.1:10101`) — they are not linked into or bundled with this codebase. Each voice in `/v1/voices` carries a **`creditText`** field that the mobile UI is required to display (Voice Gallery and persona preview) to honor per-voice attribution obligations. whisper.cpp and ggml models are installed by the operator, not vendored here.

---

## Roadmap

Self-assessment against popular apps (Duolingo / LingoDeer / Renshuu / Busuu) and top-starred repos (Anki) currently sits around **55/100**, up from a 41 baseline. Highest-impact remaining work, roughly in order:

1. **Kanji module** — stroke order + radicals (deepen beyond current kanji screen).
2. **Explicit grammar explanations** — richer teaching content per grammar point.
3. **JLPT / exam prep** — expand mock exams beyond N4; more levels of content.
4. **Monetization** — entitlements and pricing surfaces.
5. **Content volume & course completion** — more scenarios, topics, and packs per persona.
6. **Social features** — currently skeleton; make friends/leagues real.
7. **Onboarding placement test** — expand the lightweight placement flow.

**Operational follow-ups**: rebuild/restart the public demo server to serve the current backend; confirm on-device mic permissions (Expo config) on a real device; keep the demo (`8000`) build in sync with the latest backend. See the [installable demo release plan](docs/community/INSTALLABLE_DEMO_RELEASE_PLAN.md) for the public demo and app-store-readiness gates.

---

Concept, backend contract, and current status are documented in `docs/ARCHITECTURE.md`, `apps/api/README.md`, and `contracts/openapi_v0.yaml`.
