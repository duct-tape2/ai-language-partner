# Five-Minute First PR

Use this route if you want to make a useful first contribution without
installing Expo, FastAPI, local STT/TTS engines, generated audio, API keys, or
private data.

Korean-speaking contributors can use the
[한국어 5분 첫 PR guide](FIVE_MINUTE_FIRST_PR_KO.md).

Pick one row, open the edit link, make one focused improvement, and create a
pull request from GitHub's web editor.

If you want to see what the project feels like before editing docs or content,
open the hosted mock-mode demo:

`https://duct-tape2.github.io/ai-language-partner/demo/`

If you want to avoid duplicate work, comment `/claim` on the issue first. An
automated reply will point you back to the PR checklist for that issue and add
the `claimed` label for maintainer triage.

Only real, useful PRs count toward Claude for OSS evidence. Do not split
trivial typo fixes into separate PRs just to increase numbers.

## Fastest Routes

The table below is the shortest menu. If a row is already claimed, use the
full [no-install first PR board](NO_INSTALL_FIRST_PRS.md), which has 27
browser-editable issue slots.

| Route | Best if you can... | Issue | Edit link |
|---|---|---|---|
| Korean setup notes | Explain setup or troubleshooting in Korean | [#1](https://github.com/duct-tape2/ai-language-partner/issues/1) | [edit API runbook](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| Japanese mobile guide | Improve Japanese setup guidance | [#2](https://github.com/duct-tape2/ai-language-partner/issues/2) | [edit Japanese guide](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ja/index.md) |
| Dialogue glossary | Explain project terms clearly | [#5](https://github.com/duct-tape2/ai-language-partner/issues/5) | [edit architecture doc](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ARCHITECTURE.md) |
| Korean translation review | Review Korean learner-facing dialogue text | [#7](https://github.com/duct-tape2/ai-language-partner/issues/7) | [edit story source](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| Korean learner notes | Add concise notes for Korean learners | [#11](https://github.com/duct-tape2/ai-language-partner/issues/11) | [edit Korean guide](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| Korean UI consistency | Review Korean app labels | [#18](https://github.com/duct-tape2/ai-language-partner/issues/18) | [edit i18n source](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/i18n.ts) |
| No-runtime-LLM FAQ | Explain the local-first dialogue-bank design | [#31](https://github.com/duct-tape2/ai-language-partner/issues/31) | [edit contributor page](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/index.md) |
| Backend troubleshooting | Add Korean Python install troubleshooting notes | [#34](https://github.com/duct-tape2/ai-language-partner/issues/34) | [edit API runbook](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| Restaurant examples | Add beginner-safe restaurant preference examples | [#36](https://github.com/duct-tape2/ai-language-partner/issues/36) | [edit variants CSV](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) |
| First PR instructions | Improve onboarding instructions for future contributors | [#44](https://github.com/duct-tape2/ai-language-partner/issues/44) | [edit walkthrough](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/FIRST_PR_WALKTHROUGH.md) |

## PR Title Examples

- `docs: improve Korean backend mock setup`
- `docs: clarify Japanese mobile mock mode`
- `content: review yui Korean beginner dialogue`
- `docs: explain no-runtime-LLM dialogue bank`

## PR Body Template

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

## Before You Open The PR

- Keep the change focused on one issue.
- Link the issue with `Closes #ISSUE_NUMBER`.
- Do not commit `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshots,
  local engine folders, private notes, tokens, or API keys.
- If you are not sure what to choose, ask in the
  [First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53)
  or open the
  [contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml).
