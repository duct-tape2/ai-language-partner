---
layout: page
title: Call For Contributors
---

# Call For Contributors

`ai-language-partner` is looking for small, useful first PRs from language
learners, Korean/Japanese reviewers, docs contributors, accessibility reviewers,
FastAPI users, and local-first education builders.

Share link:

`https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html`

## Try The Project

- Hosted web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Repository: `https://github.com/duct-tape2/ai-language-partner`
- Call for contributors discussion:
  `https://github.com/duct-tape2/ai-language-partner/discussions/55`
- Korean call for contributors:
  `https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS_KO.html`
- Japanese call for contributors:
  `https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS_JA.html`
- Korean contributor guide: `https://duct-tape2.github.io/ai-language-partner/ko/`
- Japanese contributor guide: `https://duct-tape2.github.io/ai-language-partner/ja/`

The hosted demo uses fixture-backed mock providers. You do not need local
speech engines, generated audio, private data, or API keys to inspect the app
shape or make a useful first contribution.

## Best First PRs

Use one of these routes if you want a focused contribution that can be reviewed
quickly:

| I can help with | Start here | Good first PR shape |
|---|---|---|
| Korean setup/docs | `https://github.com/duct-tape2/ai-language-partner/issues/1` | Clarify backend mock-mode setup in Korean |
| Japanese setup/docs | `https://github.com/duct-tape2/ai-language-partner/issues/2` | Clarify mobile mock-mode setup in Japanese |
| Japanese naturalness | `https://github.com/duct-tape2/ai-language-partner/issues/8` | Review beginner-safe dialogue wording |
| Korean learner notes | `https://github.com/duct-tape2/ai-language-partner/issues/46` | Explain sentence-final particles for Korean learners |
| Dialogue content | `https://github.com/duct-tape2/ai-language-partner/issues/36` | Add beginner-safe restaurant preference examples |
| Backend/API docs | `https://github.com/duct-tape2/ai-language-partner/issues/19` | Add provider-status example responses |
| Community/release docs | `https://github.com/duct-tape2/ai-language-partner/issues/50` | Improve the public dialogue-bank roadmap |

More choices:

- First issue matcher: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md`
- Five-minute first PR: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md`
- Japanese five-minute first PR: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR_JA.md`
- No-install first PR board: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md`
- Starter issue index: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/STARTER_ISSUE_INDEX.md`
- First PR help desk: `https://github.com/duct-tape2/ai-language-partner/discussions/53`
- Japanese contributor interest form: `https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ja.yml`

## How To Claim

1. Pick one issue.
2. Comment `/claim` on the issue if you want to avoid duplicate work; the repo
   will add the `claimed` label for maintainer triage.
3. Make one focused change.
4. Open a PR with `Closes #ISSUE_NUMBER` in the body.
5. Mention the check you ran, or say it was docs/content/language review only.

The repo replies automatically with first-PR guidance when someone comments
`/claim` and marks the issue with the `claimed` label.

## Guardrails

Please do not commit generated audio, archives, SQLite files, screenshots,
local engine folders, secrets, private notes, or private datasets.

The Daily Talk path avoids runtime LLM/API calls. Contributions should preserve
that local-first design.

## Claude For OSS Note

This project is building toward the Claude for OSS community-builder route:
20+ unique external contributors with useful merged PRs in the last 12 months.

Only real external contributors with useful merged PRs count. Maintainer PRs,
bots, duplicate identities, and metric-only changes are excluded.
