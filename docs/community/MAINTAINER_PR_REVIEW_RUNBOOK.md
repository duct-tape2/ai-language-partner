# Maintainer PR Review Runbook

Use this when an external contributor opens a PR that might become Claude for
OSS evidence.

## 1. Build the review packet

```bash
GITHUB_TOKEN=... python scripts/build_pr_review_packet.py duct-tape2/ai-language-partner <PR_NUMBER>
```

The packet summarizes:

- PR author and author association
- changed files
- generated/private file risk
- issue-link or problem-statement signal
- suggested local checks
- a maintainer review comment template
- whether the PR is a possible counted candidate

The packet is a triage aid, not a final counting decision.

New PRs also get an automated review-packet comment from
`.github/workflows/pr-review-packet.yml`. The workflow checks out the trusted
base branch only and reads PR metadata/files through the GitHub API; it does
not execute contributor code.

## 2. Review for usefulness

A PR can count only when it improves real user, contributor, documentation,
test, accessibility, language-review, or maintainability value.

Do not count:

- maintainer-authored PRs
- bots
- duplicate identities
- formatting-only churn
- typo-only spam
- PRs merged only to inflate the metric
- PRs without a review trail

## 3. Leave a human review comment

Use this shape before merge:

```text
Thanks for the focused contribution. I checked:

- linked issue / problem statement:
- user or contributor value:
- no generated/private assets:
- no runtime-LLM dependency added:
- relevant check:

Decision: merge / request changes / merge but do not count for Claude for OSS evidence.
```

The automated PR welcome comment is not a review decision.
The automated PR review-packet comment is also not a review decision; it only
prepares the checklist so the human review can be faster and more consistent.

## 4. Merge and update evidence

After a useful external PR is merged:

```bash
GITHUB_TOKEN=... python scripts/export_claude_for_oss_evidence.py duct-tape2/ai-language-partner --since 2025-07-08
GITHUB_TOKEN=... python scripts/update_claude_application_evidence.py duct-tape2/ai-language-partner --since 2025-07-08
GITHUB_TOKEN=... python scripts/verify_claude_for_oss_readiness.py duct-tape2/ai-language-partner
```

Commit the evidence doc only when the generated table and manual review agree.

## 5. Apply only when ready

Submit the Phase B Claude for OSS application only when the readiness script
proves 20 unique external merged PR contributors and the evidence packet links
the counted PRs.
