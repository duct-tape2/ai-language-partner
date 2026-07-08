# Competitive GitHub Research — Backend 105 Plan

Date: 2026-06-29

Scope: backend-only research and implementation plan for `AI Language Partner Mobile`.

## Search Method

Searched GitHub repository search/API for these clusters:

```text
topic:language-learning
"duolingo clone"
"language learning" "TTS"
"language learning" "ChatGPT"
"speaking practice" "language"
"Japanese learning" "AI"
```

Excluded pure awesome-lists, static resource lists, and unrelated AI lists from the primary benchmark. Kept direct or adjacent products that ship a learner-facing app, platform, or local learning engine.

## Benchmark Table

| Repo | Stars | Why It Matters | Backend-Relevant Strength |
|---|---:|---|---|
| [mengxi-ream/read-frog](https://github.com/mengxi-ream/read-frog) | 8,217 | Top star actual language-learning app found | AI translation, article analysis, multi-model support, TTS, browser extension distribution |
| [umlx5h/LLPlayer](https://github.com/umlx5h/LLPlayer) | 3,867 | Strong AI immersion/video learner tool | Whisper ASR, OCR, real-time translation, LLM context translation, media pipeline |
| [lingdojo/kana-dojo](https://github.com/lingdojo/kana-dojo) | 2,774 | Japanese Duolingo/Monkeytype-style benchmark | Japanese drills, streaks, achievements, progress tracking, strong contributor story |
| [kantord/LibreLingo](https://github.com/kantord/LibreLingo) | 2,625 | Classic open-source language platform | Course model, spaced repetition, lightweight web app, AGPL/open learning stance |
| [LuteOrg/lute-v3](https://github.com/LuteOrg/lute-v3) | 1,477 | Reading-first language acquisition tool | Python backend, text learning workflow |
| [ripose-jp/Memento](https://github.com/ripose-jp/Memento) | 1,447 | Japanese media mining benchmark | Anki card creation, Japanese dictionary/subtitle workflows |
| [simjanos-dev/LinguaCafe](https://github.com/simjanos-dev/LinguaCafe) | 1,405 | Self-hosted reading/vocab platform | Multi-language dictionary, review, self-hosting |
| [asbplayer/asbplayer](https://github.com/asbplayer/asbplayer) | 1,307 | Subtitle mining benchmark | Multimedia flashcards, Anki/WaniKani sync-style workflow |
| [echo-loop/Echo-Loop](https://github.com/echo-loop/Echo-Loop) | 1,132 | Closest voice-learning app pattern | AI translation/parsing, audio import, AI subtitles, read-aloud scoring, flashcard review |
| [sanidhyy/duolingo-clone](https://github.com/sanidhyy/duolingo-clone) | 584 | Highest star direct Duolingo clone found | Lesson/game app pattern; less voice/backend differentiated |
| [m98/fluent](https://github.com/m98/fluent) | 214 | AI language learning kit | Spaced repetition, adaptive tutor concept, progress tracking |
| [JavaFXpert/talk-with-gpt3](https://github.com/JavaFXpert/talk-with-gpt3) | 129 | Earlier AI speaking practice app | BYOK LLM, speech-to-text, TTS, speaking avatar |
| [adrianhajdin/react-native-lingua](https://github.com/adrianhajdin/react-native-lingua) | 92 | Mobile AI voice teacher reference | Expo app, real-time AI voice teacher, auth/analytics stack |
| [ArtCC/freelingo](https://github.com/ArtCC/freelingo) | 44 | Low-star but very direct open-core competitor | CEFR plan, SM-2, hosted/self-hosted split, TTS caching, XP/streak |
| [ayameira/nihongo-dojo](https://github.com/ayameira/nihongo-dojo) | 13 | Very direct Japanese AI tutor | FastAPI, long-term memory, Anki sync, JLPT grammar, TTS, cost tracking |

Star counts were captured from GitHub API during this session. They will drift over time.

## 100-Point Baseline

For broad GitHub attention, `read-frog` is the star leader and gets the nominal 100.

For our actual product category, the real combined baseline is:

```text
read-frog attention/distribution
+ LLPlayer/Echo-Loop audio intelligence
+ kana-dojo Japanese polish/gamification
+ LibreLingo open-source learning credibility
+ nihongo-dojo direct Japanese AI tutor depth
```

So “105” cannot mean only more endpoints. It needs backend proof that our mobile app can support:

```text
AI conversation
TTS/STT without keys in mock mode
usage/cost visibility
SRS review
pronunciation feedback
profile-aware recommendations
Anki/export workflow
open-core provider boundary
Japanese/Korean learner-specific correction
```

## Gap Map Before This Pass

Already present:

- Contract-matching mobile API.
- Mock LLM/TTS/STT.
- SQLite conversations/messages/review cards/events/usage.
- `tired_today` vertical slice.
- Safety guardrails.

Missing versus top competitors:

- SM-2/SRS grading and due queue.
- Pronunciation/read-aloud scoring.
- Learner profile and recommendation engine.
- Anki-style export path.
- Provider/cost status endpoint for open-core transparency.
- Usage summary endpoint.

## Implemented Backend 105 Lift

Added these backend-only capabilities:

```text
GET  /v1/profile/me
PUT  /v1/profile/me
GET  /v1/recommendations/today
GET  /v1/review-cards/due
POST /v1/review-cards/{reviewCardId}/grade
POST /v1/pronunciation/score
GET  /v1/export/anki
GET  /v1/export/anki-apkg
POST /v1/export/anki-connect
GET  /v1/grammar/jlpt
GET  /v1/mistakes/korean-patterns
GET  /v1/weaknesses/summary
GET  /v1/providers/status
GET  /v1/usage/summary
```

Also enhanced audio/mock-audio conversation turns with a `pronunciation` object when the learner speaks.

## Backend 105 Scorecard

| Capability | Best observed competitor pattern | Current backend status |
|---|---|---|
| Open-source mock mode | FreeLingo/Nihongo Dojo local-first/BYOK | Implemented: no external key required |
| TTS/STT adapters | LLPlayer/Echo-Loop/talk-with-gpt3 | Implemented mock split; replaceable providers |
| TTS cache and usage | FreeLingo/Nihongo Dojo | Implemented SQLite cache and usage summary |
| SRS review | LibreLingo/FreeLingo/fluent | Implemented SM-2-style grading and due queue |
| Speaking/pronunciation feedback | Echo-Loop/react-native-lingua | Implemented mock scorer and audio-turn scoring |
| Profile-aware learning | FreeLingo/Nihongo Dojo/fluent | Implemented learner profile and recommendation endpoint |
| Japanese/Korean specificity | kana-dojo/Nihongo Dojo, but not Korean-first | Implemented Korean learner correction in `tired_today` |
| Anki/export flow | Memento/asbplayer/Nihongo Dojo | Implemented CSV export, real `.apkg` export, and AnkiConnect dry-run/apply payload |
| Open-core boundary | FreeLingo/open-core strategy | Implemented provider status with public/private boundary |
| Provider adapters | talk-with-gpt3/Nihongo Dojo/FreeLingo | Implemented env-driven OpenAI-compatible LLM, OpenAI/ElevenLabs TTS, OpenAI STT adapters with mock fallback |
| JLPT grammar depth | Nihongo Dojo/kana-dojo | Implemented seed JLPT grammar bank, Korean mistake catalog, and weakness-driven grammar recommendation |
| Self-hosting | FreeLingo/LinguaCafe | Implemented Dockerfile and docker-compose for backend |
| Public proof | Top repos show clear demo/readme signals | Implemented reproducible OpenAPI, Docker artifact, benchmark, and learner-model evaluation evidence |

Backend-only conclusion: after this pass, our backend is not more popular than the top repos, but it has a more complete mobile-AI-Japanese backend surface than the direct open-source comparables found in this search.

## Remaining To Reach Stronger Than 105

These are not done yet and should stay on the goal backlog:

- True audio pronunciation model instead of text-overlap mock scoring.
- Larger JLPT grammar and Korean mistake catalog.
- Public benchmark demo script and README badges.
