# Claude for OSS Phase A Submission Draft

Use this only for an honest early application before the official
community-builder threshold is met. The Phase B path remains the main route:
20+ unique external contributors with merged PRs in the last 12 months.

Official program page checked: `https://claude.com/contact-sales/claude-for-oss`

## Current Evidence

- Repository: `https://github.com/duct-tape2/ai-language-partner`
- Maintainer account: `duct-tape2`
- License: MIT
- Visibility: public
- Default branch: `main`
- Starter/community issues: 51
- Repo hygiene action: green (`https://github.com/duct-tape2/ai-language-partner/actions/runs/28933532532`)
- Community-builder count: 0 unique external merged PR contributors so far
- Status: not ready for Phase B; suitable only for a "Don't quite fit?" early
  application

## Short Answer

I maintain `ai-language-partner`, a local-first open-source Japanese speaking
practice app for Korean speakers. It uses pre-authored dialogue banks and local
STT/TTS rather than runtime LLM/API calls for the core speaking loop. The repo
is public, MIT-licensed, has CI hygiene checks, contributor docs, issue
templates, and 51 scoped starter/community issues for external language review,
accessibility, docs, tests, FastAPI examples, Expo polish, and contributor
coordination.

The project does not yet meet the numeric Claude for OSS thresholds. I am
applying under the "Don't quite fit?" guidance because the project is designed
as low-cost local-first education infrastructure: useful for Korean/Japanese
language-learning communities where privacy, latency, quality control, and
per-turn API cost matter.

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
- security, code of conduct, contribution docs, PR template, issue templates
- 51 scoped issues for first-time and external contributors
- contributor sprint kickoff, PR welcome, issue welcome, and weekly Claude OSS
  monitor workflows
- fixture-tested contributor evidence counting rules

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
- Issues: `https://github.com/duct-tape2/ai-language-partner/issues`
- Good first issues: `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22`
- Actions: `https://github.com/duct-tape2/ai-language-partner/actions`
- Recent green hygiene run: `https://github.com/duct-tape2/ai-language-partner/actions/runs/28933532532`
- Contributor evidence doc: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/CLAUDE_FOR_OSS_APPLICATION.md`
