---
layout: home
title: AI Language Partner
---

# AI Language Partner

Local-first Japanese speaking practice for Korean learners.

The project uses reviewed dialogue banks, local STT/TTS, and an Expo + FastAPI
stack. The Daily Talk path avoids runtime LLM calls so beginner dialogue can be
reviewed, low-latency, privacy-conscious, and low-cost to deploy.

## First PRs Welcome

You do not need local speech engines, generated audio, private data, or API
keys to make a useful first contribution.

Start here:

- [Hosted web demo](demo/)
- [GitHub /contribute](https://github.com/duct-tape2/ai-language-partner/contribute)
- [Call for contributors](community/CALL_FOR_CONTRIBUTORS.html)
- [한국어 기여자 모집](community/CALL_FOR_CONTRIBUTORS_KO.html)
- [日本語 contributor call](community/CALL_FOR_CONTRIBUTORS_JA.html)
- [Call for contributors discussion](https://github.com/duct-tape2/ai-language-partner/discussions/55)
- [First issue matcher](community/FIRST_ISSUE_MATCHER.html)
- [Five-minute first PR](community/FIVE_MINUTE_FIRST_PR.html)
- [한국어 5분 첫 PR](community/FIVE_MINUTE_FIRST_PR_KO.html)
- [日本語 5分 first PR](community/FIVE_MINUTE_FIRST_PR_JA.html)
- [Language review first PR kit](community/LANGUAGE_REVIEW_FIRST_PR_KIT.html)
- [한국어 기여자 안내](ko/)
- [日本語コントリビューター向け案内](ja/)
- [Starter issue index](community/STARTER_ISSUE_INDEX.html)
- [No-install first PR board](community/NO_INSTALL_FIRST_PRS.html)
- [First PR recipes](community/FIRST_PR_RECIPES.html)
- [Contributor landing](community/CONTRIBUTOR_LANDING.html)
- [First PR walkthrough](community/FIRST_PR_WALKTHROUGH.html)
- [Installable demo release plan](community/INSTALLABLE_DEMO_RELEASE_PLAN.html)
- [First PR help desk discussion](https://github.com/duct-tape2/ai-language-partner/discussions/53)
- [Contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml)
- [한국어 contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ko.yml)
- [日本語 contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ja.yml)

Useful first contribution lanes:

| Lane | Good contribution shape |
|---|---|
| Korean/Japanese docs | Setup notes, learner-facing explanations, glossary improvements |
| Japanese naturalness review | Beginner-safe wording, tone consistency, cultural-safety review |
| Dialogue content | Reviewed `story.json` or `variants.csv` source changes |
| Mobile accessibility | Labels, touch targets, contrast, small-screen layout fixes |
| FastAPI/OpenAPI examples | Curl examples, provider-status docs, local STT/TTS setup notes |
| Tests/tooling | Small fixture tests, repo checks, CI-safe verification scripts |

## Project Links

- [GitHub repository](https://github.com/duct-tape2/ai-language-partner)
- [Hosted web demo](https://duct-tape2.github.io/ai-language-partner/demo/)
- [GitHub /contribute](https://github.com/duct-tape2/ai-language-partner/contribute)
- [Open issues](https://github.com/duct-tape2/ai-language-partner/issues)
- [Good first issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- [Discussions](https://github.com/duct-tape2/ai-language-partner/discussions)
- [Actions](https://github.com/duct-tape2/ai-language-partner/actions)

## Claude for OSS Evidence

This repository is building toward the Claude for OSS community-builder route:
20+ unique external contributors with useful merged PRs in the last 12 months.

Current evidence and counting rules are public:

- [Claude for OSS application evidence](CLAUDE_FOR_OSS_APPLICATION.html)
- [PR review and counting policy](community/PR_REVIEW_AND_COUNTING_POLICY.html)
- [20 contributor sprint](community/CONTRIBUTOR_SPRINT.html)

Only real external contributors with useful merged PRs count. Maintainer-authored
PRs, bots, duplicate identities, and metric-only changes are excluded.

## Local-First Shape

The runtime flow is intentionally narrow:

1. Learner audio is transcribed locally.
2. The transcript is matched against reviewed dialogue-bank lines.
3. The app answers with local TTS or prebuilt voice assets.

The public repo is source-only. Generated audio, local engines, databases,
archives, screenshots, private notes, and secrets stay out of Git.
