# Claude for OSS Phase A Submission Draft

Use this only for an honest early application before the official
community-builder threshold is met. The Phase B path remains the main route:
20+ unique external contributors with merged PRs in the last 12 months.

Official program page checked on `2026-07-09`:
`https://claude.com/contact-sales/claude-for-oss`

## Current Evidence

- Repository: `https://github.com/duct-tape2/ai-language-partner`
- Contributor page: `https://duct-tape2.github.io/ai-language-partner/`
- Hosted web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Korean contributor page: `https://duct-tape2.github.io/ai-language-partner/ko/`
- Japanese contributor page: `https://duct-tape2.github.io/ai-language-partner/ja/`
- Maintainer account: `duct-tape2`
- License: MIT
- Visibility: public
- Default branch: `main`
- Starter/community issue availability: live index at
  `https://duct-tape2.github.io/ai-language-partner/community/STARTER_ISSUE_INDEX.html`
  (regenerated from GitHub; claimed and assigned work is excluded)
- Repo hygiene action: green (`https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827790`)
- GitHub Pages deployment: green (`https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827257`)
- No-install first PR guide action: green (`https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827750`)
- Governance: `main` branch protection enabled; one approving PR review
  required; force pushes and branch deletion disabled; conversation resolution
  required.
- First PR recipes: posted to eligible `good first issue` tasks and tracked in
  `docs/community/FIRST_PR_RECIPES.md`
- No-install first PR board: browser-editable candidate paths with generated
  issue comments, tracked in `docs/community/NO_INSTALL_FIRST_PRS.md` and
  `docs/community/NO_INSTALL_FIRST_PR_COMMENTS.md`; contributors check the live
  availability index before claiming a task
- Hosted web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Web demo prerelease: `https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09`
- Discovery labels: see the live starter-issue availability index above rather
  than static label counts
- Up For Grabs listing: merged and live
  (`https://github.com/up-for-grabs/up-for-grabs.net/pull/5916`)
- Community-builder evidence: maintained in
  `docs/CLAUDE_FOR_OSS_APPLICATION.md` and refreshed from merged PR data
- Status: not ready for Phase B; do not submit until the official contributor
  threshold is met

## Short Answer

I maintain `ai-language-partner`, a local-first open-source Japanese speaking
practice app for Korean speakers. It uses pre-authored dialogue banks and local
STT/TTS rather than runtime LLM/API calls for the core speaking loop. The repo
is public, MIT-licensed, has CI hygiene checks, contributor docs, issue
templates, a public contributor page, and a maintained starter-issue board for
external language review, accessibility, docs, tests, FastAPI examples, Expo
polish, and contributor coordination.

The project does not yet meet the numeric Claude for OSS thresholds. This
document preserves an honest Phase A narrative, but the active strategy is to
qualify through the community-builder threshold before any submission. The
project is designed as low-cost local-first education infrastructure: useful
for Korean/Japanese language-learning communities where privacy, latency,
quality control, and per-turn API cost matter.

## Longer Project Description

`ai-language-partner` is an open-source local-first Japanese learning app for
Korean speakers. Instead of using a chatbot tutor that generates every response
at runtime, the app uses a reviewed dialogue-bank architecture:

- learner audio is transcribed locally
- the transcription is matched against expected dialogue lines
- the app answers with reviewed, pre-authored persona lines and local TTS assets

This avoids runtime LLM/API dependency on the Daily Talk path. That matters for
education deployments because it keeps per-turn cost near zero, reduces privacy
exposure, lowers latency, and makes responses reviewable for beginner learners.

The public repo includes:

- FastAPI backend
- Expo/React Native mobile app
- OpenAPI and event contracts
- source-only dialogue-bank fixtures
- public-tree hygiene scan
- GitHub Actions workflows
- GitHub Pages contributor page with Korean and Japanese entry pages
- security, code of conduct, contribution docs, PR template, issue templates
- a live starter-issue availability index that removes claimed and assigned work
- browser-editable no-install first PR candidates with issue-specific comments
- hosted mock-mode web demo plus a downloadable Expo web demo prerelease with
  SHA-256 and mock-mode notes
- contributor sprint kickoff, PR welcome, issue welcome, and weekly Claude OSS
  monitor workflows
- fixture-tested contributor evidence counting rules
- issue-specific first PR recipes posted on starter issues

## Current Limitation

The project is newly public and has not yet reached 20 unique external
contributors with merged PRs. That is the main Phase B target. Evidence will be
tracked in `docs/CLAUDE_FOR_OSS_APPLICATION.md` and verified with:

```bash
python scripts/verify_claude_for_oss_readiness.py duct-tape2/ai-language-partner
python scripts/export_claude_for_oss_evidence.py duct-tape2/ai-language-partner --since 2025-07-08
```

## Links

- Repo: `https://github.com/duct-tape2/ai-language-partner`
- Contributor page: `https://duct-tape2.github.io/ai-language-partner/`
- Hosted web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Korean contributor page: `https://duct-tape2.github.io/ai-language-partner/ko/`
- Japanese contributor page: `https://duct-tape2.github.io/ai-language-partner/ja/`
- Issues: `https://github.com/duct-tape2/ai-language-partner/issues`
- Live starter issue availability: `https://duct-tape2.github.io/ai-language-partner/community/STARTER_ISSUE_INDEX.html`
- Actions: `https://github.com/duct-tape2/ai-language-partner/actions`
- Recent green hygiene run: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827790`
- Recent green Pages deployment: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827257`
- Recent green no-install guide run: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28940827750`
- Web demo prerelease: `https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09`
- No-install first PR board: `https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html`
- Contributor evidence doc: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/CLAUDE_FOR_OSS_APPLICATION.md`
