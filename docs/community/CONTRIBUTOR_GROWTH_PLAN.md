# Contributor Growth Plan

The Claude for OSS approval target is the community-builder criterion:
20+ unique external contributors with merged PRs in the last 12 months.

## Rules

- Count only real humans who are not the maintainer.
- Count one meaningful merged PR per person.
- Do not count bots, duplicate identities, trivial whitespace PRs, or PRs
  created only to inflate metrics.
- Every contributor PR should link an issue and receive a human review comment.

## Launch Sequence

1. Publish the sanitized `ai-language-partner` repository.
2. Open the issues from `docs/community/ISSUE_SEEDS.md`.
3. Add labels: `good first issue`, `help wanted`, `docs`, `content`,
   `language-review`, `accessibility`, `tests`, `backend`, `mobile`,
   `security`, `community`, and `claimed`.
4. Invite contributors from language-learning, Korean/Japanese, Expo, FastAPI,
   and local-first AI communities.
5. Merge only reviewable, useful PRs.
6. Update `docs/CLAUDE_FOR_OSS_APPLICATION.md` after every accepted external PR.

## Operating Cadence

- Keep at least 30 open, scoped issues available while contributor recruitment
  is active.
- Respond to first-time contributor PRs within 24 hours whenever possible.
- Prefer one useful PR per contributor over splitting one person's work into
  many PRs.
- Use `docs/community/PR_REVIEW_AND_COUNTING_POLICY.md` before counting a PR
  toward the Claude for OSS evidence packet.
- Run the 20-contributor sprint from `docs/community/CONTRIBUTOR_SPRINT.md`
  so outreach, issue assignment, review, and evidence updates stay auditable.
- Keep the contributor funnel monitor current so open external PRs, claim
  signals, and contributor interest issues are visible from the kickoff issue.
- Use the `claimed` label from `/claim` comments to avoid assigning duplicate
  work; redirect second claimers to a nearby first issue when needed.
- Regenerate evidence weekly:
  `python scripts/export_claude_for_oss_evidence.py duct-tape2/ai-language-partner`.

## Discovery Channel Follow-Up

- ELUSOC project-admin registration remains a time-sensitive contributor
  acquisition path. Use the verified project copy and personal-data boundary in
  `docs/community/ELUSOC_PROJECT_ADMIN_APPLICATION.md`; do not add program
  labels until the official platform confirms registration or acceptance.
- Up For Grabs is the first live external contributor discovery channel.
- The hosted web demo gives directory reviewers a click-to-inspect path:
  `https://duct-tape2.github.io/ai-language-partner/demo/`.
- Awesome Japanese should still wait for a stronger app-store or release-build
  story. The maintainer explicitly asked to come back after the project is more
  mature, so do not reopen that listing route until the remaining release gap is
  fixed. Track the gap in `docs/community/INSTALLABLE_DEMO_RELEASE_PLAN.md`.
- Keep open listing PRs current, but avoid duplicate submissions to the same
  directory.

## Outreach Copy

> I just opened `ai-language-partner`, a local-first Japanese speaking practice
> app for Korean learners. It uses pre-authored dialogue banks and local STT/TTS
> instead of runtime LLM calls. Looking for small contributions: Korean/Japanese
> wording review, docs, accessibility, FastAPI examples, Expo polish, and tests.

See `docs/community/OUTREACH_PLAYBOOK.md` for Korean, Japanese, and English
variants plus the weekly recruitment cadence. Use
`docs/community/SHARE_KIT.md` for short community posts and direct-message
variants.
