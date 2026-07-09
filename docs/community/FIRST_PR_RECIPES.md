# First PR Recipes

These recipes are generated from open `good first issue` items. They are
also posted as issue comments so first-time contributors can start without
searching the whole repository.

- Repository: `https://github.com/duct-tape2/ai-language-partner`
- Generated on: `2026-07-09`
- Issues covered: `26`

## [#1: docs: add Korean quick-start for backend mock mode](https://github.com/duct-tape2/ai-language-partner/issues/1)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/ko/index.md`
- `apps/api/README.md`
- `README.md`

**Acceptance signal**

Acceptance: backend setup works without STT/TTS engines; Korean instructions include Python venv, install, run, and health check.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && python -m pytest`

**PR body checklist**

- Link this issue: `Closes #1` or `Refs #1`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#2: docs: add Japanese quick-start for mobile mock mode](https://github.com/duct-tape2/ai-language-partner/issues/2)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/ja/index.md`
- `apps/mobile/README.md`
- `README.md`

**Acceptance signal**

Acceptance: mobile setup covers npm install, Expo web, and mock API defaults.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**PR body checklist**

- Link this issue: `Closes #2` or `Refs #2`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#5: docs: add architecture glossary for dialogue-bank terms](https://github.com/duct-tape2/ai-language-partner/issues/5)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/ARCHITECTURE.md`
- `README.md`

**Acceptance signal**

Acceptance: defines persona, pack, node, lineId, variants, match, confirm, fallback, and global intent.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**PR body checklist**

- Link this issue: `Closes #5` or `Refs #5`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#7: content: review yui v1 beginner dialogue Korean translations](https://github.com/duct-tape2/ai-language-partner/issues/7)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `packs/yui/v1/story.json`
- `packs/yui/v1/variants.csv`

**Acceptance signal**

Acceptance: PR fixes unnatural Korean explanations without changing line IDs.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #7` or `Refs #7`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#8: content: review yui v1 Japanese naturalness](https://github.com/duct-tape2/ai-language-partner/issues/8)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `packs/yui/v1/story.json`
- `packs/yui/v1/variants.csv`

**Acceptance signal**

Acceptance: PR improves Japanese dialogue while preserving beginner level.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #8` or `Refs #8`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#11: content: add notes for Korean learners on particle mistakes](https://github.com/duct-tape2/ai-language-partner/issues/11)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/ko/index.md`
- `apps/mobile/src/grammar/grammarData.ts`
- `apps/mobile/src/mistakes/mistakesData.ts`

**Acceptance signal**

Acceptance: adds concise examples for は/が, を/に, and で/に.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #11` or `Refs #11`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#12: content: add beginner-safe cultural note review checklist](https://github.com/duct-tape2/ai-language-partner/issues/12)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/community/CONTRIBUTOR_LANDING.md`
- `apps/mobile/src/culture/cultureNotes.ts`

**Acceptance signal**

Acceptance: checklist avoids stereotypes and flags context-sensitive terms. ## Accessibility and Mobile UX

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #12` or `Refs #12`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#13: mobile: audit touch target sizes in bottom tabs](https://github.com/duct-tape2/ai-language-partner/issues/13)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `apps/mobile/App.tsx`
- `apps/mobile/src/theme.ts`

**Acceptance signal**

Acceptance: identifies and fixes any tab target below common mobile guidance.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**PR body checklist**

- Link this issue: `Closes #13` or `Refs #13`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#15: mobile: improve empty state copy for Daily Talk pack loading](https://github.com/duct-tape2/ai-language-partner/issues/15)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `apps/mobile/src/screens/DailyTalkScreen.tsx`
- `apps/mobile/src/dialogue/packManager.ts`

**Acceptance signal**

Acceptance: no technical jargon; tells learner what to do next.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**PR body checklist**

- Link this issue: `Closes #15` or `Refs #15`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#16: mobile: document mock mode indicators](https://github.com/duct-tape2/ai-language-partner/issues/16)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/ARCHITECTURE.md`
- `docs/ja/index.md`
- `docs/ko/index.md`

**Acceptance signal**

Acceptance: explains when UI is fixture-backed versus live API-backed.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`

**PR body checklist**

- Link this issue: `Closes #16` or `Refs #16`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#18: mobile: review Korean UI strings for consistency](https://github.com/duct-tape2/ai-language-partner/issues/18)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `apps/mobile/src/i18n.ts`
- `apps/mobile/src/text.ts`
- `apps/mobile/src/screens/`

**Acceptance signal**

Acceptance: consistent honorifics and app terminology. ## Backend and API

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #18` or `Refs #18`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#19: backend: add provider-status example response to docs](https://github.com/duct-tape2/ai-language-partner/issues/19)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `apps/api/README.md`
- `docs/backend/API_RUNBOOK.md`
- `contracts/openapi_v0.yaml`

**Acceptance signal**

Acceptance: includes mock, fallback, and local engine examples.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && python -m pytest`

**PR body checklist**

- Link this issue: `Closes #19` or `Refs #19`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#22: backend: add tests for path traversal rejection on pack zip route](https://github.com/duct-tape2/ai-language-partner/issues/22)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `apps/api/tests/test_api_contract.py`
- `apps/api/app/main.py`

**Acceptance signal**

Acceptance: `..` and slash injection return 400/404 safely.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && python -m pytest`
- `python3 -m unittest discover -s scripts -p 'test_*.py'`

**PR body checklist**

- Link this issue: `Closes #22` or `Refs #22`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#25: tests: add public tree forbidden-file scan](https://github.com/duct-tape2/ai-language-partner/issues/25)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `scripts/check_public_tree.py`
- `scripts/test_claude_for_oss_evidence.py`

**Acceptance signal**

Acceptance: CI fails if generated engines, databases, zip, wav, or npy files are committed.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `python3 -m unittest discover -s scripts -p 'test_*.py'`

**PR body checklist**

- Link this issue: `Closes #25` or `Refs #25`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#29: chore: add issue-label taxonomy document](https://github.com/duct-tape2/ai-language-partner/issues/29)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/community/LABELS.md`
- `docs/community/ISSUE_SEEDS.md`

**Acceptance signal**

Acceptance: documents labels and when maintainers apply them.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**PR body checklist**

- Link this issue: `Closes #29` or `Refs #29`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#31: docs: add FAQ about why no runtime LLM is used](https://github.com/duct-tape2/ai-language-partner/issues/31)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/index.md`

**Acceptance signal**

Acceptance: explains cost, latency, privacy, and quality-control tradeoffs.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**PR body checklist**

- Link this issue: `Closes #31` or `Refs #31`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#34: docs: add Korean troubleshooting notes for backend dependency install](https://github.com/duct-tape2/ai-language-partner/issues/34)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `apps/api/README.md`
- `contracts/openapi_v0.yaml`
- `apps/api/tests/test_api_contract.py`

**Acceptance signal**

Acceptance: covers common Python venv, pip, and macOS command-line tools failures without assuming private maintainer context.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && python -m pytest`

**PR body checklist**

- Link this issue: `Closes #34` or `Refs #34`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#35: docs: add Japanese explanation of the no-runtime-LLM design](https://github.com/duct-tape2/ai-language-partner/issues/35)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/ja/index.md`
- `docs/index.md`
- `docs/ARCHITECTURE.md`

**Acceptance signal**

Acceptance: Japanese text explains cost, privacy, latency, and quality control tradeoffs neutrally.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #35` or `Refs #35`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#36: content: add beginner examples for giving restaurant preferences](https://github.com/duct-tape2/ai-language-partner/issues/36)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `packs/yui/v1/story.json`
- `packs/haruka/v1/story.json`
- `authoring/scenarios/`

**Acceptance signal**

Acceptance: adds beginner-safe Japanese examples with Korean notes and does not introduce generated audio or binary assets.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #36` or `Refs #36`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#40: backend: add OpenAPI example for dialogue pack listing](https://github.com/duct-tape2/ai-language-partner/issues/40)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `contracts/openapi_v0.yaml`
- `contracts/README_API_CONTRACT.md`
- `apps/api/tests/test_api_contract.py`

**Acceptance signal**

Acceptance: `contracts/openapi_v0.yaml` includes a realistic response example for `GET /v1/dialogue/packs`.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && python -m pytest`

**PR body checklist**

- Link this issue: `Closes #40` or `Refs #40`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#42: tests: add script check that issue seed count stays above 30](https://github.com/duct-tape2/ai-language-partner/issues/42)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `scripts/`
- `apps/api/tests/test_api_contract.py`

**Acceptance signal**

Acceptance: CI or a repo script fails if `docs/community/ISSUE_SEEDS.md` parses fewer than 30 issues.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/api && python -m pytest`
- `python3 -m unittest discover -s scripts -p 'test_*.py'`

**PR body checklist**

- Link this issue: `Closes #42` or `Refs #42`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#44: docs: improve first PR walkthrough](https://github.com/duct-tape2/ai-language-partner/issues/44)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/community/FIRST_PR_WALKTHROUGH.md`
- `docs/ko/index.md`
- `docs/ja/index.md`

**Acceptance signal**

Acceptance: improves `docs/community/FIRST_PR_WALKTHROUGH.md` with clearer first-time contributor steps or localized Korean/Japanese notes.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**PR body checklist**

- Link this issue: `Closes #44` or `Refs #44`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#45: docs: add maintainer review checklist](https://github.com/duct-tape2/ai-language-partner/issues/45)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md`

**Acceptance signal**

Acceptance: summarizes useful-review requirements before merging counted external PRs.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**PR body checklist**

- Link this issue: `Closes #45` or `Refs #45`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#46: content: add Korean notes for Japanese sentence-final particles](https://github.com/duct-tape2/ai-language-partner/issues/46)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/ko/index.md`
- `apps/mobile/src/grammar/grammarData.ts`
- `apps/mobile/src/mistakes/mistakesData.ts`

**Acceptance signal**

Acceptance: covers よ, ね, よね, かな at a beginner-safe level with Korean explanations.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #46` or `Refs #46`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#47: content: add cultural-safety review examples](https://github.com/duct-tape2/ai-language-partner/issues/47)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `apps/mobile/src/culture/cultureNotes.ts`
- `docs/community/CONTRIBUTOR_LANDING.md`

**Acceptance signal**

Acceptance: includes examples of stereotypes to avoid and context-sensitive wording to review carefully.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `cd apps/mobile && npm run verify`
- `manual language/content review: explain what wording you checked`

**PR body checklist**

- Link this issue: `Closes #47` or `Refs #47`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md


## [#50: docs: add public roadmap for dialogue-bank packs](https://github.com/duct-tape2/ai-language-partner/issues/50)

<!-- ai-language-partner:first-pr-recipe -->
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

- `docs/community/CONTRIBUTOR_GROWTH_PLAN.md`
- `docs/community/CONTRIBUTOR_SPRINT.md`

**Acceptance signal**

Acceptance: lists planned persona/topic/JLPT pack areas and names which items are suitable for external language review.

**Suggested checks**

- `python3 scripts/check_public_tree.py`
- `manual docs review: verify links and wording`

**PR body checklist**

- Link this issue: `Closes #50` or `Refs #50`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://duct-tape2.github.io/ai-language-partner/
- First issue matcher: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md
