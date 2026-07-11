# Contributing

AI Language Partner is a monorepo: a FastAPI backend (`apps/api`) and an
Expo / React Native app (`apps/mobile`), sharing a contract in `contracts/`
and a TypeScript fixture/type package in `packages/shared`.

The product rule that shapes everything: **no runtime LLM or external
generation API is called on the request path.** Every persona reply is
authored, reviewed, and voiced ahead of time into an offline **dialogue
bank** under `packs/`. Contributions must preserve that guarantee. See
`docs/ARCHITECTURE.md` for the rationale and full data flow.

New contributors can start with
`docs/community/FIRST_PR_WALKTHROUGH.md` and the GitHub issues labeled
`good first issue`. `docs/community/CONTRIBUTOR_LANDING.md` collects the
available routes, issue lanes, and maintainer contacts.

## Contributor trust and attribution

Normal GitHub authorship remains public in the repository history. Profile
spotlights, case studies, and any extra attribution require your opt-in; you
may decline without affecting review or merge decisions.

If you do not want to install Python, Node, Expo, or FastAPI locally, open the
repo in Codespaces:

`https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=1293331196`

Then use `docs/community/CODESPACES_FIRST_PR.md` for the shortest cloud setup
and check commands.

---

## Repository invariants

These are hard rules. A change that breaks one is not "done", regardless of
tests:

- **No runtime LLM / external generation calls.** Conversation replies come
  only from the pre-authored bank in `packs/`. The optional OpenAI-compatible
  LLM adapter in `apps/api/app/providers.py` exists for the legacy
  `POST /v1/conversations/{id}/turns` coaching surface, not for Daily Talk.
- **Persona voices go through the local engine** (AivisSpeech / VOICEVOX-compatible
  on `127.0.0.1:10101`). When the engine is down, the provider must fall back
  and **label the fallback honestly** in the `provider` field and in
  `/v1/providers/status` (e.g. `voicevox_compat_fallback_edge_tts`).
- **Do not cross the `apps/api` <-> `apps/mobile` boundary.** A contract change
  is edited in the OpenAPI contract and both clients/servers that consume it.
- **Definition of done is task-specific.** Docs-only wording reviews need no
  local setup. Pack `story.json` or `variants.csv` edits are checked by the
  `Dialogue Pack Sources` CI workflow for schema, stable IDs, references, and
  safety. Backend changes need the relevant `pytest` coverage; mobile changes
  need `npm run typecheck`. Full-stack changes must keep all affected checks
  green.
- Generated speech engines, generated clips, generated pack archives, local
  databases, and screenshots are not committed. Keep the public tree source-only.

---

## Prerequisites

| Tool | Version / note |
|---|---|
| Python | 3.9+ (`apps/api/pyproject.toml` sets `requires-python = ">=3.9"`) |
| Node.js | LTS; npm for the mobile workspace |
| Expo | SDK 52 (installed via `apps/mobile` deps; no global CLI needed) |
| ffmpeg | Only for local whisper.cpp STT (16 kHz mono normalization) |
| whisper.cpp | Optional, local STT engine |
| AivisSpeech / VOICEVOX | Optional, local TTS engine on `127.0.0.1:10101` |

Everything runs in **fully-local mock mode by default** — you do not need the
STT/TTS engines or any API key to develop or run the test suite.

## Codespaces setup

The repository includes `.devcontainer/devcontainer.json` for contributors who
want a cloud workspace. Codespaces installs Python 3.11, Node.js 20, backend
test dependencies, and mobile npm dependencies.

Quick checks inside Codespaces:

```bash
cd apps/api
.venv/bin/python -m pytest

cd ../mobile
npm run verify
```

See `docs/community/CODESPACES_FIRST_PR.md` for port forwarding and mock-mode
run commands.

---

## Backend setup (`apps/api`)

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`requirements.txt` pins: `fastapi`, `uvicorn[standard]`, `pydantic`,
`pytest`, `httpx`, `PyYAML`, `genanki`, `redis`, `edge-tts`,
`python-multipart>=0.0.9`.

Data persists in SQLite at `apps/api/data/language_partner.sqlite3`. Override
with `AI_LANGUAGE_PARTNER_DB_PATH`. Dev requests are scoped by the
`X-Learner-Id` header (default `local-dev`).

- **Do not kill the port-8000 demo server** — a public phone link is attached
  to it. Develop the backend on **port 8001**:
  ```bash
  uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001 --reload
  ```

### Running the local STT engine (whisper.cpp)

Mock STT is the default. To run real local STT:

```bash
# Verify binary + model + ffmpeg are present:
apps/api/scripts/setup_stt.sh

# Then start the backend with the whisper_cpp provider:
AI_LANGUAGE_PARTNER_STT_PROVIDER=whisper_cpp \
AI_LANGUAGE_PARTNER_WHISPER_CPP_BIN=/opt/homebrew/bin/whisper-cli \
AI_LANGUAGE_PARTNER_WHISPER_CPP_MODEL=~/whisper-models/ggml-medium.bin \
uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

`WhisperCppSTTProvider` transcodes uploaded audio to 16 kHz mono with ffmpeg,
runs whisper.cpp, and **falls back to the mock provider** (labeled
`whisper_cpp_fallback_mock`) if ffmpeg, the binary, or the model is missing.

### Running the local TTS voice engine (AivisSpeech / VOICEVOX-compatible)

```bash
# Probe the engine's /speakers endpoint:
./scripts/setup_voice_engine.sh

# Start the backend with the voicevox_compat provider (aivis or voicevox):
AI_LANGUAGE_PARTNER_TTS_PROVIDER=voicevox \
AI_LANGUAGE_PARTNER_VOICE_ENGINE_URL=http://127.0.0.1:10101 \
uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8001
```

`VoicevoxCompatTTSProvider` calls `/audio_query` + `/synthesis` on the engine,
resolves the speaker/style from `voice_catalog.json`, and **falls back to
edge-tts, then mock**, honestly labeling the result if the engine is down.
Confirm what is active:

```bash
curl http://localhost:8001/v1/providers/status
```

### Docker (optional)

```bash
cd apps/api
docker compose up --build   # persists SQLite in the ai_language_partner_api_data volume
```

---

## Mobile setup (`apps/mobile`)

```bash
cd apps/mobile
npm install
npm run start        # expo start (choose iOS / Android / Web)
npm run ios          # expo start --ios
npm run web          # expo start --web
```

The app runs against fixtures by default (`EXPO_PUBLIC_USE_MOCK_API` defaults
to mock — it is real only when explicitly set to `false`). To point the app at
a running backend:

```bash
EXPO_PUBLIC_USE_MOCK_API=false \
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000 \
npm run web
```

Env vars read by the client (`src/api/client.ts`):

| Var | Default | Meaning |
|---|---|---|
| `EXPO_PUBLIC_USE_MOCK_API` | mock (real only if `=false`) | fixture mode vs. live API |
| `EXPO_PUBLIC_API_BASE_URL` | `http://localhost:8000` | backend base URL |
| `EXPO_PUBLIC_LEARNER_ID` | `local-dev` | dev learner scope (`X-Learner-Id`) |

In mock mode the client returns fixtures immediately; in real mode it hits the
API and, for non-personal reads, falls back to a fixture so the UX never
dead-ends. Mutations flagged `noFallbackInReal` re-throw instead of faking
success.

---

## Running tests

### Backend

```bash
cd apps/api
.venv/bin/python -m pytest
```

The suite (`apps/api/tests/test_api_contract.py`) spins up the app with
`fastapi.testclient.TestClient`, validates routes against
`contracts/openapi_v0.yaml`, and exercises auth, providers, gamification, and
the dialogue-bank endpoints. It runs entirely in mock mode — no engines or
keys required.

Benchmark / readiness gate (part of "done"):

```bash
apps/api/.venv/bin/python apps/api/scripts/backend_benchmark_105.py
```

Dialogue-bank smoke:

```bash
apps/api/.venv/bin/python scripts/dialogue_smoke.py
```

### Mobile

```bash
cd apps/mobile
npm run typecheck        # tsc --noEmit; must report 0 errors
```

There is no runtime unit-test runner for the mobile app; **`tsc --noEmit` is
the gate.** Strict mode is on (`tsconfig.json`), and the shared package is
type-checked together via the `@shared/*` path alias.

---

## Code layout

```
ai-language-partner/
├── apps/
│   ├── api/                       FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py            create_app() — all @api.get/@api.post routes, ~6.9k lines
│   │   │   ├── dialogue_match.py  DialogueMatcher (STT text -> candidate lineId)
│   │   │   ├── providers.py       LLM/TTS/STT/pronunciation adapters + fallback chains
│   │   │   ├── store.py           SQLite persistence (ApiStore)
│   │   │   ├── seed.py            course/practice-room/persona seed data
│   │   │   ├── learner_model.py   offline FSRS/memory model (readiness evidence)
│   │   │   ├── reputation_model.py XP-abuse / reputation model
│   │   │   ├── safety.py          text guardrails
│   │   │   ├── rate_limit.py      in-memory / redis rate limiter
│   │   │   ├── voice_catalog.json 31-voice catalog
│   │   │   └── persona_voices.json 8 personas -> voice/emotion map
│   │   ├── scripts/               benchmark, readiness verifiers, importers
│   │   └── tests/test_api_contract.py
│   ├── mobile/                    Expo SDK 52 app
│   │   ├── App.tsx                screen switch + 5-tab bottom bar
│   │   └── src/
│   │       ├── store.ts           useApp() controller, Screen union, navigation
│   │       ├── api/client.ts      one request() helper, mock fallbacks, API_BASE
│   │       ├── dialogue/          Daily Talk engine (types/packManager/runner/audioQueue/matchMock)
│   │       ├── screens/           one <XScreen> per Screen value + index.ts barrel
│   │       └── <module>/          co-located data for each learning screen (kanji/, grammar/, ...)
├── packages/shared/src/           shared TS types + fixtures (imported by mobile)
├── contracts/                     openapi_v0.yaml + events.yaml (source of truth)
├── authoring/                     offline dialogue-bank authoring pipeline
├── packs/{persona}/{version}/     sample dialogue source (story.json + manifest.json + variants.csv)
└── docs/                          backend/ + frontend/ deep docs; ARCHITECTURE.md
```

---

## The dialogue-bank pack format

A pack lives at `packs/{personaId}/{packVersion}/` (e.g. `packs/yui/v2/`) and
is served zip-only at `GET /v1/dialogue/packs/{personaId}/{packVersion}.zip`.
Each pack directory contains:

| File | Schema | Purpose |
|---|---|---|
| `story.json` | `dialogue_bank_story_v1` | the node graph the runner walks |
| `manifest.json` | `dialogue_bank_manifest_v1` | audio index + pack metadata |
| `variants.csv` | — | accepted STT paraphrases per `lineId` (match input) |
| `embeddings.npy` | float32 `(variantCount, 16)` | offline deterministic hash embeddings |
| `audio/*.wav` | — | one pre-synthesized clip per `lineId` |
| `pack.zip` | — | prebuilt archive of the above (served directly) |

### `story.json` — `dialogue_bank_story_v1` (node graph, NOT ink)

The shipped story format is a **scenario/node graph**, not ink. `.ink` files
under `authoring/scenarios/` are a human-readable authoring *export view*
(generated by `scenario_to_ink`); the canonical shipped artifact is
`story.json`.

```jsonc
{
  "schemaVersion": "dialogue_bank_story_v1",
  "personaId": "yui",
  "packVersion": "v1",
  "scenarios": [
    {
      "scenarioId": "yui_greetings_intro_n5",
      "personaId": "yui", "packVersion": "v1",
      "topicId": "greetings_intro", "title": "인사·자기소개", "level": "N5",
      "nodes": [
        {
          "nodeId": "yui_greetings_intro_n5_node_01",
          "assistantLineId": "yui_greetings_intro_n5_a01",   // -> audio/<lineId>.wav
          "assistantText": "まずは自然にあいさつしましょう。",
          "assistantKo": "먼저 자연스럽게 인사해요.",
          "choices": [
            { "lineId": "yui_greetings_intro_n5_u01a", "text": "こんにちは",
              "ko": "안녕하세요", "nextNodeId": "yui_greetings_intro_n5_node_02" }
          ]
        }
      ]
    }
  ]
}
```

The mobile `DialogueRunner` (`src/dialogue/runner.ts`) starts at the first
node, emits the persona line + audio, offers each choice's `text` as a
suggested-reply chip, sends the choices' `lineId`s as match candidates, and on
a match advances to that choice's `nextNodeId` (a node with no choices ends the
scenario). The server stays stateless; the runner owns conversation state.

### `manifest.json` — `dialogue_bank_manifest_v1`

```jsonc
{
  "schemaVersion": "dialogue_bank_manifest_v1",
  "personaId": "yui", "packVersion": "v1",
  "runtimeLlmCalls": false,
  "ttsProvider": "local_mock_prebuilt", "voiceUsed": "voicevox_metan_normal",
  "topics": ["food_order", "greetings_intro", "hobbies", "today", "weather_seasons"],
  "levels": ["N5", "N4"],
  "scenarioCount": 10, "lineCount": 75, "audioCount": 75, "variantCount": 960,
  "audio":    [{ "lineId": "...", "path": "audio/....wav", "category": "dialogue" }],
  "filler":   [ /* same shape, category: "filler"   */ ],
  "confirm":  [ /* same shape, category: "confirm"  */ ],
  "fallback": [ /* same shape, category: "fallback" */ ]
}
```

The client indexes every entry across all four category arrays by `lineId`
(`buildAudioIndex` in `packManager.ts`), so any line the runner or matcher
names can be played. Categories:

- `dialogue` — persona/choice lines in the story graph.
- `filler` — short backchannels while waiting.
- `confirm` — played on a `confirm`-tier match (0.55–0.75 score).
- `fallback` — played when nothing matches (< 0.55).

### Matching

`POST /v1/dialogue/match` (`DialogueMatcher` in `dialogue_match.py`) normalizes
the STT text and scores it against `variants.csv` rows (per `lineId`
paraphrases). The **shipped runtime matcher is lexical** — the `describe()`
method reports `matcherModel: "lexical_ngram_fallback"` (char bigrams +
`SequenceMatcher` ratio + substring boost). `embeddings.npy` is shipped for an
optional embedding path gated by
`AI_LANGUAGE_PARTNER_DIALOGUE_EMBEDDING_MODEL`. Tiers:

| Score | Tier | Behavior |
|---|---|---|
| `>= 0.75` | `match` | accept `matchedLineId`, advance |
| `0.55–0.75` | `confirm` | ask to confirm via `confirmLineId` |
| `< 0.55` | `fallback` | play a fallback line |

Thresholds are env-overridable (`AI_LANGUAGE_PARTNER_DIALOGUE_MATCH_THRESHOLD`,
`..._CONFIRM_THRESHOLD`). Global intents (`repeat` / `hint` / `quit` / `slow`,
JP + KR patterns) short-circuit matching. Missed utterances are logged via
`POST /v1/dialogue/unmatched` and later folded back into the bank by
`authoring/weekly_expand.py`.

### Regenerating a pack (offline pipeline)

```bash
python3 authoring/generate_seed_bank.py     # authoring/scenarios -> packs/{p}/v1 source files
python3 authoring/validate_bank.py          # structural + safety validation
python3 authoring/batch_tts.py --persona yui --dry-run   # batch-synthesize real audio into a new pack version
```

Generated clips, embeddings, and archives are release assets, not source
files. Run `validate_bank.py` before committing any pack source change.

---

## Commit / PR conventions

- Branch off `main`; do not commit directly to `main`.
- Commit subjects use a `type: summary` prefix, matching existing history:
  `docs:`, `chore:`, `feat:`, `fix:` (e.g. `docs: clarify local STT setup`).
- Keep the backend/frontend boundary intact in a single PR. A contract change
  must touch `contracts/openapi_v0.yaml` and the affected backend/mobile types.
- A PR is mergeable only when the definition of done holds: backend `pytest`
  green, `backend_benchmark_105.py` passing, and mobile `npm run typecheck` at
  0 errors.
- ASCII-only in code and commit messages; straight quotes and plain hyphens.

---

## Adding a new learning screen

Learning screens are plain function components switched on a `Screen`
string-union — the app does **not** use react-navigation. To add one
(example: a screen keyed `"idioms"`), touch these five places:

**1. Data module** — co-locate the screen's content under `src/`:

```
apps/mobile/src/idioms/idiomsData.ts     // export the typed data array
```

**2. Screen component** — `src/screens/IdiomsScreen.tsx`, following the
existing signature (single `app` prop):

```tsx
import type { AppController } from '../store';
import { IDIOMS } from '../idioms/idiomsData';

export function IdiomsScreen({ app }: { app: AppController }) {
  // ... render; use app.navigate(...), app.track(...), useTheme()
}
```

**3. `store.ts`** — add the key to both the `Screen` union and the runtime
`SCREENS` array (the array gates the `?screen=` deep-link):

```ts
export type Screen = /* ... */ | 'idioms';
const SCREENS: Screen[] = [ /* ... */, 'idioms'];
```

**4. `screens/index.ts`** — re-export it from the barrel:

```ts
export { IdiomsScreen } from './IdiomsScreen';
```

**5. `App.tsx`** — import it in the `screens` import block and add its render
branch alongside the others:

```tsx
{screen === 'idioms' && <IdiomsScreen app={app} />}
```

**6. Entry point** — add a tile to `src/screens/PracticeHubScreen.tsx` so users
can reach it:

```ts
{ key: 'idioms', icon: '💡', label: '관용구', desc: '자주 쓰는 관용 표현',
  onPress: () => app.navigate('idioms') },
```

(The 5-tab bottom bar in `App.tsx` is reserved for Home / Practice / Review /
Progress / Settings; new modules are reached through the Practice Hub, not the
tab bar.)

Run `npm run typecheck` — the `Screen` union makes the compiler flag any place
you missed.
