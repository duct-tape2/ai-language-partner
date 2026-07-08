# API Runbook

Backend project: `ai-language-partner-mobile-shared-20260629-v1`

Contract source: `contracts/openapi_v0.yaml`

In default `dev` auth mode, learner scope is selected with `X-Learner-Id`. If omitted, the local development learner is `local-dev`.
In hosted/token mode, use `X-Learner-Token` instead of trusting raw learner headers.
For account sessions, use `Authorization: Bearer ...`; that account learner scope wins over raw learner headers.

## Install

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

By default SQLite is created at:

```text
apps/api/data/language_partner.sqlite3
```

For a disposable smoke-test DB:

```bash
AI_LANGUAGE_PARTNER_DB_PATH=/tmp/ai-language-partner-api.sqlite3 uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Smoke test

```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/personas
curl http://localhost:8000/v1/practice-rooms/tired_today
curl -X POST http://localhost:8000/v1/conversations \
  -H 'Content-Type: application/json' \
  -H 'X-Learner-Id: local-dev' \
  -d '{"personaId":"yui","practiceRoomId":"tired_today","mode":"practice"}'
```

Vertical slice request:

```bash
curl -X POST http://localhost:8000/v1/conversations/{conversationId}/turns \
  -H 'Content-Type: application/json' \
  -H 'X-Learner-Id: local-dev' \
  -d '{"inputType":"text","text":"나 오늘 너무 피곤했어. 일본어로 뭐라고 해?","requestTts":true}'
```

Expected `spokenText`:

```text
今日めっちゃ疲れた。
```

## Implemented endpoints

```text
GET  /health
GET  /v1/personas
GET  /v1/practice-rooms
GET  /v1/practice-rooms/{practiceRoomId}
GET  /v1/courses
GET  /v1/courses/{courseId}
POST /v1/content/validate
POST /v1/content/import
GET  /v1/content/quality-report
GET  /v1/content/translation-memory
POST /v1/content/translation-memory
POST /v1/content/translation-memory/suggest
POST /v1/content/bulk-qa
GET  /v1/content/assignments
POST /v1/content/assignments/{assignmentId}/status
GET  /v1/content/versions
GET  /v1/content/versions/{versionId}
POST /v1/content/versions/{versionId}/branch
POST /v1/content/versions/{versionId}/assign
POST /v1/content/versions/{versionId}/submit-review
POST /v1/content/versions/{versionId}/approve
POST /v1/content/versions/{versionId}/reject
POST /v1/content/versions/{versionId}/publish
GET  /v1/content/operations/jobs
POST /v1/content/operations/jobs
POST /v1/content/operations/jobs/run-next
GET  /v1/content/operations/jobs/{jobId}
POST /v1/content/operations/jobs/{jobId}/cancel
GET  /v1/content/scheduler/runs
POST /v1/content/scheduler/run-once
GET  /v1/content/releases
POST /v1/content/releases
POST /v1/content/releases/run-due
POST /v1/content/releases/{releaseId}/apply
POST /v1/content/releases/{releaseId}/rollback
GET  /v1/experiments
POST /v1/experiments
GET  /v1/experiments/assignments
GET  /v1/experiments/{experimentKey}/analytics
POST /v1/experiments/{experimentKey}/status
POST /v1/experiments/{experimentKey}/events
GET  /v1/experiments/{experimentKey}/decisions
POST /v1/experiments/{experimentKey}/decisions
POST /v1/experiments/{experimentKey}/decisions/{decisionId}/apply
POST /v1/auth/register
POST /v1/auth/login
POST /v1/auth/oidc
POST /v1/auth/oauth/pkce/start
POST /v1/auth/oauth/pkce/callback
GET  /v1/auth/sso/discovery
POST /v1/auth/sso/pkce/start
POST /v1/auth/sso/pkce/callback
GET  /v1/admin/auth/sso-connections
PUT  /v1/admin/auth/sso-connections/{connectionId}
POST /v1/auth/refresh
GET  /v1/auth/me
POST /v1/auth/logout
GET  /v1/auth/devices
POST /v1/auth/devices/attestation/challenge
POST /v1/auth/devices/trust
DELETE /v1/auth/devices/{deviceId}
GET  /v1/auth/sessions
DELETE /v1/auth/sessions/{sessionId}
POST /v1/auth/logout-all
POST /v1/auth/change-password
DELETE /v1/auth/account
POST /v1/conversations
POST /v1/conversations/{conversationId}/turns
POST /v1/tts/synthesize
POST /v1/stt/transcribe
GET  /v1/review-cards
POST /v1/review-cards
GET  /v1/progress/today
GET  /v1/gamification/me
GET  /v1/reputation/me
GET  /v1/friends
GET  /v1/friends/recommendations
GET  /v1/social/discovery
GET  /v1/social/settings
PUT  /v1/social/settings
GET  /v1/social/blocks
POST /v1/social/blocks/{blockedLearnerId}
DELETE /v1/social/blocks/{blockedLearnerId}
POST /v1/friends/invites
POST /v1/friends/invites/{inviteId}/accept
DELETE /v1/friends/{friendLearnerId}
GET  /v1/friends/quests
POST /v1/friends/quests/{questId}/claim
GET  /v1/rewards/inventory
GET  /v1/rewards/shop
POST /v1/rewards/shop/{rewardKey}/purchase
POST /v1/rewards/boosts/{rewardKey}/activate
GET  /v1/achievements/me
GET  /v1/leagues/me
GET  /v1/leaderboards/weekly
GET  /v1/admin/xp-abuse-flags
POST /v1/admin/xp-abuse-flags/{flagId}/status
GET  /v1/admin/reputation/learners
GET  /v1/admin/reputation/learners/{learnerId}
GET  /v1/entitlements/me
POST /v1/events
GET  /v1/profile/me
PUT  /v1/profile/me
GET  /v1/recommendations/today
GET  /v1/memory/summary
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
GET  /v1/audit-log
DELETE /v1/privacy/me
```

Quick checks:

```bash
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/providers/status
curl http://localhost:8000/v1/courses
curl http://localhost:8000/v1/courses/jp_beginner_speaking_ko
curl -H 'X-Admin-Key: local-dev-admin' http://localhost:8000/v1/content/quality-report
curl -H 'X-Admin-Key: local-dev-admin' http://localhost:8000/v1/content/translation-memory
curl -H 'X-Admin-Key: local-dev-admin' http://localhost:8000/v1/content/assignments
curl -H 'X-Admin-Key: local-dev-admin' http://localhost:8000/v1/content/versions
curl -H 'X-Admin-Key: local-dev-admin' http://localhost:8000/v1/experiments
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/experiments/assignments
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/gamification/me
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/reputation/me
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/friends
curl -H 'X-Learner-Id: local-dev' 'http://localhost:8000/v1/social/discovery?limit=10&targetLanguage=ja'
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/social/settings
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/social/blocks
curl -X POST http://localhost:8000/v1/friends/invites \
  -H 'Content-Type: application/json' \
  -H 'X-Learner-Id: local-dev' \
  -d '{"friendLearnerId":"friend_alpha","message":"같이 연습하자"}'
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/friends/quests
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/rewards/shop
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/rewards/inventory
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/achievements/me
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/leagues/me
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/leaderboards/weekly
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/recommendations/today
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/memory/summary
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/review-cards/due
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/export/anki
curl -H 'X-Learner-Id: local-dev' http://localhost:8000/v1/export/anki-apkg
curl 'http://localhost:8000/v1/grammar/jlpt?level=N5'
curl 'http://localhost:8000/v1/mistakes/korean-patterns?tag=감정표현'
curl http://localhost:8000/v1/weaknesses/summary
curl -X POST http://localhost:8000/v1/export/anki-connect \
  -H 'Content-Type: application/json' \
  -H 'X-Learner-Id: local-dev' \
  -d '{"deckName":"AI Japanese Partner","apply":false}'
```

Admin audit log requires `X-Admin-Key`:

```bash
curl -H 'X-Admin-Key: local-dev-admin' http://localhost:8000/v1/audit-log
```

The `local-dev-admin` fallback works only in `AI_LANGUAGE_PARTNER_AUTH_MODE=dev`. In production/hosted mode, set `AI_LANGUAGE_PARTNER_ADMIN_KEY`.

## Content authoring/import/QA

Content admin endpoints require `X-Admin-Key`.

```bash
curl -H 'X-Admin-Key: local-dev-admin' \
  http://localhost:8000/v1/content/quality-report
```

Translation memory is seeded from practice room Korean source phrases and Japanese primary/alternative targets. Viewer/editor/reviewer/publisher roles can list or request suggestions; editor can upsert new entries.

```bash
curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/content/translation-memory?limit=20'

curl -X POST http://localhost:8000/v1/content/translation-memory/suggest \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  -d '{"sourceText":"오늘 너무 피곤했어","limit":5}'

curl -X POST http://localhost:8000/v1/content/translation-memory \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: content-editor' \
  -d '{"entries":[{"sourceText":"새로운 표현","targetText":"新しい表現","tags":["manual"],"quality":95}]}'
```

Bulk QA can run against the current stored catalog, a saved `versionId`, or an inline bundle. It combines the normal content quality report with translation memory exact/fuzzy/missing/conflict checks.

```bash
curl -X POST http://localhost:8000/v1/content/bulk-qa \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  -d '{}'

curl -X POST http://localhost:8000/v1/content/bulk-qa \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  -d '{"versionId":"contentver_..."}'
```

Saved content versions can also be branched into draft work copies and assigned to an editor/writer. Assignments are one-per-version and can be reassigned or moved through `todo`, `in_progress`, `blocked`, and `done`.

```bash
curl -X POST http://localhost:8000/v1/content/versions/contentver_.../branch \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: content-editor' \
  -d '{"label":"Travel copy branch","branchName":"travel-copy","assignee":"writer-a","priority":"high","dueAt":"2026-07-05T00:00:00Z"}'

curl -X POST http://localhost:8000/v1/content/versions/contentver_.../assign \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: content-editor' \
  -d '{"assignee":"writer-b","priority":"urgent","status":"in_progress","note":"copy pass started"}'

curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/content/assignments?assignee=writer-b'

curl -X POST http://localhost:8000/v1/content/assignments/contentasgn_.../status \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: reviewer' \
  -H 'X-Admin-User: content-reviewer' \
  -d '{"status":"done","note":"ready for review submission"}'
```

Validate a bundle without writing:

```bash
curl -X POST http://localhost:8000/v1/content/validate \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -d '{"courses":[],"practiceRooms":[]}'
```

Import defaults to `dryRun: true`. To apply, send `dryRun: false`.

```bash
curl -X POST http://localhost:8000/v1/content/import \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -d '{"dryRun":true,"replaceExisting":true,"courses":[...],"practiceRooms":[...]}'
```

Dry-run and apply imports both create a content version snapshot. `X-Admin-Role` is optional and defaults to `owner` after a valid admin key, but the production-style review flow should use separate `editor`, `reviewer`, and `publisher` actors.

Inspect a saved snapshot:

```bash
curl -H 'X-Admin-Key: local-dev-admin' \
  http://localhost:8000/v1/content/versions

curl -H 'X-Admin-Key: local-dev-admin' \
  http://localhost:8000/v1/content/versions/contentver_...
```

Submit, approve, and publish a snapshot:

```bash
curl -X POST http://localhost:8000/v1/content/versions/contentver_.../submit-review \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: content-editor' \
  -d '{"note":"ready for review"}'

curl -X POST http://localhost:8000/v1/content/versions/contentver_.../approve \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: reviewer' \
  -H 'X-Admin-User: content-reviewer' \
  -d '{"note":"approved"}'

curl -X POST http://localhost:8000/v1/content/versions/contentver_.../publish \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: publisher' \
  -H 'X-Admin-User: content-publisher'
```

Reject a snapshot instead of approving it:

```bash
curl -X POST http://localhost:8000/v1/content/versions/contentver_.../reject \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: reviewer' \
  -H 'X-Admin-User: content-reviewer' \
  -d '{"note":"revise the phrase set"}'
```

Validation rejects empty bundles, duplicate course/unit/lesson/room IDs, unknown persona IDs, missing practice-room references, duplicate room placements, orphan rooms, and existing ID conflicts when `replaceExisting` is false. On apply or approved publish, practice-room `courseId`, `unitId`, `lessonId`, order, and titles are derived from the course tree. Draft snapshots cannot be published until reviewer approval; a submitter cannot approve the same snapshot as reviewer. Version creation, review submission, approval, rejection, and publish events are recorded in the admin audit log.

Content operations can be queued for worker-style execution. Supported job types are `validate_bundle`, `import_bundle`, and `run_due_releases`; queued jobs keep payload, result/error, priority, actor, timestamps, and audit evidence.

```bash
curl -X POST http://localhost:8000/v1/content/operations/jobs \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: content-editor' \
  -d '{"jobType":"import_bundle","priority":"urgent","payload":{"bundle":{"courses":[],"practiceRooms":[]},"dryRun":true}}'

curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/content/operations/jobs?status=queued'

curl -X POST http://localhost:8000/v1/content/operations/jobs/run-next \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: publisher' \
  -H 'X-Admin-User: content-ops-worker' \
  -d '{"confirmation":"run-next-content-operation-job"}'

curl -X POST http://localhost:8000/v1/content/operations/jobs/contentjob_.../cancel \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: content-editor' \
  -d '{"confirmation":"cancel-content-operation-job"}'
```

Managed scheduler runs combine due release application and queued operation jobs into one publisher-only tick. Each run stores `schedulerKey`, `leaseOwner`, status, timestamps, release worker result, operation job results, and audit evidence in `content_scheduler_runs`.

```bash
curl -X POST http://localhost:8000/v1/content/scheduler/run-once \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: publisher' \
  -H 'X-Admin-User: content-scheduler' \
  -d '{"confirmation":"run-content-scheduler-once","leaseOwner":"local-cron","maxOperationJobs":1,"releaseLimit":50}'

curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/content/scheduler/runs?status=succeeded'
```

Approved content versions can also move through release plans. A release stores scheduling/canary metadata, quality guardrail snapshot, previous published version id, due-worker evidence, apply evidence, and rollback evidence.

```bash
curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  http://localhost:8000/v1/content/releases

curl -X POST http://localhost:8000/v1/content/releases \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: content-editor' \
  -d '{"versionId":"contentver_...","title":"Week 27 cafe copy canary","releaseStrategy":"canary","rolloutPercent":25,"scheduledAt":"2026-07-01T00:00:00Z","guardrails":{"manualQa":"passed"}}'

curl -X POST http://localhost:8000/v1/content/releases/contentrel_.../apply \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: publisher' \
  -H 'X-Admin-User: content-publisher' \
  -d '{"confirmation":"apply-content-release","force":true,"note":"Approved release window"}'

curl -X POST http://localhost:8000/v1/content/releases/run-due \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: publisher' \
  -H 'X-Admin-User: content-release-worker' \
  -d '{"confirmation":"run-due-content-releases","limit":50}'

curl -X POST http://localhost:8000/v1/content/releases/contentrel_.../rollback \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: publisher' \
  -H 'X-Admin-User: content-publisher' \
  -d '{"confirmation":"rollback-content-release","note":"Rollback after canary review"}'
```

The same due-release worker can run without HTTP:

```bash
python scripts/run_due_content_releases.py --db-path app/data/language_partner.sqlite3 --actor content-release-worker --limit 50
```

## Gamification

Practice turns, generated review cards, pronunciation scoring, and review grading create idempotent XP events and earn reward currency. The XP ledger drives streaks, daily quests, friend graph/invites, friend recommendations, social discovery, privacy settings, blocking, friend quests, operated reward shop policy and purchases, reward inventory, XP boosts, multi-level achievement awards with gem rewards, weekly league tier status, boosted-XP and duplicate-payload abuse flags, leaderboard exclusion metadata, multi-signal reputation profiles, admin review status, and the weekly leaderboard.

```bash
curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/gamification/me

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/reputation/me

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/friends

curl -H 'X-Learner-Id: local-dev' \
  'http://localhost:8000/v1/friends/recommendations?limit=10'

curl -H 'X-Learner-Id: local-dev' \
  'http://localhost:8000/v1/social/discovery?limit=10&targetLanguage=ja'

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/social/settings

curl -X PUT http://localhost:8000/v1/social/settings \
  -H 'Content-Type: application/json' \
  -H 'X-Learner-Id: local-dev' \
  -d '{"discoverable":true,"allowFriendInvites":true,"showWeeklyXp":true}'

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/social/blocks

curl -X POST http://localhost:8000/v1/social/blocks/blocked_friend \
  -H 'X-Learner-Id: local-dev'

curl -X DELETE http://localhost:8000/v1/social/blocks/blocked_friend \
  -H 'X-Learner-Id: local-dev'

curl -X POST http://localhost:8000/v1/friends/invites \
  -H 'Content-Type: application/json' \
  -H 'X-Learner-Id: local-dev' \
  -d '{"friendLearnerId":"friend_alpha","message":"같이 퀘스트 하자"}'

curl -X POST http://localhost:8000/v1/friends/invites/friendinvite_.../accept \
  -H 'X-Learner-Id: friend_alpha'

curl -H 'X-Learner-Id: local-dev' \
  'http://localhost:8000/v1/friends/quests?partnerLearnerId=friend_alpha'

curl -X POST http://localhost:8000/v1/friends/quests/friendquest_.../claim \
  -H 'X-Learner-Id: local-dev'

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/rewards/inventory

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/rewards/shop

curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  http://localhost:8000/v1/admin/rewards/shop

curl -X PUT http://localhost:8000/v1/admin/rewards/shop/streak_freeze_1 \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: shop-editor' \
  -d '{"priceCurrency":"gems","priceAmount":2,"available":true,"dailyPurchaseLimit":1,"inventoryLimit":1,"sortOrder":5}'

curl -X POST http://localhost:8000/v1/rewards/shop/streak_freeze_1/purchase \
  -H 'X-Learner-Id: local-dev'

curl -X POST http://localhost:8000/v1/rewards/boosts/xp_boost_2x_15m/activate \
  -H 'X-Learner-Id: local-dev'

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/achievements/me

curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/leagues/me

curl -H 'X-Learner-Id: local-dev' \
  'http://localhost:8000/v1/leaderboards/weekly?limit=20'

curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/admin/xp-abuse-flags?status=open&limit=20'

curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/admin/reputation/learners?band=high&limit=20'

curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  http://localhost:8000/v1/admin/reputation/learners/local-dev

curl -X POST http://localhost:8000/v1/admin/xp-abuse-flags/xpflag_.../status \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: reviewer' \
  -H 'X-Admin-User: ops-reviewer' \
  -d '{"status":"resolved","note":"reviewed boosted XP evidence"}'
```

`/v1/progress/today` also includes `xpEarnedToday`, `dailyQuestsCompleted`, and `dailyQuestCount`.

Current daily quests:

```text
complete_practice_turn
review_one_card
earn_30_xp
```

Multi-level achievement awards, achievement reward currency events, friend invites/relationships/quests, social settings/blocks, reward inventory, active XP boosts, and XP anomaly/review flags are also learner-scoped. `DELETE /v1/privacy/me` removes XP events, achievement awards, friend invites/relationships/quests, social settings/blocks, reward currency events, reward inventory items, XP boosts, and XP anomaly/review flags.

## Experiments and feature flags

The backend seeds two running experiments:

```text
daily_recommendation_copy_v1
practice_room_order_v1
```

Learner assignments are deterministic per learner and experiment key. Fetching assignments logs exposure events by default.

```bash
curl -H 'X-Learner-Id: local-dev' \
  http://localhost:8000/v1/experiments/assignments

curl -H 'X-Learner-Id: local-dev' \
  'http://localhost:8000/v1/experiments/assignments?exposure=false'
```

Record conversion or custom events after assignment:

```bash
curl -X POST http://localhost:8000/v1/experiments/daily_recommendation_copy_v1/events \
  -H 'Content-Type: application/json' \
  -H 'X-Learner-Id: local-dev' \
  -d '{"eventName":"conversion","payload":{"surface":"HomeTodayScreen"}}'
```

View variant-level experiment analytics as an admin viewer:

```bash
curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/experiments/daily_recommendation_copy_v1/analytics?minimumExposedLearners=30'
```

The analytics response reports assignment count, raw exposure/conversion event counts, distinct exposed/converted learners, conversion rates, Wilson 95% conversion-rate intervals, custom event counts, `bestObservedVariantKey`, and `decisionReady`. It also compares each non-control variant against `controlVariantKey` with absolute/relative lift, a two-sided two-proportion z-test `pValue`, and a 95% lift interval. `winnerVariantKey` stays empty until at least two variants meet `minimumExposedLearners` and a positive variant is statistically significant at `statisticalSignificanceAlpha`; this is a guard against treating a tiny or noisy sample as a product decision.

Admin users can list, create/update, pause, resume, archive, or draft experiments. Viewer can list; editor can mutate.

```bash
curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  http://localhost:8000/v1/experiments

curl -X POST http://localhost:8000/v1/experiments \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: experiment-editor' \
  -d '{"key":"paywall_copy_test_v1","name":"Paywall copy test","status":"running","variants":[{"key":"control","label":"Control","weight":1},{"key":"trial_focus","label":"Trial focus","weight":1,"payload":{"copy":"trial"}}],"allocation":{"unit":"learner"}}'

curl -X POST http://localhost:8000/v1/experiments/paywall_copy_test_v1/status \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: experiment-editor' \
  -d '{"status":"paused"}'
```

Experiment assignments and experiment events are learner-scoped and are removed by `DELETE /v1/privacy/me`.

## Account auth mode

Password account/session auth is available without external identity providers:

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"learner@example.com","password":"correct-horse-battery","learnerId":"account-alpha","deviceLabel":"ios-simulator","deviceId":"optional-stable-device-id"}'
```

The response returns `tokenType: Bearer`, `accessTokenFormat: jwt_hs256`, an HS256 JWT access token, and an opaque refresh token. Store tokens on the client; the backend stores only token hashes for session lookup and revocation. In production/hosted mode, set `AI_LANGUAGE_PARTNER_JWT_SECRET` or `AI_LANGUAGE_PARTNER_AUTH_SECRET`. If `deviceId` is supplied, later bearer requests must include:

```text
X-Device-Id: optional-stable-device-id
```

The first bound session is recorded in the account device registry as `untrusted`. The current backend supports account-confirmed device trust, signed challenge HMAC attestation, RS256 public-key challenge proof-of-possession, WebAuthn-style ES256 assertion verification, and revoke-to-session-revocation. Configure `AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET` to enable HMAC `signed_challenge`; `public_key_challenge` can issue a one-time challenge without a shared server secret and verifies a public RSA JWK signature; `webauthn_public_key` verifies a P-256 public JWK assertion with challenge, origin, RP ID hash, user-presence, authenticatorData, and clientDataJSON checks. Native Apple App Attest, Play Integrity production evidence, and real platform-authenticator WebAuthn ceremony evidence are still separate gaps.

Use the account scope:

```bash
curl -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Device-Id: optional-stable-device-id' \
  http://localhost:8000/v1/auth/me
```

List trusted/untrusted devices, trust the current bound device, and revoke a device:

```bash
curl -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Device-Id: optional-stable-device-id' \
  http://localhost:8000/v1/auth/devices

curl -X POST http://localhost:8000/v1/auth/devices/attestation/challenge \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Device-Id: optional-stable-device-id' \
  -H 'Content-Type: application/json' \
  -d '{"attestationProvider":"signed_challenge","attestationSubject":"device-public-key-id"}'

curl -X POST http://localhost:8000/v1/auth/devices/trust \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Device-Id: optional-stable-device-id' \
  -H 'Content-Type: application/json' \
  -d '{"confirmation":"trust-this-device","deviceLabel":"ios-simulator","platform":"ios","attestationProvider":"self_attested"}'

curl -X DELETE http://localhost:8000/v1/auth/devices/dev_... \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Device-Id: optional-stable-device-id'
```

For `signed_challenge`, sign the returned `message` with HMAC-SHA256 using the configured attestation secret and submit:

```json
{
  "confirmation": "trust-this-device",
  "deviceLabel": "ios-simulator",
  "platform": "ios",
  "attestationProvider": "signed_challenge",
  "attestationSubject": "device-public-key-id",
  "evidence": {
    "challengeId": "attchal_...",
    "challenge": "alp_dev_att_...",
    "signature": "hex-hmac-sha256"
  }
}
```

For `public_key_challenge`, send a stable `attestationSubject` when issuing the challenge. The subject may be the public RSA JWK JSON itself, or a stable key id with the public JWK supplied as `evidence.publicKeyJwk` during trust. Sign the returned `message` with the matching private key using RS256, then submit the same `attestationSubject`:

```json
{
  "confirmation": "trust-this-device",
  "deviceLabel": "android-device",
  "platform": "android",
  "attestationProvider": "public_key_challenge",
  "attestationSubject": "{\"kty\":\"RSA\",\"n\":\"...\",\"e\":\"AQAB\"}",
  "evidence": {
    "algorithm": "rs256",
    "challengeId": "attchal_...",
    "challenge": "alp_dev_att_...",
    "signature": "base64url-rs256-signature"
  }
}
```

Bad signatures and replayed/expired challenges return `401`.

For `webauthn_public_key`, issue the challenge with a P-256 public JWK JSON as `attestationSubject`. Set `AI_LANGUAGE_PARTNER_WEBAUTHN_RP_ID` and `AI_LANGUAGE_PARTNER_WEBAUTHN_ALLOWED_ORIGINS` for hosted deployments. The client must submit `clientDataJSON`, `authenticatorData`, and an ES256 signature over `authenticatorData || SHA256(clientDataJSON)`:

```json
{
  "confirmation": "trust-this-device",
  "deviceLabel": "ios-passkey",
  "platform": "ios",
  "attestationProvider": "webauthn_public_key",
  "attestationSubject": "{\"kty\":\"EC\",\"crv\":\"P-256\",\"x\":\"...\",\"y\":\"...\"}",
  "evidence": {
    "algorithm": "webauthn-es256",
    "challengeId": "attchal_...",
    "challenge": "alp_dev_att_...",
    "clientDataJSON": "base64url-json",
    "authenticatorData": "base64url-authenticator-data",
    "signature": "base64url-der-or-raw-es256-signature"
  }
}
```

Bad WebAuthn origin, RP ID hash mismatch, missing user-presence, bad signature, and replayed/expired challenges return `401`.

Revoking a device revokes matching bound sessions and future login with the same `deviceId` is rejected with `403`.

List and revoke account sessions:

```bash
curl -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  http://localhost:8000/v1/auth/sessions

curl -X DELETE http://localhost:8000/v1/auth/sessions/sess_... \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

Logout all sessions, optionally keeping the current one:

```bash
curl -X POST 'http://localhost:8000/v1/auth/logout-all?keepCurrent=true' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

Refresh rotates the old session:

```bash
curl -X POST http://localhost:8000/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refreshToken":"alp_rt_...","deviceId":"optional-stable-device-id"}'
```

If an already-rotated refresh token is submitted again, it is treated as replay/reuse: the request returns `401`, all sessions for that account are revoked, and the admin audit log records `auth_refresh_reuse_detected`.

Password change requires the current password and revokes prior sessions:

```bash
curl -X POST http://localhost:8000/v1/auth/change-password \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Device-Id: optional-stable-device-id' \
  -H 'Content-Type: application/json' \
  -d '{"currentPassword":"correct-horse-battery","newPassword":"new-correct-horse-battery","deviceId":"optional-stable-device-id"}'
```

Account deletion requires password re-authentication, disables the account, revokes sessions, and runs learner-scoped privacy deletion:

```bash
curl -X DELETE http://localhost:8000/v1/auth/account \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Device-Id: optional-stable-device-id' \
  -H 'Content-Type: application/json' \
  -d '{"password":"new-correct-horse-battery"}'
```

OIDC-compatible ID-token login is also available:

```bash
cd apps/api
OIDC_TOKEN=$(.venv/bin/python - <<'PY'
from app.main import create_oidc_id_token
print(create_oidc_id_token(
    provider="local-oidc",
    subject="local-subject-123",
    email="oidc-learner@example.com",
    secret="local-dev-jwt-secret",
    nonce="demo-nonce",
))
PY
)

curl -X POST http://localhost:8000/v1/auth/oidc \
  -H 'Content-Type: application/json' \
  -d "{\"provider\":\"local-oidc\",\"idToken\":\"$OIDC_TOKEN\",\"nonce\":\"demo-nonce\",\"learnerId\":\"oidc-alpha\",\"deviceLabel\":\"ios-oidc\"}"
```

`POST /v1/auth/oidc` verifies provider allowlist, issuer, audience, expiry, nonce, and `email_verified`, checks the signature with either HS256 secret or RS256 JWKS public keys, links the provider subject in `account_identities`, then returns the same `AuthTokenResponse` shape as password login. Provider status reports `oidcIdTokenVerification=hs256_rs256_jwks`.

OAuth authorization-code PKCE is available through a two-step backend handoff. The start endpoint validates provider/redirect URI, stores only a hashed state plus S256 challenge, and returns a provider authorization URL:

```bash
export CODE_VERIFIER='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~'
CODE_CHALLENGE=$(python3 - <<'PY'
import base64, hashlib, os
verifier = os.environ["CODE_VERIFIER"]
print(base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii"))
PY
)

curl -X POST http://localhost:8000/v1/auth/oauth/pkce/start \
  -H 'Content-Type: application/json' \
  -d "{\"provider\":\"local-oidc\",\"redirectUri\":\"http://localhost:8000/auth/callback\",\"codeChallenge\":\"$CODE_CHALLENGE\",\"learnerId\":\"oauth-alpha\"}"
```

The callback endpoint consumes state once, rejects PKCE verifier mismatches, rejects replay, then exchanges the authorization code through a configured token endpoint or verifies a dev/local signed authorization code:

```bash
curl -X POST http://localhost:8000/v1/auth/oauth/pkce/callback \
  -H 'Content-Type: application/json' \
  -d '{"provider":"local-oidc","state":"alp_oauth_state_...","code":"...","codeVerifier":"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~","redirectUri":"http://localhost:8000/auth/callback"}'
```

Provider status reports `oauthAuthorizationCodePkce=true`, `oauthPkceS256Only=true`, `oauthPkceStateStoredHashed=true`, and `oauthPkceOneTimeState=true`. Real providers should configure redirect URI allowlists and token endpoints:

```bash
AI_LANGUAGE_PARTNER_OAUTH_GOOGLE_AUTHORIZATION_ENDPOINT=https://accounts.google.com/o/oauth2/v2/auth
AI_LANGUAGE_PARTNER_OAUTH_GOOGLE_TOKEN_ENDPOINT=https://oauth2.googleapis.com/token
AI_LANGUAGE_PARTNER_OAUTH_GOOGLE_CLIENT_ID=com.example.languagepartner
AI_LANGUAGE_PARTNER_OAUTH_GOOGLE_REDIRECT_URIS=com.example.languagepartner:/oauth2redirect,http://localhost:8000/auth/callback
```

Enterprise SSO uses the same OIDC/OAuth provider verification layer, but adds an admin-managed connection registry and email-domain discovery. Register a connection:

```bash
curl -X PUT http://localhost:8000/v1/admin/auth/sso-connections/acme-sso \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'Content-Type: application/json' \
  -d '{"provider":"local-oidc","organizationName":"Acme Language Ops","domains":["acme.example"],"redirectUris":["http://localhost:8000/auth/sso/callback"],"requiredEmailDomain":"acme.example"}'
```

Discover a learner's enterprise connection by email domain:

```bash
curl 'http://localhost:8000/v1/auth/sso/discovery?email=learner%40acme.example'
```

Start an enterprise SSO PKCE handoff. The backend stores only the hashed state plus the SSO connection id:

```bash
curl -X POST http://localhost:8000/v1/auth/sso/pkce/start \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"learner@acme.example\",\"redirectUri\":\"http://localhost:8000/auth/sso/callback\",\"codeChallenge\":\"$CODE_CHALLENGE\",\"learnerId\":\"sso-alpha\"}"
```

Complete the callback. The verified code/ID-token email domain must match the connection domain, otherwise the backend rejects account creation:

```bash
curl -X POST http://localhost:8000/v1/auth/sso/pkce/callback \
  -H 'Content-Type: application/json' \
  -d '{"connectionId":"acme-sso","state":"alp_sso_state_...","code":"...","codeVerifier":"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~","redirectUri":"http://localhost:8000/auth/sso/callback"}'
```

Successful enterprise identities are linked as `sso:{connectionId}` and provider status reports `enterpriseSso=true`, `enterpriseSsoDomainDiscovery=true`, and `enterpriseSsoAuthorizationCodePkce=true`.

RS256 JWKS configuration can be supplied as JSON or a URL:

```bash
AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS=google
AI_LANGUAGE_PARTNER_OIDC_GOOGLE_ISSUER=https://accounts.google.com
AI_LANGUAGE_PARTNER_OIDC_GOOGLE_AUDIENCE=com.example.languagepartner
AI_LANGUAGE_PARTNER_OIDC_GOOGLE_JWKS_JSON='{"keys":[{"kty":"RSA","kid":"...","alg":"RS256","use":"sig","n":"...","e":"AQAB"}]}'
# or:
AI_LANGUAGE_PARTNER_OIDC_GOOGLE_JWKS_URL=https://www.googleapis.com/oauth2/v3/certs
```

OIDC-linked accounts can be disabled with an active bearer session and explicit confirmation:

```bash
curl -X DELETE http://localhost:8000/v1/auth/account \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{"confirmation":"delete-my-account"}'
```

Login failures are recorded as hashed email/client attempts. Defaults:

```bash
AI_LANGUAGE_PARTNER_AUTH_MAX_FAILURES=8
AI_LANGUAGE_PARTNER_AUTH_FAILURE_WINDOW_SECONDS=900
```

Registration bursts are also throttled by hashed email/client attempts, independently from login failures:

```bash
AI_LANGUAGE_PARTNER_AUTH_REGISTER_MAX_ATTEMPTS=5
AI_LANGUAGE_PARTNER_AUTH_REGISTER_WINDOW_SECONDS=3600
```

Client-level password-spray risk control blocks login when one client hash spreads failed attempts across many distinct email hashes:

```bash
AI_LANGUAGE_PARTNER_AUTH_RISK_MAX_DISTINCT_EMAILS=12
AI_LANGUAGE_PARTNER_AUTH_RISK_WINDOW_SECONDS=900
```

When triggered, login returns `429` and the audit log records `auth_login_risk_blocked`.

## Token auth mode

```bash
cd apps/api
AI_LANGUAGE_PARTNER_AUTH_MODE=token \
AI_LANGUAGE_PARTNER_AUTH_SECRET=dev-secret \
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Generate a local signed learner token. The default format is expiring `v2:{learner}:{expiresAtUnix}:{hmac}`:

```bash
cd apps/api
AI_LANGUAGE_PARTNER_AUTH_SECRET=dev-secret .venv/bin/python - <<'PY'
from app.main import create_signed_learner_token
print(create_signed_learner_token("alpha", "dev-secret"))
PY
```

Use it:

```bash
curl -H 'X-Learner-Token: v2:alpha:...' http://localhost:8000/v1/profile/me
```

Legacy non-expiring `v1` tokens are rejected unless explicitly enabled:

```bash
AI_LANGUAGE_PARTNER_ALLOW_LEGACY_TOKENS=true
```

## Experiment Decisions

Variant analytics are available to `viewer` and above:

```bash
curl -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: viewer' \
  'http://localhost:8000/v1/experiments/paywall_copy_test_v1/analytics?minimumExposedLearners=30'
```

Decision proposals require `editor`, `reviewer`, or `publisher`. The backend stores the analytics snapshot and guardrail result with the proposal:

```bash
curl -X POST http://localhost:8000/v1/experiments/paywall_copy_test_v1/decisions \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: editor' \
  -H 'X-Admin-User: experiment-editor' \
  -H 'Content-Type: application/json' \
  -d '{"action":"auto","minimumExposedLearners":30,"reason":"Weekly experiment review"}'
```

Applying a decision requires `publisher` and an explicit confirmation. `promote_variant` locks future rollout weight to the selected variant; `pause`, `archive`, `no_winner`, and `collect_more_data` are also recorded as auditable decisions.

```bash
curl -X POST http://localhost:8000/v1/experiments/paywall_copy_test_v1/decisions/expdec_.../apply \
  -H 'X-Admin-Key: local-dev-admin' \
  -H 'X-Admin-Role: publisher' \
  -H 'X-Admin-User: experiment-publisher' \
  -H 'Content-Type: application/json' \
  -d '{"confirmation":"apply-experiment-decision","note":"Approved in experiment review"}'
```

## Verification scripts

```bash
cd apps/api
python scripts/validate_openapi_contract.py
python scripts/verify_docker_smoke.py
python scripts/evaluate_learner_model.py --output ../../artifacts/backend/learner_model_evaluation_20260630.json
python scripts/evaluate_reputation_model.py --output ../../artifacts/backend/reputation_model_evaluation_20260630.json
python scripts/backend_benchmark_105.py
```

`validate_openapi_contract.py` independently parses `contracts/openapi_v0.yaml` and checks every contract path/method against FastAPI routes, including path parameters, required request bodies, declared 200 responses, and undocumented backend routes.

`verify_docker_smoke.py` statically validates `Dockerfile` and `docker-compose.yml`. The current shell used for this run does not have `docker`, `podman`, `colima`, or `nerdctl`, so runtime compose build/run must be performed on a machine with a container runtime installed.

## Docker self-hosting

```bash
cd apps/api
docker compose up --build
```

If Docker is unavailable, run:

```bash
python scripts/verify_docker_smoke.py
```

This validates the checked-in Dockerfile/Compose wiring but does not replace a real Docker runtime build.

## Provider adapters

The API defaults to mock providers and never requires external API keys for local development.
To test adapter wiring without leaking secrets, set provider env vars and inspect `/v1/providers/status`.

```bash
AI_LANGUAGE_PARTNER_LLM_PROVIDER=openai_compatible
AI_LANGUAGE_PARTNER_LLM_API_KEY=...
AI_LANGUAGE_PARTNER_LLM_BASE_URL=https://api.openai.com/v1
AI_LANGUAGE_PARTNER_LLM_MODEL=gpt-4o-mini
AI_LANGUAGE_PARTNER_LLM_RESPONSE_FORMAT=json_object

AI_LANGUAGE_PARTNER_TTS_PROVIDER=openai
AI_LANGUAGE_PARTNER_TTS_API_KEY=...
AI_LANGUAGE_PARTNER_TTS_MODEL=gpt-4o-mini-tts

AI_LANGUAGE_PARTNER_STT_PROVIDER=openai
AI_LANGUAGE_PARTNER_STT_API_KEY=...
AI_LANGUAGE_PARTNER_STT_MODEL=whisper-1
```

The OpenAI STT adapter accepts raw base64 and data URL audio payloads such as:

```text
data:audio/mpeg;base64,...
data:audio/webm;base64,...
data:audio/wav;base64,...
```

The adapter preserves the detected content type and filename extension in the multipart upload.

ElevenLabs TTS can be selected with:

```bash
AI_LANGUAGE_PARTNER_TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

External LLM structured output repair defaults to two attempts and is capped at three:

```bash
AI_LANGUAGE_PARTNER_LLM_REPAIR_ATTEMPTS=2
```

External LLM structured output requires `schemaVersion=turn_payload_v1`. For providers that support strict JSON Schema response format, opt in with:

```bash
AI_LANGUAGE_PARTNER_LLM_RESPONSE_FORMAT=json_schema
```

## Rate limiting

Default local mode uses an in-process memory limiter:

```bash
AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE=240
AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND=memory
```

Production-style Redis wiring:

```bash
AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND=redis
AI_LANGUAGE_PARTNER_REDIS_URL=redis://localhost:6379/0
```

If Redis is selected but unavailable at startup, the API falls back to memory mode and exposes the fallback reason at:

```bash
curl http://localhost:8000/v1/providers/status
```

Rate-limit keys include client host and learner hint, so separate `X-Learner-Id` values on localhost do not immediately collide in local testing.

## Recommendations

`/v1/recommendations/today` returns `signalSummary`, which includes recent correction categories, lapse tags, recent practice rooms, today's completed rooms, and pressure tags used by the simple recommendation scorer.

## Learner Model Evaluation

The live scheduler still uses `hlr_inspired_local_estimator_v1`. To generate offline learner-memory model readiness evidence from local review-grade rows plus deterministic fixtures:

```bash
cd apps/api
python scripts/evaluate_learner_model.py \
  --db-path data/ai_language_partner.sqlite3 \
  --learner-id local-dev \
  --output ../../artifacts/backend/learner_model_evaluation_20260630.json
```

The artifact includes `offline_logistic_memory_model_v1` coefficients, train/eval counts, calibrated-threshold metrics, default-threshold metrics, and `productionTrained=false`. It is not a Duolingo/Birdbrain-scale production model.

Offline reputation/anti-cheat model readiness evidence can be generated from local XP abuse/reputation rows plus deterministic fixtures:

```bash
python scripts/evaluate_reputation_model.py \
  --db-path app/data/language_partner.sqlite3 \
  --output ../../artifacts/backend/reputation_model_evaluation_20260630.json
```

The artifact includes `offline_logistic_reputation_model_v1` coefficients, train/eval counts, calibrated-threshold metrics, default-threshold metrics, and `productionTrained=false`. It is not production learned enforcement and should not make automatic moderation decisions without real moderation outcome labels.

## Course catalog

`/v1/courses` returns Korean-first Japanese speaking course trees. Current seed depth is 2 courses, 10 units, 20 lessons, and 52 practice-room references. Each practice room also carries `courseId`, `unitId`, and `lessonId` metadata.

## CORS

Allowed origins are explicit by default. Override for local Expo/browser targets:

```bash
AI_LANGUAGE_PARTNER_CORS_ORIGINS=http://localhost:8000,http://localhost:8081,http://localhost:19006
```

## Claude frontend real API mode

```bash
cd apps/mobile
EXPO_PUBLIC_USE_MOCK_API=false EXPO_PUBLIC_API_BASE_URL=http://localhost:8000 npx expo start
```
