# First Issue Matcher

Use this page when you want to contribute but do not know which issue to pick.
Choose the row that matches your skill and time. Each route is scoped so a
maintainer can review it quickly.

You do not need generated audio, local speech engines, private data, API keys,
or app-store builds for any issue in the browser-only section.

## Pick In One Minute

1. Choose the row that matches your language, docs, mobile, API, or test skill.
2. Open the issue and comment `/claim` if you want the maintainer to reserve it
   for you.
3. Open the edit link, make one focused change, and put
   `Closes #ISSUE_NUMBER` in the PR body.

If you are here from an external directory, the safest first PR routes are
docs, wording review, beginner dialogue examples, API examples, and focused
tests. They are useful even when you do not run the full mobile/backend stack.

## Thirty-Second Match

| If you can help with... | Time | Start with | Edit path | Check |
|---|---:|---|---|---|
| Korean wording or learner notes | 10-30 min | [#46 sentence-final particles](https://github.com/duct-tape2/ai-language-partner/issues/46) | [edit Korean guide](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) | Docs/content review only |
| Japanese naturalness | 10-30 min | [#8 yui Japanese naturalness](https://github.com/duct-tape2/ai-language-partner/issues/8) | [edit story source](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) | Keep line IDs stable |
| Beginner dialogue examples | 10-30 min | [#36 restaurant preferences](https://github.com/duct-tape2/ai-language-partner/issues/36) | [edit variants CSV](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) | Keep CSV columns unchanged |
| First-time OSS docs | 10-20 min | [#44 first PR walkthrough](https://github.com/duct-tape2/ai-language-partner/issues/44) | [edit walkthrough](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/FIRST_PR_WALKTHROUGH.md) | Docs review only |
| Local-first explanation | 10-20 min | [#31 no-runtime-LLM FAQ](https://github.com/duct-tape2/ai-language-partner/issues/31) | [edit contributor page](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/index.md) | Docs review only |
| Backend examples | 20-45 min | [#19 provider status examples](https://github.com/duct-tape2/ai-language-partner/issues/19) | [edit API runbook](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) | Docs review or API check |
| OpenAPI examples | 30-60 min | [#24 auth device trust examples](https://github.com/duct-tape2/ai-language-partner/issues/24) | [edit OpenAPI contract](https://github.com/duct-tape2/ai-language-partner/edit/main/contracts/openapi_v0.yaml) | Keep YAML valid |
| Mobile accessibility | 30-60 min | [#13 bottom tab touch targets](https://github.com/duct-tape2/ai-language-partner/issues/13) | [mobile source](https://github.com/duct-tape2/ai-language-partner/tree/main/apps/mobile/src) | `npm run verify` if possible |
| Python tests | 30-60 min | [#49 malformed STT upload test](https://github.com/duct-tape2/ai-language-partner/issues/49) | [API tests](https://github.com/duct-tape2/ai-language-partner/tree/main/apps/api/tests) | `python -m pytest` |
| Repo/community process | 10-30 min | [#45 maintainer checklist](https://github.com/duct-tape2/ai-language-partner/issues/45) | [edit review runbook](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md) | Docs review only |

## Low-Collision Starter-Issue Menu

These routes spread first PRs across different files and review lanes so
contributors can choose work that improves the learner experience or project
without all colliding on the same edit.

| Slot | Best for | Issue | First file |
|---:|---|---|---|
| 1 | Korean setup docs | [#1](https://github.com/duct-tape2/ai-language-partner/issues/1) | [`docs/backend/API_RUNBOOK.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 2 | Japanese mobile docs | [#2](https://github.com/duct-tape2/ai-language-partner/issues/2) | [`docs/ja/index.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ja/index.md) |
| 3 | macOS STT setup docs | [#3](https://github.com/duct-tape2/ai-language-partner/issues/3) | [`docs/backend/API_RUNBOOK.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 4 | Local TTS setup docs | [#4](https://github.com/duct-tape2/ai-language-partner/issues/4) | [`docs/backend/API_RUNBOOK.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 5 | Architecture glossary | [#5](https://github.com/duct-tape2/ai-language-partner/issues/5) | [`docs/ARCHITECTURE.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ARCHITECTURE.md) |
| 6 | API curl examples | [#6](https://github.com/duct-tape2/ai-language-partner/issues/6) | [`docs/backend/API_RUNBOOK.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 7 | Korean translation review | [#7](https://github.com/duct-tape2/ai-language-partner/issues/7) | [`packs/yui/v1/story.json`](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| 8 | Japanese naturalness | [#8](https://github.com/duct-tape2/ai-language-partner/issues/8) | [`packs/yui/v1/story.json`](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| 9 | Korean learner notes | [#11](https://github.com/duct-tape2/ai-language-partner/issues/11) | [`docs/ko/index.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| 10 | Cultural review checklist | [#12](https://github.com/duct-tape2/ai-language-partner/issues/12) | [`docs/community/CONTRIBUTOR_LANDING.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/CONTRIBUTOR_LANDING.md) |
| 11 | Mock-mode docs | [#16](https://github.com/duct-tape2/ai-language-partner/issues/16) | [`docs/ARCHITECTURE.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ARCHITECTURE.md) |
| 12 | Korean UI consistency | [#18](https://github.com/duct-tape2/ai-language-partner/issues/18) | [`apps/mobile/src/i18n.ts`](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/i18n.ts) |
| 13 | Provider-status examples | [#19](https://github.com/duct-tape2/ai-language-partner/issues/19) | [`docs/backend/API_RUNBOOK.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 14 | Match-threshold explanation | [#20](https://github.com/duct-tape2/ai-language-partner/issues/20) | [`docs/ARCHITECTURE.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ARCHITECTURE.md) |
| 15 | OpenAPI examples | [#24](https://github.com/duct-tape2/ai-language-partner/issues/24) | [`contracts/openapi_v0.yaml`](https://github.com/duct-tape2/ai-language-partner/edit/main/contracts/openapi_v0.yaml) |
| 16 | Local-first FAQ | [#31](https://github.com/duct-tape2/ai-language-partner/issues/31) | [`docs/index.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/index.md) |
| 17 | Restaurant examples | [#36](https://github.com/duct-tape2/ai-language-partner/issues/36) | [`packs/yui/v1/variants.csv`](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) |
| 18 | Fallback labels | [#41](https://github.com/duct-tape2/ai-language-partner/issues/41) | [`docs/backend/API_RUNBOOK.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 19 | Sentence-final particles | [#46](https://github.com/duct-tape2/ai-language-partner/issues/46) | [`docs/ko/index.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| 20 | Cultural-safety examples | [#47](https://github.com/duct-tape2/ai-language-partner/issues/47) | [`apps/mobile/src/culture/cultureNotes.ts`](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/culture/cultureNotes.ts) |

If your first choice is already claimed, pick another row in the same skill
area or ask in the
[First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53).

If a listed issue is already claimed, use the
[no-install first PR board](NO_INSTALL_FIRST_PRS.md) for more browser-editable
options.

## Quick Claim

1. Open the issue.
2. Comment `/claim`.
3. Make one focused change.
4. Open a PR with `Closes #ISSUE_NUMBER` in the body.
5. Mention the check you ran, or write `Docs/content review only`.

The repo will reply automatically with first-PR guidance after `/claim` and
mark the issue with the `claimed` label for maintainer triage.

## Good PR Shape

```text
Closes #ISSUE_NUMBER

What changed:
- 

Review/check:
- Docs/content review only; no local setup required.

Notes:
- I did not add generated audio, archives, SQLite files, screenshots, secrets,
  or local engine files.
```

## What Makes a Useful Contribution

Useful docs, content review, accessibility, API examples, and tests solve a
learner or project need. Keep the work focused, link the issue or problem in
your PR, and avoid splitting trivial typo fixes across separate PRs.
