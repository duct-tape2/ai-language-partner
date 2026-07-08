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
   `security`, and `community`.
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
- Regenerate evidence weekly:
  `python scripts/export_claude_for_oss_evidence.py duct-tape2/ai-language-partner`.

## Outreach Copy

> I just opened `ai-language-partner`, a local-first Japanese speaking practice
> app for Korean learners. It uses pre-authored dialogue banks and local STT/TTS
> instead of runtime LLM calls. Looking for small contributions: Korean/Japanese
> wording review, docs, accessibility, FastAPI examples, Expo polish, and tests.

See `docs/community/OUTREACH_PLAYBOOK.md` for Korean, Japanese, and English
variants plus the weekly recruitment cadence.
