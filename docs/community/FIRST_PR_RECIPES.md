# First PR Recipes

These recipes are generated from open `good first issue` items. They are
also posted as issue comments so first-time contributors can start without
searching the whole repository.

- Repository: `https://github.com/duct-tape2/ai-language-partner`
- Generated on: `2026-07-20`
- Issues covered: `25`

## [#1: docs: add Korean quick-start for backend mock mode](https://github.com/duct-tape2/ai-language-partner/issues/1)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/ko/index.md`
- `apps/api/README.md`
- `README.md`

**Done when**

Acceptance: backend setup works without STT/TTS engines; Korean instructions

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && .venv/bin/python -m pytest`

**Open the PR**

- Write `Closes #1` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#2: docs: add Japanese quick-start for mobile mock mode](https://github.com/duct-tape2/ai-language-partner/issues/2)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/ja/index.md`
- `apps/mobile/README.md`
- `README.md`

**Done when**

Acceptance: mobile setup covers npm install, Expo web, and mock API defaults.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**Open the PR**

- Write `Closes #2` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#5: docs: add architecture glossary for dialogue-bank terms](https://github.com/duct-tape2/ai-language-partner/issues/5)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/ARCHITECTURE.md`
- `README.md`

**Done when**

Acceptance: defines persona, pack, node, lineId, variants, match, confirm,

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**Open the PR**

- Write `Closes #5` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#7: content: review yui v1 beginner dialogue Korean translations](https://github.com/duct-tape2/ai-language-partner/issues/7)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `packs/yui/v1/story.json`
- `packs/yui/v1/variants.csv`

**Done when**

Acceptance: PR fixes unnatural Korean explanations without changing line IDs.

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #7` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#8: content: review yui v1 Japanese naturalness](https://github.com/duct-tape2/ai-language-partner/issues/8)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `packs/yui/v1/story.json`
- `packs/yui/v1/variants.csv`

**Done when**

Acceptance: PR improves Japanese dialogue while preserving beginner level.

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #8` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#11: content: add notes for Korean learners on particle mistakes](https://github.com/duct-tape2/ai-language-partner/issues/11)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/ko/index.md`
- `apps/mobile/src/grammar/grammarData.ts`
- `apps/mobile/src/mistakes/mistakesData.ts`

**Done when**

Acceptance: adds concise examples for は/が, を/に, and で/に.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #11` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#12: content: add beginner-safe cultural note review checklist](https://github.com/duct-tape2/ai-language-partner/issues/12)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/community/CONTRIBUTOR_LANDING.md`
- `apps/mobile/src/culture/cultureNotes.ts`

**Done when**

Acceptance: checklist avoids stereotypes and flags context-sensitive terms.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #12` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#13: mobile: audit touch target sizes in bottom tabs](https://github.com/duct-tape2/ai-language-partner/issues/13)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/mobile/App.tsx`
- `apps/mobile/scripts/verify-frontend-regressions.mjs`

**Done when**

- Each of the five bottom tabs has a stable target height of at least 48 logical pixels.
- Labels and icons remain centered and do not overlap at narrow mobile width.
- Existing accessibility metadata remains intact.
- `cd apps/mobile && npm run verify` passes.
- `python3 scripts/check_public_tree.py` passes.
- The PR body includes `Closes #13` and briefly explains the accessibility benefit.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `python3 -m unittest discover -s scripts -p 'test_*.py'`

**Open the PR**

- Write `Closes #13` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#14: mobile: add accessibility labels to voice preview controls](https://github.com/duct-tape2/ai-language-partner/issues/14)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/mobile/App.tsx`
- `apps/mobile/src/screens/`
- `apps/mobile/src/components.tsx`

**Done when**

- An idle voice card announces the play action and identifies the character/style.
- The currently playing card announces its playing state and the same voice identity.
- Labels are derived from existing localized strings rather than new hardcoded Korean or Japanese copy.
- Existing Voice Gallery behavior and TypeScript checks remain passing.
- The PR body includes `Closes #14` and names the checks run.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**Open the PR**

- Write `Closes #14` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#15: mobile: improve empty state copy for Daily Talk pack loading](https://github.com/duct-tape2/ai-language-partner/issues/15)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/mobile/src/screens/DailyTalkScreen.tsx`
- `apps/mobile/src/dialogue/packManager.ts`

**Done when**

Acceptance: no technical jargon; tells learner what to do next.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**Open the PR**

- Write `Closes #15` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#16: mobile: document mock mode indicators](https://github.com/duct-tape2/ai-language-partner/issues/16)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/ARCHITECTURE.md`
- `docs/ja/index.md`
- `docs/ko/index.md`

**Done when**

- A small table or equivalent compact section distinguishes **mock**, **real with healthy API**, and **real with a read fallback**.
- Every documented label and fallback statement matches current source behavior.
- The documentation does not imply that selecting real mode guarantees a live speech engine.
- The PR changes only `docs/ARCHITECTURE.md` and includes `Closes #16`.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**Open the PR**

- Write `Closes #16` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#18: mobile: review Korean UI strings for consistency](https://github.com/duct-tape2/ai-language-partner/issues/18)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/mobile/src/i18n.ts`
- `apps/mobile/src/text.ts`
- `apps/mobile/src/screens/`

**Done when**

Acceptance: consistent honorifics and app terminology.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #18` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#19: backend: add provider-status example response to docs](https://github.com/duct-tape2/ai-language-partner/issues/19)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/api/README.md`
- `docs/backend/API_RUNBOOK.md`
- `contracts/openapi_v0.yaml`

**Done when**

- All three labeled examples are present and valid JSON after replacing explanatory placeholders with JSON strings.
- Field names and nesting match the current implementation.
- The surrounding text explains that `externalApiKeysRequired` is `false` and that fallback status is diagnostic rather than proof that a live external engine succeeded.
- The change stays within `docs/backend/API_RUNBOOK.md`.
- The PR body includes `Closes #19`.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && .venv/bin/python -m pytest`

**Open the PR**

- Write `Closes #19` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#21: backend: add tests for malformed dialogue pack metadata](https://github.com/duct-tape2/ai-language-partner/issues/21)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/api/README.md`
- `contracts/openapi_v0.yaml`
- `apps/api/tests/test_api_contract.py`

**Done when**

- Invalid manifest JSON does not crash pack listing.
- Safe default metadata is asserted explicitly.
- Existing valid dialogue-pack behavior remains covered and passing.
- The PR body includes `Closes #21` and names the checks run.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && .venv/bin/python -m pytest`
- `python3 -m unittest discover -s scripts -p 'test_*.py'`

**Open the PR**

- Write `Closes #21` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#29: chore: add issue-label taxonomy document](https://github.com/duct-tape2/ai-language-partner/issues/29)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/community/LABELS.md`
- `docs/community/ISSUE_SEEDS.md`

**Done when**

Acceptance: documents labels and when maintainers apply them.

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**Open the PR**

- Write `Closes #29` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#31: docs: add FAQ about why no runtime LLM is used](https://github.com/duct-tape2/ai-language-partner/issues/31)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/index.md`

**Done when**

Acceptance: explains cost, latency, privacy, and quality-control tradeoffs.

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**Open the PR**

- Write `Closes #31` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#34: docs: add Korean troubleshooting notes for backend dependency install](https://github.com/duct-tape2/ai-language-partner/issues/34)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/api/README.md`
- `contracts/openapi_v0.yaml`
- `apps/api/tests/test_api_contract.py`

**Done when**

Acceptance: covers common Python venv, pip, and macOS command-line tools

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && .venv/bin/python -m pytest`

**Open the PR**

- Write `Closes #34` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#35: docs: add Japanese explanation of the no-runtime-LLM design](https://github.com/duct-tape2/ai-language-partner/issues/35)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/ja/index.md`
- `docs/index.md`
- `docs/ARCHITECTURE.md`

**Done when**

Acceptance: Japanese text explains cost, privacy, latency, and quality

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #35` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#36: content: add beginner examples for giving restaurant preferences](https://github.com/duct-tape2/ai-language-partner/issues/36)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `packs/yui/v1/story.json`
- `packs/haruka/v1/story.json`
- `authoring/scenarios/`

**Done when**

Acceptance: adds beginner-safe Japanese examples with Korean notes and does

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #36` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#44: docs: improve first PR walkthrough](https://github.com/duct-tape2/ai-language-partner/issues/44)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/community/FIRST_PR_WALKTHROUGH.md`

**Done when**

- A first-time contributor can complete the change in GitHub without a local clone.
- The walkthrough directly answers whether documentation PRs are taken seriously.
- The new guidance distinguishes useful docs work from splitting trivial typo-only changes for metrics.
- The PR changes only `docs/community/FIRST_PR_WALKTHROUGH.md` and includes `Closes #44`.

**Verify**

- `manual docs review: use GitHub Markdown preview and verify links and wording`

**Open the PR**

- Write `Closes #44` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#45: docs: add maintainer review checklist](https://github.com/duct-tape2/ai-language-partner/issues/45)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md`

**Done when**

Acceptance: summarizes useful-review requirements before merging counted

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**Open the PR**

- Write `Closes #45` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#46: content: add Korean notes for Japanese sentence-final particles](https://github.com/duct-tape2/ai-language-partner/issues/46)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/ko/index.md`
- `apps/mobile/src/grammar/grammarData.ts`
- `apps/mobile/src/mistakes/mistakesData.ts`

**Done when**

Acceptance: covers よ, ね, よね, かな at a beginner-safe level with Korean

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #46` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#47: content: add cultural-safety review examples](https://github.com/duct-tape2/ai-language-partner/issues/47)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/mobile/src/culture/cultureNotes.ts`
- `docs/community/CONTRIBUTOR_LANDING.md`

**Done when**

Acceptance: includes examples of stereotypes to avoid and context-sensitive

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**Open the PR**

- Write `Closes #47` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#49: backend: add malformed multipart upload test for STT endpoint](https://github.com/duct-tape2/ai-language-partner/issues/49)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `apps/api/tests/test_api_contract.py`
- `apps/api/app/main.py`

**Done when**

- Missing multipart `file` returns `422`.
- A non-upload value under `file` returns `422`.
- An empty uploaded file returns `422`.
- Error details are clear and do not expose tracebacks or filesystem paths.
- Existing valid multipart upload and JSON mock-mode tests remain passing.

**Verify**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && .venv/bin/python -m pytest`
- `python3 -m unittest discover -s scripts -p 'test_*.py'`

**Open the PR**

- Write `Closes #49` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53


## [#50: docs: add public roadmap for dialogue-bank packs](https://github.com/duct-tape2/ai-language-partner/issues/50)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Keep this to one useful change for this issue.

**Inspect**

- `docs/community/CONTRIBUTOR_GROWTH_PLAN.md`
- `docs/community/CONTRIBUTOR_SPRINT.md`

**Done when**

Acceptance: lists planned persona/topic/JLPT pack areas and names which

**Verify**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**Open the PR**

- Write `Closes #50` in the PR body.
- Say what changed and name the check or review you completed.
- Do not add generated media, archives, local engines, databases, secrets,
  screenshots, or private data.

**Need a route?**

- Browser edit: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Code or tests without local setup: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- Ask a maintainer: https://github.com/duct-tape2/ai-language-partner/discussions/53
