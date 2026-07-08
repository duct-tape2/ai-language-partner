# Codex Backend Tasks

Status: implemented for local/mobile integration and re-audited on 2026-06-30. Not yet Duolingo-grade production backend.

## Phase 0 — 기존 결과물 감사

- Completed. Prior `src/ai_language_partner` SQLite/provider/safety ideas were salvaged into `apps/api/app`.

## Phase 1 — API 서버

- Completed with FastAPI.
- All 120 endpoints in `contracts/openapi_v0.yaml` are implemented with matching path names.
- Contract validation now fails on undocumented backend routes.

## Phase 2 — 저장소

- Completed with SQLite and `AI_LANGUAGE_PARTNER_DB_PATH` override.
- Conversation, Message, ReviewCard, Event, UsageRecord, and TTS cache entries are stored.
- Learner-scoped local/dev isolation added with `X-Learner-Id`.
- Hosted-style expiring v2 HMAC token mode added with `X-Learner-Token`.
- Password account/session auth added with register/login/OIDC ID-token login/OAuth PKCE/enterprise SSO discovery and PKCE handoff/refresh/me/logout, PBKDF2 hashes, hashed access/refresh tokens, refresh rotation, refresh-token reuse/replay detection, logout revoke, password change, optional device binding, account device registry/trust/revoke lifecycle, login failure throttling, registration throttling, client-level password-spray risk guard, and password/OIDC-confirmed account deletion.
- Device attestation now supports one-time HMAC signed challenges when configured, one-time RS256 public-key challenge proof-of-possession without a shared secret, and WebAuthn-style ES256 assertion verification with challenge/origin/RP ID/user-presence checks.
- OIDC ID-token login verifies provider allowlist, issuer, audience, expiry, nonce, and `email_verified`, with HS256 secret verification and RS256 JWKS public-key verification.
- Enterprise SSO stores admin-managed domain/redirect/provider connections, supports email-domain discovery, starts SSO PKCE requests bound to a connection id, and rejects callback claims whose email domain is outside that connection.
- Account access tokens are HS256-signed JWTs with issuer/audience/subject/jti/expiry claims; SQLite stores only token hashes for session lookup/revocation.
- Account session management now includes session inventory, remote session revoke, and logout-all.
- Privacy deletion now deletes only the selected learner scope.
- Privacy deletion audit target now stores a learner hash, not the raw learner id.
- Recommendations now include learner signal summary from corrections, lapse tags, recent rooms, completed rooms, and HLR-inspired memory summary.
- Review cards now include memory strength, difficulty, recall probability, recall risk, and tag-level mastery through `/v1/memory/summary`.
- Offline learner-memory train/evaluate now exists through `app/learner_model.py` and `scripts/evaluate_learner_model.py`, producing fixture/local DB evaluation metrics and coefficients while explicitly marking `productionTrained=false`.
- Offline reputation/anti-cheat train/evaluate now exists through `app/reputation_model.py` and `scripts/evaluate_reputation_model.py`, producing fixture/local DB reputation evaluation metrics and coefficients while explicitly marking `productionTrained=false`.
- Course catalog is stored as 2 courses, 10 units, 20 lessons, and 52 practice-room references.
- Content authoring/import/QA now has admin-gated validation, dry-run import, apply import, current stored quality report, translation memory list/suggest/upsert, bulk QA, version snapshot list/detail, branch/assignment tracking, content operation job queue, managed scheduler run history, editor submit-review, reviewer approve/reject, publisher publish-from-approved-snapshot, and release plan/canary metadata/due-worker/apply/rollback endpoints.
- Experiment/feature flag storage now has seeded running experiments, weighted variants, deterministic learner assignment, exposure logging, conversion/custom event logging, variant analytics, statistical testing, decision-readiness/significance guard, persisted decision proposal/apply workflow, publisher-gated winner rollout weight lock, admin-gated upsert/status controls, provider status flags, and privacy-delete cleanup.
- Gamification storage now has idempotent XP events, streak summary, daily quests, friend graph, friend invites, friend recommendations, social discovery, social privacy settings, social blocking, friend quests, reward currency ledger, operated reward shop pricing/policy/purchase limits, reward inventory, XP boost activation/application, multi-level achievement tracks, achievement gem rewards, league tier status, XP anomaly flags, boosted-XP abuse flags, duplicate-payload flags, leaderboard exclusion metadata, admin XP abuse review queue, multi-signal reputation profiles/review queue, offline reputation model evaluation evidence, weekly leaderboard, progress XP/quest fields, provider status flags, and privacy-delete cleanup.

## Phase 3 — providers

- Completed.
- Mock LLM/TTS/STT are split in `apps/api/app/providers.py`.
- TTS cache now stores content type and separates cache keys by provider.
- OpenAI-compatible LLM output is normalized, requires `schemaVersion=turn_payload_v1`, can request strict `json_schema` response format, and performs configurable structured-output repair attempts with default 2 and max 3.
- Rate limiting is split into a pluggable memory/Redis component with safe fallback.
- OpenAI STT adapter handles raw base64 and data URL audio payloads while preserving multipart content type and filename extension for MP3/M4A/WebM/WAV-style inputs.

## Phase 4 — tests

- Completed in `apps/api/tests/test_api_contract.py`.
- Added learner isolation, expiring token, account session hardening, OIDC ID-token login, OAuth authorization-code PKCE start/callback, enterprise SSO discovery/PKCE/domain enforcement, refresh-token reuse/replay detection, registration burst throttling, password-spray risk guard, account session inventory/remote revoke, account device registry/trust/revoke lifecycle, signed HMAC, RS256 public-key, and WebAuthn-style ES256 device-attestation challenge verification, admin audit-log, event-name validation, learner-aware rate-limit, LLM multi-repair/schemaVersion, recommendation signal, HLR-inspired memory summary, offline learner-memory model train/evaluate artifact coverage, course catalog, content authoring/import/QA/translation-memory/bulk-QA/branch-assignment/version publishing with role-based review/content operation jobs/managed scheduler run history/release due-worker/apply/rollback, experiment assignment/event logging/admin controls/variant analytics/statistical testing, gamified XP/streak/daily quest/friend graph/friend invite/friend recommendation/social discovery/privacy/blocking/friend quest/reward currency/reward shop/reward inventory/XP boost/achievement/league/anomaly/leaderboard/admin abuse review/multi-signal reputation coverage, STT media mapping, and contract-undocumented-route coverage.

## Phase 5 — handoff

- Completed.
- Claude mobile env: `EXPO_PUBLIC_USE_MOCK_API=false`, `EXPO_PUBLIC_API_BASE_URL=http://localhost:8000`.

## Remaining Production Gaps

- Upgrade the current OAuth/OIDC/enterprise SSO implementation with real Apple/Google and real enterprise IdP operation evidence, native Apple App Attest/Play Integrity production evidence and real platform-authenticator WebAuthn ceremony evidence beyond the current signed challenge HMAC, public-key challenge, and WebAuthn-style ES256 assertion proof, and production abuse-monitoring operations beyond the current login/register throttle, password-spray guard, OAuth/SSO PKCE state replay protection, refresh-token replay response, device revoke, and deterministic reputation profile.
- Replace mock/text-overlap pronunciation with a production speech scorer.
- Add real Redis distributed rate-limit smoke/load evidence.
- Upgrade content workflow into a full CMS with a dedicated UI, production-scale content operations evidence, release UI, and hosted scheduler/worker operations beyond the current backend content operation queue, managed scheduler run history, and release plan/due-worker/apply/rollback rail, and experiment analytics/decision UI beyond the current backend decision workflow; expand XP economy beyond the current friend graph/friend recommendation/social discovery/privacy/blocking/friend quest/operated reward shop/reward inventory/XP boost/multi-level achievement/achievement reward/abuse-review/multi-signal reputation/offline reputation model backend into production-scale learned anti-cheat/reputation automation; upgrade the offline learner-memory train/evaluate pipeline into a real trained/validated long-term learner model on production-scale history.
- Run real Docker build/run smoke on a machine with container runtime.
- Add real-key provider-native strict external LLM structured-output evidence.
- Run real-key STT/TTS/pronunciation media compatibility tests.
