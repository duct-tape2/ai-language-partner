# Architecture

AI Language Partner teaches Japanese to Korean speakers through a
**pre-authored dialogue bank** instead of a runtime language model. The learner
speaks; the app recognizes the speech locally, matches it against the expected
lines of the current scene, and plays a **pre-synthesized native-quality voice
clip** in reply. No LLM runs at request time.

This document covers the design rationale, the offline authoring pipeline, the
runtime data flow, the API contract, the provider fallback chains, the cost
model, and the mobile module map. It is written against the actual source
(`apps/api/app/*.py`, `apps/mobile/src/dialogue/*`, `authoring/*`, `packs/*`);
where the code and older prose disagree, the code wins and the note says so.

---

## 1. Zero-runtime-LLM design rationale

The product owner ruled out runtime LLM / external generation calls for three
reasons, encoded as a repo invariant in `AGENTS.md`:

1. **Cost** — a per-turn LLM+TTS call has a nonzero marginal cost that scales
   with users. The bank pays its generation cost **once, offline**, so the
   marginal cost of a conversation turn at runtime is effectively **zero**
   (STT + a string match).
2. **Maintainability** — replies are fixed artifacts on disk, versioned in
   `packs/`. There is no prompt to tune, no model drift, no provider outage on
   the conversation path.
3. **Quality control** — every persona utterance is authored and human-reviewed
   before shipping, so there is **zero hallucination** and every line is
   native-review quality. `manifest.json` records `runtimeLlmCalls: false` and
   `DialogueMatcher.describe()` reports `runtimeLlmCalls: False` as machine-
   checkable evidence.

Consequences that ripple through the design:

- **The client owns conversation state.** Because the reply for any node is
  known ahead of time, the mobile `DialogueRunner` tracks the current
  scenario/node; the server only needs to answer "does this utterance match one
  of these candidate line IDs?" This keeps the backend **stateless per match
  request** and horizontally scalable.
- **The UI can show suggested-reply chips.** The set of things a learner *can*
  say at a node is exactly the node's `choices`, so beginners never freeze —
  and if the mic is denied, the same chips power a **chip-only** fallback mode.
- **Latency is bounded and small.** A turn is STT + a lexical match + playing a
  local clip — sub-second, no network round-trip to a model provider.

> The legacy `POST /v1/conversations/{id}/turns` coaching endpoint *can* use an
> optional OpenAI-compatible LLM adapter (structured `turn_payload_v1` output
> with JSON-schema repair). That is a separate, opt-in surface — it is **not**
> on the Daily Talk dialogue-bank path and defaults to a deterministic mock.

---

## 2. Offline dialogue-bank pipeline (authoring)

The pipeline runs **off the request path** and produces the `packs/` artifacts.
It is a node-graph story compile + variant expansion + hash embeddings + batch
TTS + zip — **not** ink.

```
authoring/scenarios/{persona}/*.ink        (human-readable authoring export view,
                                             #line: / #ko: annotated; the node graph
                                             is the source of truth in generate_seed_bank.py)
        │
        ▼
authoring/generate_seed_bank.py
   ├─ build node-graph scenarios (persona × topic × JLPT level)
   ├─ expand_variants(text, ko) → accepted STT paraphrases per lineId
   │        (drop josa/です/ます, add "。", KR forms, kanji→kana, pad to 8–10)
   ├─ embedding_for(text, size=16) → deterministic SHA-256 hash embedding, L2-normalized
   ├─ write_wav(...) → placeholder mock audio (one clip per lineId)
   └─ emit per pack: story.json, manifest.json, variants.csv, embeddings.npy,
                     audio/*.wav, pack.zip
        │
        ▼
authoring/validate_bank.py     structural + safety.assess_text() validation (gate)
        │
        ▼
authoring/batch_tts.py         replace mock audio with REAL synthesis from the local
                               voice engine (/audio_query + /synthesis), copy embeddings
                               forward, rebuild manifest + pack.zip into a new packVersion
        │
        ▼
packs/{persona}/{version}/     shipped pack (served by the API, downloaded by the app)
        ▲
        │
authoring/weekly_expand.py     reads POST /v1/dialogue/unmatched rows from SQLite and
                               proposes new variants to fold back into the bank
```

Key facts, verified in source:

- **`embeddings.npy` is a deterministic hash embedding**, not a neural model
  output: `embedding_for` takes `sha256(text)`, maps the first 16 bytes to
  `[-1, 1]`, and L2-normalizes. Shape is `(variantCount, 16)` (e.g. `(960, 16)`
  for a seed pack). It is written by the authoring step and copied forward by
  `batch_tts.py`; the shipped runtime matcher does not require it (see §5).
- **Seed pack scale (`authoring/seed_bank_summary.json`):** 3 seed personas
  (`yui`, `haruka`, `ren`) × 10 scenarios = 30 scenarios, 960 variants each
  (2880 total), 75 audio clips each (225 total). `packs/` also ships `v2` per
  persona (the `batch_tts` output version); the app auto-selects the highest
  `packVersion` per persona.
- **`.ink` files are an export view**, produced by `scenario_to_ink` from the
  node graph for human readability and validated for `#line:`/`#ko:`
  annotations. The runtime never parses ink; `story.json` is canonical.

---

## 3. Runtime data flow (STT → match → pre-synth audio)

One Daily Talk turn:

```
 mobile: DailyTalkScreen + DialogueRunner            apps/api (FastAPI, stateless match)
 ───────────────────────────────────────            ─────────────────────────────────
 1. runner.current() → persona line + choices
 2. audioQueue.play(persona clip)  ── uri from pack.audioBytes[lineId] (expo-av)
                                       └─ fixture (uri=null) → device TTS (expo-speech)
 3. show choices as suggested-reply chips
 4. user taps mic → record 16 kHz mono ──(multipart /v1/stt/transcribe)──▶ whisper.cpp
                                                                    ◀── { text, confidence }
 5. POST /v1/dialogue/match { personaId, packVersion,
        utterance: text, candidateLineIds: node.choices[].lineId,
        globalIntents: true }                        ──▶ DialogueMatcher.match()
                                                          normalize → score vs variants.csv
                                                     ◀── { tier, matchedLineId, score,
                                                           confirmLineId, globalIntent }
 6. tier === 'match'   → runner.choose(matched) → advance to nextNodeId, play its clip
    tier === 'confirm' → play confirmLineId clip, ask to confirm
    tier === 'fallback'→ play a random fallback-category clip;
                         POST /v1/dialogue/unmatched (fire-and-forget, 202)
    globalIntent       → repeat / hint / quit / slow handled client-side
 7. barge-in: a new user turn calls audioQueue.cancel() (token-scoped) to stop playback
 8. AsyncStorage snapshot { scenarioId, nodeId } lets the learner resume mid-dialogue
```

Notes tied to source:

- **Pack delivery is zip-only.** There is no per-file route; the app downloads
  `GET /v1/dialogue/packs/{personaId}/{packVersion}.zip` and unzips it in-app
  with **fflate `unzipSync`** (Expo managed has no native unzip; fflate's async
  path is Web-Worker-backed and Workers do not exist on Hermes, so the unzip is
  synchronous behind a one-time spinner). See `packManager.ts`.
- **Audio is materialized lazily.** `playableUri` writes each clip's bytes to
  the cache dir (native) or an object URL (web), cached by
  `{persona}_{version}_{lineId}`; the cache is cleared when a new pack loads.
- **Mock mode** loads a bundled fixture pack with `audioBytes: null`, so every
  line is spoken by device TTS and the client-side `matchMock` (bigram Dice)
  stands in for the server matcher — the full flow is demoable with no backend.

---

## 4. API contract (dialogue-bank + core surface)

Routes are registered as `@api.get` / `@api.post` inside
`create_app()` in `apps/api/app/main.py`; the module-level `app = create_app()`
is what `uvicorn app.main:app` serves. The contract is pinned in
`contracts/openapi_v0.yaml` and asserted by `tests/test_api_contract.py`.

Dialogue-bank + conversation surface:

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/dialogue/match` | STT text → `{ tier, matchedLineId, score, confirmLineId, globalIntent, latencyMs }` |
| GET | `/v1/dialogue/packs` | list packs (bare array: persona, version, sizeBytes, topics, levels, counts) |
| GET | `/v1/dialogue/packs/{personaId}/{packVersion}.zip` | download the pack zip (path-traversal guarded) |
| POST | `/v1/dialogue/unmatched` | log a missed utterance (202) for `weekly_expand.py` |
| POST | `/v1/stt/transcribe` | multipart or JSON → `{ text, provider, confidence, latencyMs }` |
| POST | `/v1/tts/synthesize` | text → audio (data URI / base64) + `voiceUsed`, `provider` |
| GET | `/v1/voices` | 31-voice catalog (voiceId, engine, character/style, sampleUrl, creditText) |
| GET | `/v1/voices/samples/{voiceId}.wav` | voice preview clip |
| POST | `/v1/pronunciation/score` | expected vs actual text → score/rating/feedback |
| POST | `/v1/conversations` / `…/{id}/turns` | legacy LLM-coaching surface (optional adapter) |
| GET | `/v1/providers/status` | active LLM/TTS/STT/pronunciation/matcher + fallbacks |
| GET | `/health` | liveness |

Supporting surface (also in `main.py`, same contract): personas, practice-rooms,
courses, review-cards (FSRS) + `/due` + `/grade`, progress, gamification /
friends / rewards / achievements / leagues / leaderboards, auth (register /
login / OIDC / OAuth-PKCE / refresh / devices+attestation / sessions), content
pipeline (validate / import / versions / releases / scheduler / jobs),
experiments, exports (Anki / apkg / anki-connect), usage / audit-log / privacy /
events, and admin HTML consoles.

Request/response shapes for the dialogue surface are mirrored in
`apps/mobile/src/dialogue/types.ts` (verified against the backend + on-disk
packs).

---

## 5. Provider fallback chains

All providers live in `apps/api/app/providers.py`. `build_provider_stack()`
selects each from env vars; every real adapter subclasses its Mock and **falls
back to a labeled mock on any failure**, so the request never hard-fails and
`/v1/providers/status` always reports the honest active provider.

### TTS (`_build_tts`)

Selected by `AI_LANGUAGE_PARTNER_TTS_PROVIDER`:

```
voicevox / aivis / voicevox_compat
   → VoicevoxCompatTTSProvider  (local engine /audio_query + /synthesis)
        └─(engine down / speaker unmatched)→ EdgeTTSProvider("ja-JP-NanamiNeural")
              └─(edge-tts fails)→ MockTTSProvider
        provider label on fallback: "voicevox_compat_fallback_<inner>"

openai        → OpenAITTSProvider     ─(fail)→ MockTTSProvider   ("openai_tts_fallback_mock")
elevenlabs    → ElevenLabsTTSProvider ─(fail)→ MockTTSProvider   ("elevenlabs_tts_fallback_mock")
edge          → EdgeTTSProvider       ─(fail)→ MockTTSProvider   ("edge_tts_fallback_mock")
(default)     → MockTTSProvider       (synthesizes a deterministic tone WAV)
```

The primary local path is **aivis / voicevox_compat → edge → mock**, matching
the README and the setup script's honesty guarantee.

### STT (`_build_stt`)

Selected by `AI_LANGUAGE_PARTNER_STT_PROVIDER`:

```
whisper / whisper_cpp
   → WhisperCppSTTProvider  (ffmpeg 16 kHz mono → whisper.cpp -otxt)
        └─(no audio / ffmpeg missing / binary|model missing / empty text)→ MockSTTProvider
        provider label on fallback: "whisper_cpp_fallback_mock"

openai     → OpenAISTTProvider ─(fail / no audio)→ MockSTTProvider ("openai_stt_fallback_mock")
(default)  → MockSTTProvider   (returns a fixed transcript, confidence 0.92)
```

The primary local path is **whisper_cpp → mock**.

### LLM (legacy coaching only) and pronunciation

```
LLM (_build_llm):  openai / openai_compatible + key → OpenAICompatibleLLMProvider
                     ─(request fail or schema-invalid after repair attempts)→ MockLLMProvider
                   (default) → MockLLMProvider          # NOT on the dialogue-bank path

Pronunciation (_build_pronunciation):
   acoustic_feature_mock (default) → AcousticFeaturePronunciationScorer
        ─(no/invalid audio)→ text-overlap fallback scoring
   mock / text_mock → MockPronunciationScorer
```

---

## 6. Scaling & cost logic

The economics follow directly from §1.

| Cost | Where it is paid | Marginal cost per conversation turn |
|---|---|---|
| Reply generation (authoring + review) | offline, once per pack | 0 |
| TTS synthesis of persona lines | offline batch (`batch_tts.py`), once | 0 |
| STT of the learner's audio | runtime, **local** whisper.cpp | ~0 (own compute) |
| Match | runtime, in-process lexical scoring | ~0 (no model call) |
| Playback | runtime, local pre-synth clip | 0 |

- **Per-turn external API cost is 0** in the default and local-engine
  configurations — the whole point of the design. `manifest.json.runtimeLlmCalls`
  and the matcher's `runtimeLlmCalls: false` are the machine-checkable claim.
- **Backend scales horizontally.** The match endpoint is stateless (state lives
  in the client's `DialogueRunner`); `DialogueMatcher` caches parsed
  `variants.csv` per `(persona, version)` in-process. SQLite holds
  learner-scoped data; hosted deployments swap in the redis rate limiter
  (`rate_limit.py`) and token/JWT auth mode.
- **The runtime matcher is lexical, not embedding-based.**
  `DialogueMatcher.describe()` reports `matcherModel: "lexical_ngram_fallback"`
  (NFKC normalize + josa/です/ます stripping, char bigrams, `SequenceMatcher`
  ratio, substring boost). `embeddings.npy` ships for an optional embedding
  path gated by `AI_LANGUAGE_PARTNER_DIALOGUE_EMBEDDING_MODEL`; when that env is
  unset (the default), matching stays pure-lexical and needs no model. Do not
  claim embedding inference runs by default — it does not.
- Thresholds and fallback labels are the levers, not model size: tune
  `AI_LANGUAGE_PARTNER_DIALOGUE_MATCH_THRESHOLD` / `..._CONFIRM_THRESHOLD`
  rather than swapping models.

---

## 7. Mobile module map

`apps/mobile` is a plain string-union router (no react-navigation): `store.ts`
holds the `Screen` union and current screen; `App.tsx` renders
`screen === 'x' && <XScreen app={app} />` and a 5-tab bottom bar.

```
apps/mobile/
├── App.tsx                          screen switch + 5-tab bar (Home/Practice/Review/Progress/Settings)
└── src/
    ├── store.ts                     useApp() → AppController: Screen union, SCREENS[],
    │                                navigate/track, gamification/SRS/practice state, persistence
    ├── api/
    │   ├── client.ts                one request() helper; API_BASE / USE_MOCK / LEARNER_ID;
    │   │                            mock fixtures; synthesizePersona; multipart transcribeAudioFile
    │   └── auth.ts                  device-key / token auth helpers
    ├── dialogue/                    ── Daily Talk engine (the dialogue bank) ──
    │   ├── types.ts                 pack/story/manifest/match/voice contract types
    │   ├── packManager.ts           list/load packs (zip download + fflate unzip), audio cache
    │   ├── runner.ts                DialogueRunner — walks the story_v1 node graph, owns state
    │   ├── audioQueue.ts            serialized playback, token-scoped cancel (barge-in), TTS fallback
    │   └── matchMock.ts             client-side match stub for mock mode (bigram Dice + global intents)
    ├── screens/                     one <XScreen> per Screen value + index.ts barrel
    │   ├── DailyTalkScreen.tsx      the dialogue-bank UI (setup → active → summary)
    │   ├── VoiceGalleryScreen.tsx   31-voice catalog preview
    │   └── … (kanji, grammar, vocab, kana, conjugation, counters, keigo, pitch,
    │          numbers, exam, placement, reading, listening, shadowing, roleplay,
    │          mistakes, pronunciation, mastery, situations, home, personas, …)
    ├── <module>/                    co-located data for each learning screen
    │   (kana/, kanji/, grammar/, vocab/, counters/, conjugation/, numbers/,
    │    keigo/, pitch/, pitfalls/, reading/, mistakes/, mastery/, situations/,
    │    shadowing/, exam/ …)
    ├── crypto/ (deviceKey, hmacSha256)   device attestation client
    ├── characters/ (Mascot, PoseSheet)   persona art
    ├── components.tsx / theme.ts / ThemeContext.tsx / i18n.ts / labels.ts   UI kit + i18n
    ├── srs.ts / gamification.ts / coaching.ts / personaStyle.ts             domain logic
    └── storage.ts / services.ts / devConfig.ts                             persistence + config

packages/shared/src/                 shared TS types + fixtures, imported via @shared/*
```

The dialogue-bank feature is the `src/dialogue/*` cluster plus
`DailyTalkScreen`; every other screen is a self-contained learning module with
a co-located data file, reached from `PracticeHubScreen`. To add one, see
**Adding a new learning screen** in `CONTRIBUTING.md`.
