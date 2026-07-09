# Contributor Landing

Welcome. This project is looking for small, useful public contributions from
language learners, Korean/Japanese reviewers, mobile accessibility reviewers,
FastAPI/API docs contributors, and test-minded developers.

You do not need local speech engines, private data, generated audio, or API
keys to make a useful first PR.

Start with the [public contributor page](https://duct-tape2.github.io/ai-language-partner/),
the [hosted web demo](https://duct-tape2.github.io/ai-language-partner/demo/),
the [한국어 guide](https://duct-tape2.github.io/ai-language-partner/ko/), the
[日本語 guide](https://duct-tape2.github.io/ai-language-partner/ja/), or the
[starter issue index](STARTER_ISSUE_INDEX.md) if you want a lane-by-lane list
of currently open tasks.

If you want to help make the project easier for non-contributors to try, see
the [installable demo release plan](INSTALLABLE_DEMO_RELEASE_PLAN.md).

For the lowest-friction route, use the
[five-minute first PR guide](FIVE_MINUTE_FIRST_PR.md). It links directly to
browser-editable issues and includes a PR body template.

For step-by-step issue-specific guidance, see the
[first PR recipes](FIRST_PR_RECIPES.md).

If you want to contribute without installing anything, start with the
[no-install first PR board](NO_INSTALL_FIRST_PRS.md). It links directly to
GitHub web-editor tasks for docs, Korean/Japanese review, and beginner dialogue
content.

## Pick Your Lane

| I can help with... | Start here | Good first outcome |
|---|---|---|
| Korean docs or learner notes | [Korean docs issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22+label%3Adocs) | Clearer setup or learner explanation |
| Japanese naturalness review | [Language-review issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22language-review%22) | Beginner-safe wording and tone |
| Dialogue content review | [Content issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Acontent) | Reviewed source text, no generated assets |
| Mobile accessibility | [Accessibility issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Aaccessibility) | Better labels, touch targets, or layout |
| FastAPI/OpenAPI examples | [Backend docs issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Abackend+label%3Adocs) | Clear examples or provider docs |
| Tests/tooling | [Tests issues](https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Atests) | Focused repo, API, or fixture checks |

If you are not sure where to start, ask in the
[First PR help desk discussion](https://github.com/duct-tape2/ai-language-partner/discussions/53),
comment on the
[20 contributor sprint kickoff issue](https://github.com/duct-tape2/ai-language-partner/issues/52)
with the lane you prefer, or open a
[contributor interest issue](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml).

## Fastest First PR Path

1. Pick one issue from the table above.
2. Comment `/claim` on the issue if you want to avoid duplicate work.
3. Read the [first PR walkthrough](FIRST_PR_WALKTHROUGH.md).
4. Make one focused change.
5. Open a PR that links the issue and names the check you ran.

For docs or language review, the fastest path is the
[five-minute first PR guide](FIVE_MINUTE_FIRST_PR.md) or the
[no-install first PR board](NO_INSTALL_FIRST_PRS.md): pick a row, use the
direct edit link, and submit a focused browser-only PR.

If you need a maintainer to suggest a first issue, use the
[contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml).

Docs-only and language-review PRs are welcome when they improve real learner or
contributor experience.

## What Not To Commit

Please do not commit:

- generated `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, or screenshot files
- local speech engine folders
- private notes, handoff files, or personal paths
- secrets, tokens, API keys, or private datasets

The repository intentionally keeps generated voice assets and local engines out
of Git.

## Project Rule

The Daily Talk path avoids runtime LLM/API calls. Learner audio is transcribed
locally, matched against reviewed dialogue-bank lines, and answered with local
TTS assets. Contributions should preserve that local-first design.

## Claude for OSS Note

This project is building toward the Claude for OSS community-builder route:
20+ unique external contributors with useful merged PRs in the last 12 months.

Only real external contributors count. Maintainer-authored PRs, bots, duplicate
identities, and trivial metric-only PRs are excluded. See the
[PR review and counting policy](PR_REVIEW_AND_COUNTING_POLICY.md).
