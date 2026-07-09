---
layout: page
title: Language Review First PR Kit
---

# Language Review First PR Kit

Use this kit if you can review Japanese naturalness, Korean learner wording,
dialogue examples, or cultural-safety notes but do not want to install Expo,
FastAPI, local STT/TTS engines, generated audio, or API keys.

The goal is one focused, useful PR from one real reviewer. A small docs or
content review can count for the community-builder route when it improves the
project and is merged after maintainer review. Do not split tiny typo-only
changes just to increase contributor count.

## Fastest Review Routes

| I can review... | Issue | Source file | Safe first PR shape |
|---|---|---|---|
| Beginner Japanese naturalness | [#8](https://github.com/duct-tape2/ai-language-partner/issues/8) | [`packs/yui/v1/story.json`](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) | Improve 2-5 beginner-safe Japanese lines while preserving every ID |
| Korean translations for learner dialogue | [#7](https://github.com/duct-tape2/ai-language-partner/issues/7) | [`packs/yui/v1/story.json`](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) | Clarify Korean `ko` or `assistantKo` wording without changing Japanese intent |
| Restaurant preference variants | [#36](https://github.com/duct-tape2/ai-language-partner/issues/36) | [`packs/yui/v1/variants.csv`](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) | Replace awkward placeholder-like variants with natural beginner alternatives |
| Japanese honorific or tone consistency | [#37](https://github.com/duct-tape2/ai-language-partner/issues/37) | [`packs/yui/v1/story.json`](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) | Make onboarding examples consistent in politeness level |
| Cultural-safety examples | [#47](https://github.com/duct-tape2/ai-language-partner/issues/47) | [`apps/mobile/src/culture/cultureNotes.ts`](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/culture/cultureNotes.ts) | Add or improve examples that avoid stereotypes and overgeneralization |
| Korean notes for sentence-final particles | [#46](https://github.com/duct-tape2/ai-language-partner/issues/46) | [`docs/ko/index.md`](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) | Explain `よ`, `ね`, `よね`, or `かな` in beginner-safe Korean |

## What To Change

Good first language-review PRs usually change one of these:

- `assistantText`: Japanese persona line shown by the app.
- `assistantKo`: Korean explanation for an assistant line.
- `choices[].text`: Japanese learner response option.
- `choices[].ko`: Korean meaning for a learner response option.
- `variants.csv` `text`: accepted utterance variants for a learner line.
- `variants.csv` `ko`: Korean gloss for that variant.
- `cultureNotes.ts` `bodyKo`: Korean cultural explanation shown to learners.

Keep the review narrow. It is better to improve three well-explained lines than
to rewrite the whole pack.

## Do Not Change

For a first language-review PR, avoid changing structure:

- Do not change `schemaVersion`, `personaId`, `packVersion`, `scenarioId`,
  `nodeId`, `assistantLineId`, `lineId`, `nextNodeId`, or `intent`.
- Do not add generated audio, screenshots, `.zip`, `.wav`, `.npy`, `.sqlite`,
  `.db`, local engine folders, private notes, tokens, or API keys.
- Do not rewrite every line into a different voice or level.
- Do not introduce runtime LLM/API dependencies.
- Do not add machine-generated text dumps without human review notes.

## Review Checklist

Before opening the PR, check:

- Japanese remains beginner-safe for the issue's level.
- Korean explanations are useful for Korean learners, not only literal.
- The speaker tone stays consistent.
- Cultural notes avoid "Japanese people always..." style claims.
- JSON, CSV, and TypeScript syntax still follow the existing shape.
- The PR body links the issue with `Closes #ISSUE_NUMBER`.

## PR Body Template

```text
Closes #ISSUE_NUMBER

What changed:
- Reviewed the wording in FILE_OR_SECTION.
- Improved ...

Review/check:
- Docs/content/language review only; no local setup required.
- I preserved existing IDs and file structure.

Notes:
- I did not add generated audio, archives, SQLite files, screenshots, secrets,
  or local engine files.
```

## If You Are Not Sure

Use one of these entry points:

- First issue matcher: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md`
- No-install first PR board: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md`
- Japanese contributor interest form: `https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ja.yml`
- Korean contributor interest form: `https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ko.yml`
- First PR help desk: `https://github.com/duct-tape2/ai-language-partner/discussions/53`
