# First Issue Matcher

Use this page when you want to contribute but do not know which issue to pick.
Choose the row that matches your skill and time. Each route is scoped so a
maintainer can review it quickly.

You do not need generated audio, local speech engines, private data, API keys,
or app-store builds for any issue in the browser-only section.

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
| Python tests | 30-60 min | [#22 path traversal rejection test](https://github.com/duct-tape2/ai-language-partner/issues/22) | [API tests](https://github.com/duct-tape2/ai-language-partner/tree/main/apps/api/tests) | `python -m pytest` |
| Repo/community process | 10-30 min | [#45 maintainer checklist](https://github.com/duct-tape2/ai-language-partner/issues/45) | [edit review runbook](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md) | Docs review only |

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

## What Counts

The project is building toward the Claude for OSS community-builder route:
20+ unique external contributors with useful merged PRs in the last 12 months.

Useful docs, content review, accessibility, API example, and test PRs can all
count after maintainer review. Maintainer-authored PRs, bots, duplicate
identities, trivial typo splits, and metric-only changes do not count.
