# Starter Issue Index

This is a snapshot of open issues that are useful for first-time
contributors. Pick one focused issue, comment if you want to claim it,
then follow the first PR walkthrough.

- Repository: `https://github.com/duct-tape2/ai-language-partner`
- Generated on: `2026-07-08`
- Open issues indexed: `51`
- Good first issues: `18`
- Help wanted issues: `15`
- First PR walkthrough: [docs/community/FIRST_PR_WALKTHROUGH.md](FIRST_PR_WALKTHROUGH.md)
- Contributor interest form: `https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml`

Only useful, reviewable PRs count toward the Claude for OSS
community-builder evidence. Do not split trivial changes just to create
more PRs.

## Lane Summary

| Lane | Open issues | Best for |
|---|---:|---|
| Mobile/accessibility | 11 | Expo, React Native, labels, touch targets, layout |
| Backend/API docs | 14 | FastAPI, OpenAPI, local STT/TTS setup, provider docs |
| Tests/tooling | 4 | Python, TypeScript, CI, repo checks, fixtures |
| Dialogue/content review | 11 | Japanese naturalness, Korean learner notes, JLPT review |
| Release/community | 6 | Issue taxonomy, review process, roadmap, sprint coordination |
| Korean/Japanese docs | 5 | Setup docs, architecture notes, learner-facing explanation |

## Mobile/accessibility

Expo, React Native, labels, touch targets, layout.

| Issue | Labels |
|---|---|
| [#13: mobile: audit touch target sizes in bottom tabs](https://github.com/duct-tape2/ai-language-partner/issues/13) | `good first issue`, `accessibility`, `mobile` |
| [#14: mobile: add accessibility labels to voice preview controls](https://github.com/duct-tape2/ai-language-partner/issues/14) | `accessibility`, `mobile` |
| [#15: mobile: improve empty state copy for Daily Talk pack loading](https://github.com/duct-tape2/ai-language-partner/issues/15) | `good first issue`, `mobile` |
| [#16: mobile: document mock mode indicators](https://github.com/duct-tape2/ai-language-partner/issues/16) | `docs`, `mobile` |
| [#17: mobile: add regression check for duplicate screen labels](https://github.com/duct-tape2/ai-language-partner/issues/17) | `help wanted`, `mobile`, `tests` |
| [#18: mobile: review Korean UI strings for consistency](https://github.com/duct-tape2/ai-language-partner/issues/18) | `good first issue`, `language-review`, `mobile` |
| [#27: tests: add mobile package script inventory check](https://github.com/duct-tape2/ai-language-partner/issues/27) | `mobile`, `tests` |
| [#33: mobile: plan Expo SDK upgrade for transitive security advisories](https://github.com/duct-tape2/ai-language-partner/issues/33) | `help wanted`, `mobile`, `security` |
| [#38: mobile: add accessibility label audit for Daily Talk controls](https://github.com/duct-tape2/ai-language-partner/issues/38) | `help wanted`, `accessibility`, `mobile` |
| [#39: mobile: improve small-screen layout for Voice Gallery cards](https://github.com/duct-tape2/ai-language-partner/issues/39) | `accessibility`, `mobile` |
| [#48: mobile: add regression guard for missing accessibility labels](https://github.com/duct-tape2/ai-language-partner/issues/48) | `accessibility`, `mobile`, `tests` |

## Backend/API docs

FastAPI, OpenAPI, local STT/TTS setup, provider docs.

| Issue | Labels |
|---|---|
| [#3: docs: clarify local whisper.cpp setup on macOS](https://github.com/duct-tape2/ai-language-partner/issues/3) | `help wanted`, `docs`, `stt` |
| [#4: docs: clarify AivisSpeech and VOICEVOX-compatible setup](https://github.com/duct-tape2/ai-language-partner/issues/4) | `help wanted`, `docs`, `tts` |
| [#6: docs: add API curl examples for Daily Talk endpoints](https://github.com/duct-tape2/ai-language-partner/issues/6) | `help wanted`, `docs`, `backend` |
| [#19: backend: add provider-status example response to docs](https://github.com/duct-tape2/ai-language-partner/issues/19) | `good first issue`, `docs`, `backend` |
| [#20: backend: add dialogue match threshold explanation](https://github.com/duct-tape2/ai-language-partner/issues/20) | `docs`, `backend` |
| [#21: backend: add tests for malformed dialogue pack metadata](https://github.com/duct-tape2/ai-language-partner/issues/21) | `help wanted`, `backend`, `tests` |
| [#22: backend: add tests for path traversal rejection on pack zip route](https://github.com/duct-tape2/ai-language-partner/issues/22) | `good first issue`, `backend`, `tests` |
| [#23: backend: document Redis rate-limit optional setup](https://github.com/duct-tape2/ai-language-partner/issues/23) | `docs`, `backend` |
| [#24: backend: add OpenAPI examples for auth device trust](https://github.com/duct-tape2/ai-language-partner/issues/24) | `docs`, `backend` |
| [#28: tests: add pack source schema check](https://github.com/duct-tape2/ai-language-partner/issues/28) | `help wanted`, `backend`, `tests` |
| [#34: docs: add Korean troubleshooting notes for backend dependency install](https://github.com/duct-tape2/ai-language-partner/issues/34) | `good first issue`, `docs`, `backend` |
| [#40: backend: add OpenAPI example for dialogue pack listing](https://github.com/duct-tape2/ai-language-partner/issues/40) | `good first issue`, `docs`, `backend` |
| [#41: backend: document provider fallback labels](https://github.com/duct-tape2/ai-language-partner/issues/41) | `docs`, `backend` |
| [#49: backend: add malformed multipart upload test for STT endpoint](https://github.com/duct-tape2/ai-language-partner/issues/49) | `backend`, `tests` |

## Tests/tooling

Python, TypeScript, CI, repo checks, fixtures.

| Issue | Labels |
|---|---|
| [#25: tests: add public tree forbidden-file scan](https://github.com/duct-tape2/ai-language-partner/issues/25) | `good first issue`, `tests` |
| [#26: tests: add README command smoke script](https://github.com/duct-tape2/ai-language-partner/issues/26) | `docs`, `tests` |
| [#42: tests: add script check that issue seed count stays above 30](https://github.com/duct-tape2/ai-language-partner/issues/42) | `good first issue`, `tests`, `community` |
| [#43: tests: add contributor evidence script fixture test](https://github.com/duct-tape2/ai-language-partner/issues/43) | `tests`, `community` |

## Dialogue/content review

Japanese naturalness, Korean learner notes, JLPT review.

| Issue | Labels |
|---|---|
| [#7: content: review yui v1 beginner dialogue Korean translations](https://github.com/duct-tape2/ai-language-partner/issues/7) | `good first issue`, `content`, `language-review` |
| [#8: content: review yui v1 Japanese naturalness](https://github.com/duct-tape2/ai-language-partner/issues/8) | `help wanted`, `content`, `language-review` |
| [#9: content: review haruka v1 polite-tone consistency](https://github.com/duct-tape2/ai-language-partner/issues/9) | `content`, `language-review` |
| [#10: content: review ren v1 casual-tone consistency](https://github.com/duct-tape2/ai-language-partner/issues/10) | `content`, `language-review` |
| [#11: content: add notes for Korean learners on particle mistakes](https://github.com/duct-tape2/ai-language-partner/issues/11) | `good first issue`, `docs`, `content` |
| [#12: content: add beginner-safe cultural note review checklist](https://github.com/duct-tape2/ai-language-partner/issues/12) | `docs`, `content` |
| [#35: docs: add Japanese explanation of the no-runtime-LLM design](https://github.com/duct-tape2/ai-language-partner/issues/35) | `help wanted`, `docs`, `language-review` |
| [#36: content: add beginner examples for giving restaurant preferences](https://github.com/duct-tape2/ai-language-partner/issues/36) | `good first issue`, `content`, `language-review` |
| [#37: content: review honorific consistency in onboarding examples](https://github.com/duct-tape2/ai-language-partner/issues/37) | `content`, `language-review` |
| [#46: content: add Korean notes for Japanese sentence-final particles](https://github.com/duct-tape2/ai-language-partner/issues/46) | `content`, `language-review` |
| [#47: content: add cultural-safety review examples](https://github.com/duct-tape2/ai-language-partner/issues/47) | `docs`, `content` |

## Release/community

Issue taxonomy, review process, roadmap, sprint coordination.

| Issue | Labels |
|---|---|
| [#29: chore: add issue-label taxonomy document](https://github.com/duct-tape2/ai-language-partner/issues/29) | `good first issue`, `docs`, `community` |
| [#30: chore: add release checklist for generated voice assets](https://github.com/duct-tape2/ai-language-partner/issues/30) | `docs`, `release` |
| [#44: docs: improve first PR walkthrough](https://github.com/duct-tape2/ai-language-partner/issues/44) | `good first issue`, `docs`, `community` |
| [#45: docs: add maintainer review checklist](https://github.com/duct-tape2/ai-language-partner/issues/45) | `docs`, `community` |
| [#50: docs: add public roadmap for dialogue-bank packs](https://github.com/duct-tape2/ai-language-partner/issues/50) | `help wanted`, `docs`, `community` |
| [#52: community: 20 contributor sprint kickoff](https://github.com/duct-tape2/ai-language-partner/issues/52) | `help wanted`, `community` |

## Korean/Japanese docs

Setup docs, architecture notes, learner-facing explanation.

| Issue | Labels |
|---|---|
| [#1: docs: add Korean quick-start for backend mock mode](https://github.com/duct-tape2/ai-language-partner/issues/1) | `help wanted`, `good first issue`, `docs` |
| [#2: docs: add Japanese quick-start for mobile mock mode](https://github.com/duct-tape2/ai-language-partner/issues/2) | `help wanted`, `good first issue`, `docs` |
| [#5: docs: add architecture glossary for dialogue-bank terms](https://github.com/duct-tape2/ai-language-partner/issues/5) | `good first issue`, `docs` |
| [#31: docs: add FAQ about why no runtime LLM is used](https://github.com/duct-tape2/ai-language-partner/issues/31) | `good first issue`, `docs` |
| [#32: docs: add comparison table for dialogue bank versus chatbot tutor](https://github.com/duct-tape2/ai-language-partner/issues/32) | `help wanted`, `docs` |
