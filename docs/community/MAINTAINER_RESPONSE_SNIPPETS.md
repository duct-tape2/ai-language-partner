# Maintainer Response Snippets

Use these snippets when a real external contributor claims an issue, opens a
PR, or needs a small review nudge. The goal is fast, honest review that helps a
useful PR merge without inflating Claude for OSS evidence.

Do not promise that a PR will count before it is merged and manually reviewed.
Use the public counting policy for the final decision.

## First Response To A New PR

```text
Thanks for the focused PR, @USERNAME. I am reviewing it against the public
first-PR checklist:

- linked issue or problem statement:
- contributor/user value:
- generated/private files:
- no-runtime-LLM Daily Talk rule:
- relevant check:

I will either merge, request a small change, or explain why it should not count
as Claude for OSS evidence.
```

## Docs Or Language Review Looks Good

```text
Thanks, @USERNAME. I checked the PR against the linked issue.

- Issue link: Closes #ISSUE_NUMBER
- Value: improves docs/content/language review for real contributors or learners
- Generated/private assets: none
- Runtime LLM/API dependency: none added
- Check: docs/content review only

Decision: merge after final file review. Counting decision will be made after
merge using the public policy.
```

## Request A Small Change

```text
Thanks, @USERNAME. This is close. Could you make one small follow-up before
merge?

Requested change:
- 

Why:
- 

After that, please leave the PR focused on this issue so it stays easy to
review.
```

## Missing Issue Link

```text
Thanks, @USERNAME. Could you add `Closes #ISSUE_NUMBER` or `Refs #ISSUE_NUMBER`
to the PR body?

That keeps the review trail auditable and helps us avoid counting unrelated or
metric-only changes.
```

## Check Needed

```text
Thanks, @USERNAME. Could you add the smallest relevant check to the PR body?

Examples:
- `Docs/content review only`
- `python -m pytest`
- `npm run verify`
- `OpenAPI YAML stays valid`

No need to run the full stack for a docs-only or language-review PR.
```

## Not Counted But Appreciated

```text
Thanks for the contribution, @USERNAME. I appreciate the help.

I am going to merge / close this as useful housekeeping, but I will not count it
as Claude for OSS evidence because:

- 

The counting policy excludes maintainer PRs, bots, duplicate identities,
metric-only changes, and changes without a clear review trail.
```

## Duplicate Claim Or Collision

```text
Thanks for claiming this, @USERNAME. Someone else is already working on the
same issue, so I want to avoid duplicate work.

Good nearby issues:
- 
- 

If you prefer, reply with your skill/time range and I will suggest one focused
first PR.
```

## Merge Follow-Up

```text
Merged. Thanks, @USERNAME.

This PR is now in the evidence-review queue. That queue is not an automatic
Claude for OSS counting decision; maintainers still verify author identity,
usefulness, issue linkage, review trail, and duplicate-account risk before it
appears in the application packet.
```

## Overdue SLA Reply

```text
Sorry for the slow response, @USERNAME. I am picking this back up now.

Current review status:
- 

Next maintainer action:
- 
```

## Final Counting Checklist

Before recording a merged PR as evidence, confirm:

| Check | Required |
|---|---|
| External contributor | Not maintainer-authored, not a bot, not a duplicate identity |
| Merged PR | Merged into `main` within the last 12 months |
| Useful change | Real docs, content, accessibility, API, test, or maintainer value |
| Review trail | Human maintainer review comment exists |
| Issue/problem link | PR links an issue or clearly states the problem |
| No metric gaming | Not a trivial split, typo-only spam, or cosmetic counter update |

Then regenerate the application evidence and run readiness verification.
