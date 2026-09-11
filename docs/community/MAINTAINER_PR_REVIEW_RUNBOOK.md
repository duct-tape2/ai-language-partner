# Maintainer PR Review Runbook

Use this when an external contributor opens a PR that might become Claude for
OSS evidence.

## Pre-merge checklist

Complete these checks before merging a focused external PR:

- [ ] **Scope:** The PR addresses one linked issue or clearly stated problem and
  does not bundle unrelated cleanup.
- [ ] **Contribution:** The author is an external contributor, not the
  maintainer, a bot, or a duplicate identity.
- [ ] **Usefulness:** The change improves a real user, contributor,
  documentation, test, accessibility, language-review, or maintainability
  workflow.
- [ ] **Safety:** The diff contains no generated media, private data, secrets,
  local engines, databases, archives, or unnecessary runtime-LLM dependency.
- [ ] **Validation:** The relevant automated check or manual review is named and
  its result is understood.
- [ ] **Review trail:** A human maintainer has reviewed the change and left a
  comment that records what was verified.
- [ ] **Merge decision:** Required status checks pass, the acceptance criteria
  are satisfied, and any remaining concerns are resolved before merging.

After merging, place the PR in the evidence-review queue only if the manual
review agrees that it is a useful external contribution. The queue label is a
review cue, not an automatic counting decision.

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

Use `docs/community/MAINTAINER_RESPONSE_SNIPPETS.md` for fast, consistent
responses when a PR needs a first reply, a small change request, a missing issue
link, or a final merge follow-up.

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

- The `PR Merge Followup` workflow labels external merged PRs as
  `merged-external-pr-candidate` and posts a thank-you comment.
- Treat that label as an evidence-review queue only. It is not a final counting
  decision.

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
