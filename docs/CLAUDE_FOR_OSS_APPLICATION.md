# Claude for OSS Application Evidence

This document is the application packet for Anthropic's Claude for Open Source
program.

## Repository

- Repository: `https://github.com/duct-tape2/ai-language-partner`
- Contributor page: `https://duct-tape2.github.io/ai-language-partner/`
- Hosted web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Korean contributor page: `https://duct-tape2.github.io/ai-language-partner/ko/`
- Japanese contributor page: `https://duct-tape2.github.io/ai-language-partner/ja/`
- Maintainer: `duct-tape2`
- License: MIT
- Project: local-first Japanese speaking practice for Korean learners
- Program page checked: `https://claude.com/contact-sales/claude-for-oss`
  on `2026-07-09`
- Account eligibility audit: `docs/CLAUDE_FOR_OSS_ACCOUNT_AUDIT.md`
- Core principle: no runtime LLM or external generation API on the Daily Talk
  request path

## Official Criteria Checklist

| Track | Current status | Evidence |
|---|---|---|
| Maintainer: 500 dependent repos / 100 dependent packages / 200k monthly downloads | Not yet met | New public OSS launch; package split is future work |
| Core contributor to recognized foundation/language project | Not claimed | Not the basis for this application |
| Active contributor: 100 merged PRs into repos not owned by maintainer in last 12 months | Not yet met | Possible long-term supporting route |
| Community builder: one maintained repo has 20+ unique external contributors with merged PRs in last 12 months | Target route | Track in the table below after public launch |
| Critical infrastructure: OpenSSF criticality score >= 0.4 | Not yet met | Not expected for initial launch |

## Phase A Application Text

Use this only if applying before the 20-external-contributor threshold is met:

> I maintain `ai-language-partner`, a local-first open-source Japanese learning
> app for Korean speakers. The project avoids runtime LLM/API dependency for
> its core speaking loop: learner audio is transcribed locally, matched against
> pre-authored dialogue-bank lines, and answered with pre-synthesized local
> voice assets. This makes the architecture useful for low-cost education
> deployments where latency, privacy, and per-turn API cost matter. The project
> is newly public and does not yet meet the numeric thresholds, but it is built
> to support community-authored dialogue banks, language review, and local-first
> learning infrastructure.

## Phase B Application Text

Use this after the repo has 20+ unique external contributors with merged PRs in
the last 12 months:

> I maintain `ai-language-partner`, a local-first open-source Japanese learning
> app for Korean speakers. The project has 20+ unique external contributors with
> merged PRs in the last 12 months. Its architecture avoids runtime LLM/API
> dependency for the core speaking loop, making it useful for low-cost education
> deployments where latency, privacy, and per-turn API cost matter.

## Contributor Evidence

Fill this only with real merged PRs from unique external contributors. Do not
count maintainer-authored PRs, bots, duplicate identities, or trivial spam.

- Evidence generated from: `duct-tape2/ai-language-partner`
- Since: `2025-07-09`
- Unique external contributors counted: `0`
- Status: `NOT READY for Phase B`
- Remaining contributors needed: `20`

| # | Contributor | PR URL | Area | Merged date | Review note |
|---|---|---|---|---|---|

Current table has fewer than 20 rows because the official community-builder
threshold is not met yet. Do not submit Phase B with this status.

## Verification Links

- Contributors: `https://github.com/duct-tape2/ai-language-partner/graphs/contributors`
- Contributor page: `https://duct-tape2.github.io/ai-language-partner/`
- Hosted web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Korean contributor page: `https://duct-tape2.github.io/ai-language-partner/ko/`
- Japanese contributor page: `https://duct-tape2.github.io/ai-language-partner/ja/`
- Merged PRs: `https://github.com/duct-tape2/ai-language-partner/pulls?q=is%3Apr+is%3Amerged`
- Actions: `https://github.com/duct-tape2/ai-language-partner/actions`
- Recent green repo hygiene run: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827790`
- Recent green starter issue index run: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28936333894`
- Recent green Pages deployment: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827257`
- Recent green no-install guide run: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827750`
- Governance: `main` branch protection enabled; one approving PR review
  required; force pushes and branch deletion disabled; conversation resolution
  required; the 20-contributor sprint kickoff issue is pinned.
- First PR recipes: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_RECIPES.md`
- No-install first PR board: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md`
- No-install issue guide comments: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PR_COMMENTS.md`
- Hosted web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Web demo prerelease: `https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09`
- Discovery labels: 34 open `up-for-grabs` issues, 24 open
  `first-timers-only` issues, and 26 open `good first issue` items
- Up For Grabs listing PR: merged and live
  `https://github.com/up-for-grabs/up-for-grabs.net/pull/5916`
- Awesome for Beginners listing PR: `https://github.com/MunGell/awesome-for-beginners/pull/2072`
  - Hosted-demo follow-up: `https://github.com/MunGell/awesome-for-beginners/pull/2072#issuecomment-4921750431`
- Awesome for Non-Programmers listing PR: `https://github.com/szabgab/awesome-for-non-programmers/pull/107`
  - Hosted-demo follow-up: `https://github.com/szabgab/awesome-for-non-programmers/pull/107#issuecomment-4921750475`
- Awesome Language Learning listing PR: `https://github.com/Vuizur/awesome-language-learning/pull/31`
  - Hosted-demo follow-up: `https://github.com/Vuizur/awesome-language-learning/pull/31#issuecomment-4921750535`
- Awesome Japanese Learning Resources listing PR:
  `https://github.com/ailanguagetutor/awesome-japanese-learning-resources/pull/5`
- Awesome Japanese Study Materials listing PR:
  `https://github.com/naghim/Awesome-Japanese-Study-Materials/pull/8`
- Awesome Japanese listing suggestion issue: deferred until the project has a
  clearer app-store/release-build path; hosted demo is now the first maturity
  step
  `https://github.com/yudataguy/awesome-japanese/issues/149`
- Discovery listing tracker: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/DISCOVERY_LISTINGS.md`
- Dependency graph: `https://github.com/duct-tape2/ai-language-partner/network/dependencies`

## Local Evidence Commands

Run these before applying:

```bash
git shortlog -sn --since=2025-07-09 --all
find . -type f | grep -Ei 'local_engines|artifacts|handoff|reference_archive|\\.sqlite|\\.zip|\\.wav|\\.npy' && exit 1 || true
git grep -nE 'sk-[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}' -- .
python scripts/export_claude_for_oss_evidence.py duct-tape2/ai-language-partner --since=2025-07-09
python scripts/audit_claude_for_oss_account.py --owner duct-tape2 --since=2025-07-09 --out docs/CLAUDE_FOR_OSS_ACCOUNT_AUDIT.md
python scripts/update_claude_application_evidence.py duct-tape2/ai-language-partner --since=2025-07-09
python scripts/verify_claude_for_oss_readiness.py duct-tape2/ai-language-partner
```

See `docs/community/PUBLISHING_AND_APPLICATION_CHECKLIST.md` for the full
publish, issue-seeding, and application sequence.
