# Cold Backend Review — Duolingo/GitHub 기준

Date: 2026-06-29

이 문서는 점수를 매기지 않는다. 현재 백엔드가 Duolingo 1위 제품 기준과 공개 GitHub 레퍼런스 기준에서 어디까지 왔고, 어디가 아직 약한지만 냉정하게 정리한다.

## 비교 기준

- Duolingo는 2026년 1분기 기준 56.5M DAU와 12.5M paid subscribers를 공시한 대규모 학습 서비스다. 따라서 단순 API 동작보다 사용자 격리, 장기 학습 데이터, 운영 안정성, 실험/텔레메트리, 콘텐츠 품질 관리가 핵심이다. Source: [Duolingo Q1 2026 10-Q](https://investors.duolingo.com/static-files/37b98739-93ae-4b0e-b38b-ec1fcb8d6c49)
- Duolingo는 Q1 2026에 language course skill 20,500개를 발행했다고 밝힌다. 현재 2개 course/10개 unit/20개 lesson/52개 practice room은 prototype으로는 의미 있지만, Duolingo급 콘텐츠 운영과 비교하면 아직 시작점이다. Source: [Duolingo Company Strategy Overview](https://investors.duolingo.com/company-strategy-overview-0)
- Duolingo는 제품 개선을 대규모 실험 운영으로 밀어붙인다. 공식 strategy overview 기준으로 분기당 1,000개 이상 A/B 테스트를 운영한다고 설명하므로, 언어 앱 백엔드도 feature flag, learner-stable assignment, exposure/conversion logging이 최소 운영 뼈대에 들어가야 한다. Source: [Duolingo Company Strategy Overview](https://investors.duolingo.com/company-strategy-overview-0)
- Duolingo는 XP, streak, Daily Quests, Friends Quest, XP Boost, weekly Leaderboards를 학습 동기화의 핵심 루프로 쓴다. 공식 블로그는 lesson/practice/story/timed challenge 완료로 XP를 얻고 주간 leaderboard에서 경쟁한다고 설명하며, streak는 하루 한 lesson으로 연장되는 habit mechanic으로 분리했다. Source: [Duolingo 101](https://blog.duolingo.com/duolingo-101-how-to-learn-a-language-on-duolingo/), [Improving the streak](https://blog.duolingo.com/improving-the-streak/), [Leaderboards and Leagues](https://blog.duolingo.com/duolingo-leagues-leaderboards/)
- Duolingo Max는 Roleplay, Video Call처럼 AI 대화 경험을 제품화했다. Video Call은 실제 대화형 연습, 속도 조절/반복 요청, 저압박 말하기 환경을 내세운다. Source: [Duolingo Video Call](https://blog.duolingo.com/video-call/), [Duolingo Max](https://blog.duolingo.com/duolingo-max/)
- Duolingo의 개인화 방향은 Birdbrain 같은 학습자 모델에 기대고, 반복학습 역시 중요한 제품 원리로 다룬다. Source: [Birdbrain](https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain/), [Spaced repetition](https://blog.duolingo.com/spaced-repetition-for-learning/)
- Duolingo가 공개한 half-life regression(HLR)은 단순 SRS보다 진전된 recall prediction 모델이다. 이 백엔드는 HLR-inspired local estimator와 이번 루프에서 추가한 offline logistic learner-memory train/evaluate artifact를 갖췄지만, Duolingo처럼 대규모 실제 학습 이력으로 훈련된 운영 모델은 아니다. Source: [duolingo/halflife-regression](https://github.com/duolingo/halflife-regression), [Duolingo Research](https://research.duolingo.com/)
- 공개 GitHub 비교군은 `LibreLingo`, `Echo-Loop`, `kana-dojo`, `read-frog`, `LLPlayer`, `Anki` 계열이다. 이들은 각각 SRS, 읽기/미디어 학습, AI 음성/자막, self-hosting, Anki export 같은 강점을 가진다.

## 현재 백엔드의 강점

- FastAPI + SQLite로 모바일 API를 바로 실행할 수 있다.
- mock LLM/TTS/STT가 있어 외부 키 없이 vertical slice를 돌릴 수 있다.
- `tired_today` 대화 흐름, TTS, mock STT, 교정, 리뷰카드, 진행률까지 이어진다.
- SRS due queue/grading, Anki CSV/APKG/AnkiConnect export, 2개 course/10개 unit/20개 lesson/52개 practice room, content authoring/import/QA/version snapshot/role-based review/publish/translation memory/bulk QA/branching assignment/content operation queue/managed scheduler run history/release plan/canary metadata/due-worker/apply/rollback API, learner-stable experiment assignment/exposure/conversion logging/variant analytics/statistical testing, XP ledger/streak/daily quest/friend graph/friend invite/friend recommendation/social discovery/social privacy/blocking/friend quest/reward currency ledger/reward shop/reward inventory/XP boost/multi-level achievement/achievement reward/league tier/anomaly flag/leaderboard exclusion/admin abuse review/multi-signal reputation review/offline reputation model evaluation/weekly leaderboard, HS256/RS256-JWKS OIDC-compatible identity token login, OAuth PKCE, enterprise SSO connection discovery/PKCE handoff, account device registry/trust/revoke lifecycle, JLPT grammar, Korean mistake catalog, provider status, usage summary가 있다.
- 이번 수정으로 `X-Learner-Id` 기반 learner scope가 들어갔다. 대화, 리뷰카드, 사용량, TTS 캐시, 이벤트, 프로필, 추천, 삭제가 같은 learner 기준으로 묶인다.
- 이번 수정으로 확장 엔드포인트 120개가 OpenAPI 계약에 올라갔고, 계약에 없는 백엔드 라우트가 있으면 검증이 실패한다.
- 이번 수정으로 이벤트 이름을 `contracts/events.yaml` 허용 목록으로 검증한다.
- 이번 수정으로 TTS cache가 content type과 provider별 cache key를 갖는다.
- 이번 수정으로 audit log는 admin key 없이 열리지 않는다.
- 이번 수정으로 OpenAI-compatible LLM adapter가 JSON 응답을 파싱해 `assistantText`, `spokenText`, `suggestedUserReply`, `corrections`, `reviewCards`를 구조적으로 반영한다.
- 이번 수정으로 hosted/token mode에서는 HMAC 서명된 `X-Learner-Token`이 없으면 learner scope를 선택할 수 없게 했다.
- 이번 수정으로 privacy delete audit target은 원문 learner id가 아니라 hash로 남는다.
- 이번 수정으로 기본 admin key fallback은 dev mode에서만 동작한다.
- 이번 추가 루프로 rate limiter를 middleware 내부 dict에서 `rate_limit.py`의 pluggable limiter로 분리했다. 기본은 memory, `AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND=redis` 설정 시 Redis adapter를 시도하고 실패하면 secret을 노출하지 않는 memory fallback으로 내려온다.
- 이번 추가 루프로 OpenAI-compatible LLM adapter가 structured output을 정규화하고, 필수 필드 누락 시 repair prompt를 보낸 뒤 실패하면 mock fallback으로 내려온다.
- 이번 추가 루프로 practice room seed를 초기 2개에서 현재 52개로 늘렸다. 약속, 사과, 요청, 컨디션, 직장, 쉐도잉, 여행/체류 survival 등 모바일 루틴에서 반복 가능한 표현군이 생겼다.
- 이번 추가 루프로 HMAC learner token을 무기한 `v1`에서 만료 시간이 있는 `v2_expiring_hmac`로 바꿨다. Legacy `v1` token은 명시 env 없이 거부된다.
- 이번 추가 루프로 rate limit key가 localhost/IP만 보지 않고 learner hint도 포함한다. 로컬/프록시 환경에서 서로 다른 learner가 같은 IP 때문에 즉시 충돌하는 문제를 줄였다.
- 이번 추가 루프로 추천 응답에 `signalSummary`를 추가했다. 최근 교정 category, review lapse tag, 최근 practice room, 오늘 완료 room을 추천 점수에 반영한다.
- 이번 추가 루프로 OpenAI STT adapter가 raw base64와 `data:audio/...;base64,` 입력을 처리하고, MP3/WebM/M4A/WAV content type에 맞는 multipart filename/content-type을 보내도록 고쳤다.
- 이번 추가 루프로 `/v1/courses`와 `/v1/courses/{courseId}`를 추가하고, 52개 practice room을 2개 course/10개 unit/20개 lesson에 매핑했다.
- 이번 추가 루프로 `/v1/content/validate`, `/v1/content/import`, `/v1/content/quality-report`를 추가했다. Admin key가 필요하고, content bundle의 중복 ID, 누락 필드, 알 수 없는 persona, 누락 room ref, 중복 placement, orphan room, existing ID conflict를 구조화된 오류로 리포트한다. Import는 dry-run이 기본이며 apply 시 course tree 기준 room metadata를 주입한다.
- 이번 추가 루프로 `/v1/content/versions`, `/v1/content/versions/{versionId}`, `/v1/content/versions/{versionId}/publish`를 추가했다. Dry-run/apply import는 콘텐츠 버전 스냅샷을 남기고, 저장된 스냅샷은 admin publish로 현재 course/practice-room 저장소에 다시 적용되며 audit log에 생성/게시 이벤트가 남는다.
- 이번 추가 루프로 `/v1/content/versions/{versionId}/submit-review`, `/v1/content/versions/{versionId}/approve`, `/v1/content/versions/{versionId}/reject`를 추가했다. `X-Admin-Role`의 editor/reviewer/publisher 역할을 구분하고, draft snapshot은 reviewer 승인 없이는 publish되지 않는다. 같은 submitter가 reviewer로 자기 승인하는 경로도 409로 막고 audit log에 제출/승인/반려를 남긴다.
- 이번 추가 루프로 `/v1/content/translation-memory`, `/v1/content/translation-memory/suggest`, `/v1/content/bulk-qa`를 추가했다. Seed practice room의 한국어 원문/일본어 문장을 translation memory로 자동 적재하고, editor upsert, viewer/reviewer/publisher 조회·제안, 현재/버전/요청 bundle bulk QA, 동일 한국어 원문에 다른 일본어 번역이 붙은 conflict warning을 테스트와 benchmark로 잠갔다.
- 이번 추가 루프로 `/v1/content/versions/{versionId}/branch`, `/v1/content/versions/{versionId}/assign`, `/v1/content/assignments`, `/v1/content/assignments/{assignmentId}/status`를 추가했다. 저장된 content version에서 draft branch를 만들고, assignee/priority/due date/status를 붙여 editor/reviewer workflow와 audit log로 추적할 수 있다.
- 이번 추가 루프로 `/v1/content/releases`, `/v1/content/releases/{releaseId}/apply`, `/v1/content/releases/{releaseId}/rollback`을 추가했다. 승인된 content version으로 release plan을 만들고, scheduled/canary metadata와 quality guardrail snapshot을 저장하며, publisher만 live catalog에 적용하거나 직전 published snapshot으로 rollback할 수 있다. Tests와 benchmark는 unapproved release 409, viewer create 403, future schedule apply 409, publisher-only apply, live catalog 변경, rollback 복구, audit log를 확인한다.
- 이번 추가 루프로 OpenAI-compatible LLM 응답에 `schemaVersion=turn_payload_v1`을 요구하고, 선택 strict `json_schema` response format mode와 회귀 테스트를 추가했다.
- 이번 추가 루프로 외부 LLM structured output repair 정책을 기본 2회, 최대 3회로 명확히 하고, 두 번째 repair에서 정상 payload가 돌아오는 경로를 테스트와 benchmark artifact로 잠갔다.
- 이번 추가 루프로 STT multipart 업로드의 M4A/WebM filename/content-type 매핑도 테스트로 잠갔다.
- 이번 추가 루프로 password account/session auth를 추가했다. register/login/refresh/me/logout, PBKDF2 password hash, hashed access/refresh session token, bearer-token learner scoping, refresh token rotation, logout revoke를 테스트로 잠갔다.
- 이번 추가 루프로 password lifecycle과 계정 폐쇄 흐름을 보강했다. password change는 현재 비밀번호를 요구하고 기존 세션을 revoke하며, account deletion은 비밀번호 재인증 뒤 learner-scoped privacy delete와 account disable/session revoke를 수행한다. 선택적 `deviceId` binding과 로그인 실패 throttle도 테스트로 잠갔다.
- 이번 추가 루프로 refresh token 재사용/replay 감지를 추가했다. 이미 rotate되어 revoke된 refresh token이 다시 제출되면 계정 전체 세션을 revoke하고 `auth_refresh_reuse_detected` audit event를 남긴다.
- 이번 추가 루프로 가입 폭주 throttle을 추가했다. `auth_attempts`에 `purpose`를 분리해 login 실패 throttle과 registration throttle이 서로 오염되지 않게 하고, 같은 email/client hash에서 window 기준 과도한 계정 생성 시 429와 `auth_registration_throttled` audit event를 남긴다.
- 이번 추가 루프로 client-level password-spray guard를 추가했다. 같은 client hash에서 window 안에 여러 email hash로 실패가 분산되면 정상 계정 로그인도 429로 막고 `auth_login_risk_blocked` audit event를 남긴다.
- 이번 추가 루프로 `/v1/experiments`, `/v1/experiments/assignments`, `/v1/experiments/{experimentKey}/events`, `/v1/experiments/{experimentKey}/status`를 추가했다. Learner별 deterministic hash assignment, weighted variant, exposure event, conversion/custom event, admin-gated create/status control, privacy delete scope를 테스트와 benchmark로 잠갔다.
- 이번 추가 루프로 `/v1/gamification/me`, `/v1/reputation/me`, `/v1/friends`, `/v1/friends/recommendations`, `/v1/social/discovery`, `/v1/social/settings`, `/v1/social/blocks`, `/v1/social/blocks/{blockedLearnerId}`, `/v1/friends/invites`, `/v1/friends/invites/{inviteId}/accept`, `/v1/friends/{friendLearnerId}`, `/v1/friends/quests`, `/v1/friends/quests/{questId}/claim`, `/v1/rewards/shop`, `/v1/admin/rewards/shop`, `/v1/admin/rewards/shop/{rewardKey}`, `/v1/rewards/shop/{rewardKey}/purchase`, `/v1/rewards/inventory`, `/v1/rewards/boosts/{rewardKey}/activate`, `/v1/achievements/me`, `/v1/leagues/me`, `/v1/leaderboards/weekly`, `/v1/admin/xp-abuse-flags`, `/v1/admin/xp-abuse-flags/{flagId}/status`, `/v1/admin/reputation/learners`, `/v1/admin/reputation/learners/{learnerId}`를 추가했다. Practice turn, review card 생성, pronunciation score, review grade가 idempotent XP event로 적립되고, 이를 기반으로 streak, daily quest 3종, friend graph/invite lifecycle, friend recommendation, social discovery/privacy/blocking, friend quest, reward currency ledger, operated reward shop pricing/policy, reward inventory, XP boost, achievement award, weekly league tier, anomaly flag, boosted-XP/duplicate-payload abuse flag, leaderboard exclusion, admin review status, multi-signal reputation profile/review queue, leaderboard를 계산한다. Privacy delete는 XP event, achievement award, XP abuse flag, friend invite/relationship/quest, social settings/blocks, reward currency event, reward shop purchase history, reward inventory, active XP boost까지 지운다.
- 이번 추가 루프로 review card에 `memoryStrengthDays`, `memoryDifficulty`, `recallProbability`, `recallRisk`를 붙이고 `/v1/memory/summary`를 추가했다. 추천 응답도 memory summary를 포함해 태그별 fragile/new mastery와 at-risk card를 반영한다. 이번 이어진 루프에서는 `app/learner_model.py`와 `scripts/evaluate_learner_model.py`로 offline logistic learner-memory train/evaluate artifact를 추가했다.
- 이번 추가 루프로 여행/체류 survival 코스를 추가해 course catalog를 2개 course/10개 unit/20개 lesson/52개 practice room reference로 확장했다.

## 아직 Duolingo급이 아닌 점

- 인증은 개발용 헤더 모드, 만료형 HMAC token 모드, password account/session auth, HS256 JWT access token, session inventory/remote revoke/logout-all, password change, password-confirmed/OIDC-confirmed account deletion, optional device binding, account device registry/trust/revoke lifecycle, signed challenge HMAC device attestation, RS256 public-key challenge proof-of-possession, WebAuthn-style ES256 assertion verification, login failure throttling, registration throttling, refresh-token replay response, password-spray client guard, HS256 secret 또는 RS256 JWKS 기반 OIDC-compatible ID token federation, OAuth authorization-code PKCE start/callback, enterprise SSO connection registry/domain discovery/PKCE start/callback/domain enforcement, XP abuse review queue, deterministic multi-signal reputation profile, offline reputation model train/evaluate artifact까지 갖췄다. 그래도 Duolingo급 또는 hosted 제품 기준에서는 실제 Apple/Google token endpoint 운영 검증, 실제 기업 IdP 운영 검증, Apple App Attest/Play Integrity 생산 운영 증거, 실제 플랫폼 authenticator 기반 WebAuthn ceremony 증거, 실제 moderation outcome 기반 production learned reputation anomaly engine이 필요하다.
- 발음 평가는 아직 production speech model이 아니다. 현재는 text overlap과 간단한 WAV feature 기반 mock에 가깝다. 실제 음소/억양/속도/문장 단위 피드백 모델이 필요하다.
- 추천은 이제 최근 교정, lapse, 최근 방, 오늘 완료 방, HLR-inspired recall estimate, offline learner-memory model evaluation artifact를 반영하고, 실험 배정/노출/전환 이벤트/variant analytics/statistical testing/decision proposal/apply workflow, content release plan/apply/rollback, XP/streak/daily quest/friend graph/friend recommendation/social discovery/privacy/blocking/friend quest/reward shop/boost/leaderboard/abuse-review 원장도 갖췄다. 그래도 Birdbrain급 개인화와 비교하면 장기 retention signal, 대규모 실제 학습 이력 기반 훈련, 자동 릴리즈 의사결정 UI와 완전 자동화가 부족하다.
- 콘텐츠 데이터셋은 2개 course와 52개 room으로 늘었고 authoring/import/QA, translation memory, bulk QA, 버전 스냅샷/게시, editor-reviewer-publisher 승인 게이트, branching/assignment API, content operation queue, managed scheduler run history, release plan/canary metadata/due-worker/apply/rollback backend도 생겼지만, Duolingo식 대규모 skill tree나 LibreLingo식 장기 코스 운영에는 아직 못 미친다. 아직 실제 CMS UI, production-scale 콘텐츠 운영 queue 운영 증거, 릴리즈 전용 UI, hosted/production scheduler-worker 운영 증거는 없다.
- 레이트리밋은 pluggable memory/Redis adapter 구조가 생겼다. 하지만 이 환경에서는 실제 Redis 서버로 멀티워커/멀티인스턴스 부하 테스트를 돌리지 못했다.
- Docker 검증은 이 환경에서 정적 검증까지만 했다. 실제 container build/run smoke는 Docker가 설치된 환경에서 추가해야 한다.
- provider adapter는 structured output 정규화, schemaVersion 검증, 선택 strict JSON Schema response format, 기본 2회/최대 3회 repair loop, STT data URL/content-type 처리를 갖췄다. 그래도 실제 key 기반 provider-native JSON Schema 호환성 증거와 미디어 end-to-end 검증까지는 아니다.

## 이번 루프에서 실제로 닫은 결함

- 전역 `me` 프로필/전역 리뷰카드/전역 삭제 문제를 learner scope로 바꿨다.
- `/v1/audit-log` 무인증 공개 문제를 admin key 요구로 막았다.
- `POST /v1/events` 임의 event name 수용 문제를 허용 목록 검증으로 바꿨다.
- 확장 API가 계약 밖에 남아 있던 문제를 OpenAPI 120개 operation으로 동기화했다.
- 계약 검증기가 undocumented backend route를 실패로 처리하게 했다.
- TTS 캐시의 WAV 고정 재포장 문제를 content type 저장으로 고쳤다.
- CORS `*` + credentials 조합을 명시 origin 환경변수 방식으로 바꿨다.
- 외부 LLM adapter가 assistantText만 바꾸던 문제를 줄이고, structured JSON fields를 반영하도록 고쳤다.
- hosted/token mode에서 unsigned learner header를 거부하게 했다.
- privacy delete audit에 원문 learner id가 남지 않게 했다.
- admin key 기본값은 dev mode에서만 허용하게 했다.
- rate limiter를 교체 가능한 memory/Redis adapter로 분리하고 provider status에 backend 상태를 노출했다.
- 외부 LLM structured output에 정규화, 필드 검증, 다중 repair loop, repaired warning을 추가했다.
- practice room seed를 52개로 확장했다.
- learner token을 만료형 v2 HMAC로 바꾸고 legacy token 허용을 명시 env 뒤로 숨겼다.
- recommendations에 learner signal summary를 추가하고 공유 OpenAPI/TypeScript 계약에 반영했다.
- OpenAI STT adapter의 raw base64/data URL media decoding과 multipart content type/filename extension 처리를 고쳤다.
- course/unit/lesson catalog endpoint와 practice room course metadata를 추가했다.
- 외부 LLM structured output에 schemaVersion 필수 검증과 optional strict `json_schema` response format mode를 추가했다.
- 외부 LLM structured output 다중 repair policy를 테스트와 benchmark로 추가 검증했다.
- STT multipart M4A/WebM filename/content-type mapping 회귀 테스트를 추가했다.
- password account/session auth와 hashed session storage, refresh rotation, logout revoke, bearer-token learner scope를 추가했다.
- OIDC-compatible ID token login을 추가했다. `/v1/auth/oidc`는 provider allowlist, issuer, audience, expiry, nonce, `email_verified` claim을 검증하고, HS256 secret 또는 RS256 JWKS public key로 서명을 확인한 뒤 `account_identities`에 provider subject를 연결하고 기존 JWT/refresh account session을 발급한다. Provider status는 `oidcFederation=true`, `oidcIdTokenVerification=hs256_rs256_jwks`, `oidcJwksVerification=true/false`로 현재 범위를 명확히 드러낸다.
- OAuth authorization-code PKCE start/callback을 추가했다. `/v1/auth/oauth/pkce/start`는 허용 provider/redirect URI, S256 code challenge, nonce, state를 검증하고 state는 SHA-256 hash로만 저장한다. `/v1/auth/oauth/pkce/callback`은 state를 1회성으로 소비하고 S256 `codeVerifier`를 대조한 뒤, 설정된 token endpoint에서 받은 ID token을 기존 OIDC 검증기로 확인하거나 dev/local signed authorization code를 검증해 계정 세션을 발급한다. 회귀 테스트와 benchmark는 bad verifier 401, bad verifier 뒤 state 재사용 401, 성공 뒤 replay 401을 확인한다.
- Enterprise SSO connection registry와 domain discovery, SSO 전용 PKCE start/callback을 추가했다. `/v1/admin/auth/sso-connections`, `/v1/admin/auth/sso-connections/{connectionId}`는 운영자가 provider/domain/redirect URI를 관리하게 하고, `/v1/auth/sso/discovery`는 이메일 도메인으로 connection을 찾는다. `/v1/auth/sso/pkce/start`와 `/v1/auth/sso/pkce/callback`은 hashed one-time state를 enterprise connection id에 묶고, callback ID token/code claim email이 connection domain과 맞지 않으면 계정 생성을 거부한다. Tests와 benchmark는 viewer update 403, unmatched domain 404, bad callback domain 401, replay 401, `sso:{connectionId}` identity linking, provider status flags를 확인한다.
- account access token을 opaque local token에서 HS256-signed JWT로 승격하고, DB에는 JWT 원문이 아니라 hash만 저장해 revocation lookup을 유지했다. Auth 응답은 `accessTokenFormat: jwt_hs256`을 반환한다.
- 계정 session inventory, 개별 session revoke, logout-all endpoint를 추가했다. 이제 사용자가 다른 기기/브라우저 세션을 확인하고 원격으로 끊을 수 있다.
- password change, password-confirmed account deletion, optional device binding, account device registry/trust/revoke lifecycle, login failure throttling을 추가했다.
- refresh token reuse/replay detection을 추가했다. rotate된 refresh token 재사용은 401로 거부되고, 해당 계정의 활성 세션을 revoke하며 audit log에 `auth_refresh_reuse_detected`를 남긴다.
- registration throttle을 추가했다. 같은 client/email hash 기준 계정 생성 burst를 막고, login/register attempt purpose를 분리해 throttle 간 오염을 줄였다.
- password-spray risk control을 추가했다. 같은 client hash가 여러 email hash로 로그인 실패를 뿌리면 429로 차단하고 audit log에 `auth_login_risk_blocked`를 남긴다.
- account device registry/trust/revoke lifecycle을 추가했다. Bound session은 처음 `untrusted` device로 기록되고, `trust-this-device` 확인 후 `trusted`가 되며, device revoke는 같은 device hash의 session을 즉시 revoke하고 같은 device id 재사용 로그인을 403으로 막는다.
- 이번 추가 루프로 `/v1/auth/devices/attestation/challenge`와 signed challenge HMAC 검증을 추가했다. 이어진 루프에서는 같은 challenge lifecycle에 RS256 public JWK proof-of-possession을 추가했고, 이번 루프에서는 `webauthn_public_key`의 P-256 ES256 assertion verifier를 추가했다. Provider status는 `publicKeyDeviceAttestationVerification=public_key_challenge_rs256`, `webauthnDeviceAttestationVerification=webauthn_assertion_es256`, RP ID, origin allowlist, user-presence requirement를 노출한다. Trust 요청은 HMAC, RSA public-key, WebAuthn-style ES256 모드 모두에서 1회성 challenge, bad signature 또는 bad WebAuthn origin 401, consumed challenge replay 401, successful `attestationVerified=true`를 테스트와 benchmark evidence로 남긴다. Native Apple App Attest/Play Integrity 생산 운영 증거와 실제 플랫폼 authenticator 기반 WebAuthn ceremony 증거는 아직 별도 과제다.
- review card memory fields, `/v1/memory/summary`, recommendations `memorySummary`, HLR-inspired recall estimate 회귀 테스트를 추가했다.
- 이번 추가 루프로 offline logistic learner-memory model train/evaluate pipeline을 추가했다. `learner_model_evaluation_20260630.json`은 fixture/local DB example count, train/eval split, calibrated threshold, accuracy/AUC/Brier/log-loss, coefficients, `productionTrained=false`를 남긴다. 이는 production Birdbrain 대체가 아니라 실제 학습 이력 기반 모델로 가기 위한 운영 readiness evidence다.
- 이번 추가 루프로 offline logistic reputation/anti-cheat model train/evaluate pipeline을 추가했다. `reputation_model_evaluation_20260630.json`은 XP abuse/reputation profile 기반 DB example, deterministic fixture, train/eval split, calibrated threshold, accuracy/AUC/Brier/log-loss, coefficients, `productionTrained=false`를 남긴다. 이는 production learned enforcement가 아니라 실제 moderation outcome 기반 모델로 가기 위한 readiness evidence다.
- 여행 survival course를 추가해 50개 이상 practice room과 multi-course 구조를 테스트로 잠갔다.
- 콘텐츠 authoring/import/QA API를 추가해 seed 파일만 수정해야 콘텐츠가 바뀌던 문제를 줄였다. 현재 seed 전체가 quality report를 통과하고, 잘못된 bundle은 missing ref/duplicate/orphan/conflict를 구조화된 오류로 돌려준다.
- 콘텐츠 import dry-run/apply 결과를 version snapshot으로 보존하고, `/v1/content/versions/{versionId}/publish`에서 저장된 snapshot을 다시 게시할 수 있게 했다. 생성/게시 audit event와 OpenAPI/TypeScript 계약, 테스트, benchmark artifact를 함께 갱신했다.
- 콘텐츠 version snapshot에 role-based review gate를 추가했다. Editor가 review 제출, reviewer가 승인/반려, publisher가 승인된 snapshot만 게시하는 흐름을 API/SQLite/OpenAPI/TypeScript/test/benchmark에 반영했다.
- 콘텐츠 translation memory와 bulk QA를 추가했다. Practice room seed/import에서 한국어 원문과 일본어 primary/alternative target을 적재하고, exact/fuzzy suggestion, editor upsert, 현재/버전/요청 bundle QA, target conflict warning을 API/SQLite/OpenAPI/TypeScript/test/benchmark에 반영했다.
- 콘텐츠 branching/assignment workflow를 추가했다. 저장된 snapshot에서 draft branch를 만들고, assignee/priority/due date/status를 관리하며, list/filter/status update와 audit event를 API/SQLite/OpenAPI/TypeScript/test/benchmark에 반영했다.
- 콘텐츠 release automation backend를 추가했다. 승인된 content version을 release plan으로 저장하고, scheduled/canary metadata, quality guardrail snapshot, publisher-only apply, future schedule guard, due release worker API/CLI, 직전 published snapshot rollback, audit event를 API/SQLite/OpenAPI/TypeScript/test/benchmark에 반영했다.
- 이번 추가 루프로 content operation queue backend를 추가했다. validate/import/run-due-release job을 SQLite에 저장하고, priority queue, publisher-only run-next worker, queued job cancel, job result/error persistence, provider status, audit event를 API/OpenAPI/TypeScript/test/benchmark에 반영했다.
- 이번 추가 루프로 managed content scheduler backend를 추가했다. `/v1/content/scheduler/run-once`가 due release worker와 queued operation job runner를 하나의 publisher-only tick으로 묶고, `content_scheduler_runs`에 lease owner, run status, release/job result, timestamps, audit evidence를 남긴다. `/v1/content/scheduler/runs`는 scheduler run history를 조회한다.
- 실험/feature flag backend를 추가했다. Seed running experiments, weighted variants, deterministic learner assignment, exposure logging, conversion/custom event logging, admin upsert/status controls, provider status flags, privacy deletion, OpenAPI/TypeScript/test/benchmark를 함께 반영했다.
- 실험 variant analytics/statistical testing backend를 추가했다. `/v1/experiments/{experimentKey}/analytics`는 admin viewer 이상에게 variant별 assignment, raw exposure event, distinct exposed learner, raw conversion event, distinct converted learner, conversion rate, Wilson 95% conversion interval, control 대비 absolute/relative lift, two-proportion z-test p-value, lift confidence interval, best observed variant, decision readiness를 제공한다. `winnerVariantKey`는 표본 조건과 positive statistical significance가 같이 맞을 때만 채우고, 테스트와 benchmark는 무권한 403, 노출/전환 집계, 표본 부족 guard, p-value/CI, audit log를 확인한다.
- 이번 추가 루프로 실험 decision workflow backend를 추가했다. `/v1/experiments/{experimentKey}/decisions`는 analytics snapshot과 guardrail 결과를 저장한 decision proposal을 만들고, `/v1/experiments/{experimentKey}/decisions/{decisionId}/apply`는 publisher 권한으로 winner rollout weight lock, pause/archive/no-winner/collect-more-data 결정을 적용한다. Tests와 benchmark는 viewer 제안 403, missing variant guard 409, proposal 저장/list, publisher-only apply, duplicate apply 409, 새 learner winner assignment, audit log를 확인한다.
- Gamification backend를 추가했다. XP ledger, anti-duplicate idempotency key, streak summary, daily quests, friend graph, friend invites, friend recommendations, social discovery/privacy/blocking, friend quests, reward currency ledger, operated reward shop pricing/policy/purchase limits, reward inventory, XP boost activation/application, multi-level achievement tracks, achievement gem rewards, weekly league tiers, XP anomaly flags, single-source concentration flag, boosted-XP abuse flag, duplicate-payload flag, leaderboard exclusion metadata, admin XP abuse review queue, deterministic multi-signal reputation profile/review queue, weekly leaderboard, progress 응답 XP/quest fields, provider status flags, privacy deletion, OpenAPI/TypeScript/test/benchmark를 함께 반영했다.
- 이번 추가 루프로 learner/admin reputation API를 추가했다. `/v1/reputation/me`, `/v1/admin/reputation/learners`, `/v1/admin/reputation/learners/{learnerId}`는 open XP abuse flag, leaderboard exclusion, weekly XP/event volume, social block friction, account device trust/revoke status, active session count를 evidence-backed signal로 묶고 `riskScore`, `riskBand`, `reviewRecommended`, `leaderboardEligible`을 반환한다. Tests와 benchmark는 boosted-XP block flag가 reputation high risk, leaderboard ineligible, admin queue 포함으로 이어지는 경로를 검증한다.

## 다음 루프에서 봐야 할 것

- 현재 OAuth/OIDC/enterprise SSO federation을 실제 Apple/Google token endpoint 운영 검증, 실제 기업 IdP JWKS/claims 운영 증거, native Apple App Attest/Play Integrity 생산 운영 증거, 실제 플랫폼 authenticator 기반 WebAuthn ceremony 증거, 현재의 login/register throttle/password-spray guard/refresh-token replay response/device revoke/signed challenge attestation/public-key challenge proof/WebAuthn-style ES256 assertion proof/deterministic reputation profile을 넘어서는 production-scale learned reputation/anomaly 기반 abuse controls로 승격한다.
- 실제 external provider key로 JSON Schema response_format 호환성 증거를 남긴다.
- 실제 API key로 MP3/WAV/WebM STT/pronunciation end-to-end media compatibility test를 남긴다.
- 실제 Redis 서버로 distributed rate limiter smoke/load test를 남긴다.
- Docker 가능한 머신에서 clean container smoke artifact를 남긴다.
- offline logistic learner-memory train/evaluate pipeline을 fixture/local DB evidence에서 실제 대규모 학습 이력으로 훈련/검증되는 learner model로 승격한다.
- content workflow를 CMS UI, production-scale 콘텐츠 운영 queue 운영 증거, 릴리즈 UI/hosted scheduler-worker 운영 증거, 실험 결과 분석 전용 UI와 운영 의사결정 workflow, 더 큰 grammar/mistake catalog가 있는 full CMS로 승격한다.
- XP economy는 이번 루프에서 friend graph/social invite lifecycle, friend recommendation, social discovery/privacy/blocking, friend quest, reward currency ledger, operated reward shop pricing/policy/purchase limits, reward inventory, XP boost, multi-level achievement tracks, achievement gem rewards, single-source anomaly flag, boosted-XP abuse flag, duplicate-payload flag, leaderboard exclusion, admin review queue, multi-signal reputation profile, offline reputation model evaluation까지 올라왔지만, 아직 production-scale learned cheating/reputation automation까지 확장해야 한다.
