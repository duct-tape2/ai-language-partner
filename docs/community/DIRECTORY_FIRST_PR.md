---
layout: page
title: Directory First PR Fast Lane
---

# Directory First PR Fast Lane

Use this page if you found `ai-language-partner` through GitHub topics, Up For
Grabs, For Good First Issue, CodeTriage, 24 Pull Requests, an awesome list, or
another good-first-issue directory.

You can make a useful first PR without local speech engines, generated audio,
private data, API keys, or app-store builds.

## Start In 60 Seconds

1. Try the hosted demo:
   `https://duct-tape2.github.io/ai-language-partner/demo/`
2. Pick one issue from the table below.
3. Comment `/claim` on the issue if you want the maintainer to reserve it for
   review.
4. Use the browser edit link or Codespaces.
5. Open a focused PR with `Closes #ISSUE_NUMBER` in the body.

## Pick One Lane

| I can help with... | Best issue | First edit |
|---|---|---|
| Korean learner docs | [#46 sentence-final particles](https://github.com/duct-tape2/ai-language-partner/issues/46) | [edit Korean guide](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| Japanese naturalness | [#8 yui dialogue wording](https://github.com/duct-tape2/ai-language-partner/issues/8) | [edit story source](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| Beginner dialogue examples | [#36 restaurant preferences](https://github.com/duct-tape2/ai-language-partner/issues/36) | [edit variants CSV](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) |
| First-time contributor docs | [#44 first PR walkthrough](https://github.com/duct-tape2/ai-language-partner/issues/44) | [edit walkthrough](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/FIRST_PR_WALKTHROUGH.md) |
| Backend/API examples | [#19 provider-status examples](https://github.com/duct-tape2/ai-language-partner/issues/19) | [edit API runbook](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| Local-first explanation | [#31 no-runtime-LLM FAQ](https://github.com/duct-tape2/ai-language-partner/issues/31) | [edit project page](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/index.md) |
| Mobile accessibility | [#13 bottom tab touch targets](https://github.com/duct-tape2/ai-language-partner/issues/13) | [mobile source](https://github.com/duct-tape2/ai-language-partner/tree/main/apps/mobile/src) |
| Focused tests | [#22 path traversal rejection test](https://github.com/duct-tape2/ai-language-partner/issues/22) | [API tests](https://github.com/duct-tape2/ai-language-partner/tree/main/apps/api/tests) |

If the issue you picked is already claimed, use the
[first issue matcher](FIRST_ISSUE_MATCHER.html), the
[no-install first PR board](NO_INSTALL_FIRST_PRS.html), or ask in the
[First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53).

## PR Body Template

```text
Closes #ISSUE_NUMBER

What changed:
- 

Review/check:
- Docs/content review only; no local setup required.

Notes:
- I did not add generated audio, archives, SQLite files, screenshots, secrets,
  local engine files, or private data.
```

## What Maintainers Review

Maintainers check that the PR:

- links one issue
- improves real learner, contributor, API, accessibility, or test value
- keeps generated/private artifacts out of Git
- preserves the no-runtime-LLM Daily Talk path
- is one focused contribution from one real external contributor

Useful docs, language review, accessibility, API example, and test PRs are all
welcome. Stars, comments, listings, and outreach posts do not count as Claude
for OSS evidence by themselves. Only useful merged external PRs count.
