# Claude for OSS Application Evidence

This document is the application packet for Anthropic's Claude for Open Source
program.

## Repository

- Repository: `https://github.com/sinmb79/ai-language-partner`
- Maintainer: `sinmb79`
- License: MIT
- Project: local-first Japanese speaking practice for Korean learners
- Program page checked: `https://claude.com/contact-sales/claude-for-oss`
- Core principle: no runtime LLM or external generation API on the Daily Talk
  request path

## Official Criteria Checklist

| Track | Current status | Evidence |
|---|---|---|
| Maintainer: 500 dependent repos / 100 dependent packages / 200k monthly downloads | Not yet met | New public OSS launch; package split is future work |
| Core contributor to recognized foundation/language project | Not claimed | Not the basis for this application |
| Active contributor: 100 merged PRs into repos not owned by maintainer in last 12 months | Not yet met | Possible long-term supporting route |
| Community builder: one maintained repo has 20+ unique external contributors with merged PRs in last 12 months | Target route | Track in the table below after public launch |
| Critical infrastructure: OpenSSF criticality score >= 0.4 | Not yet met | Not expected for initial launch |

## Phase A Application Text

Use this only if applying before the 20-external-contributor threshold is met:

> I maintain `ai-language-partner`, a local-first open-source Japanese learning
> app for Korean speakers. The project avoids runtime LLM/API dependency for
> its core speaking loop: learner audio is transcribed locally, matched against
> pre-authored dialogue-bank lines, and answered with pre-synthesized local
> voice assets. This makes the architecture useful for low-cost education
> deployments where latency, privacy, and per-turn API cost matter. The project
> is newly public and does not yet meet the numeric thresholds, but it is built
> to support community-authored dialogue banks, language review, and local-first
> learning infrastructure.

## Phase B Application Text

Use this after the repo has 20+ unique external contributors with merged PRs in
the last 12 months:

> I maintain `ai-language-partner`, a local-first open-source Japanese learning
> app for Korean speakers. The project has 20+ unique external contributors with
> merged PRs in the last 12 months. Its architecture avoids runtime LLM/API
> dependency for the core speaking loop, making it useful for low-cost education
> deployments where latency, privacy, and per-turn API cost matter.

## Contributor Evidence

Fill this only with real merged PRs from unique external contributors. Do not
count maintainer-authored PRs, bots, duplicate identities, or trivial spam.

| # | Contributor | PR URL | Area | Merged date | Review note |
|---|---|---|---|---|---|
| 1 | TBD | TBD | TBD | TBD | TBD |
| 2 | TBD | TBD | TBD | TBD | TBD |
| 3 | TBD | TBD | TBD | TBD | TBD |
| 4 | TBD | TBD | TBD | TBD | TBD |
| 5 | TBD | TBD | TBD | TBD | TBD |
| 6 | TBD | TBD | TBD | TBD | TBD |
| 7 | TBD | TBD | TBD | TBD | TBD |
| 8 | TBD | TBD | TBD | TBD | TBD |
| 9 | TBD | TBD | TBD | TBD | TBD |
| 10 | TBD | TBD | TBD | TBD | TBD |
| 11 | TBD | TBD | TBD | TBD | TBD |
| 12 | TBD | TBD | TBD | TBD | TBD |
| 13 | TBD | TBD | TBD | TBD | TBD |
| 14 | TBD | TBD | TBD | TBD | TBD |
| 15 | TBD | TBD | TBD | TBD | TBD |
| 16 | TBD | TBD | TBD | TBD | TBD |
| 17 | TBD | TBD | TBD | TBD | TBD |
| 18 | TBD | TBD | TBD | TBD | TBD |
| 19 | TBD | TBD | TBD | TBD | TBD |
| 20 | TBD | TBD | TBD | TBD | TBD |

## Verification Links

- Contributors: `https://github.com/sinmb79/ai-language-partner/graphs/contributors`
- Merged PRs: `https://github.com/sinmb79/ai-language-partner/pulls?q=is%3Apr+is%3Amerged`
- Actions: `https://github.com/sinmb79/ai-language-partner/actions`
- Dependency graph: `https://github.com/sinmb79/ai-language-partner/network/dependencies`

## Local Evidence Commands

Run these before applying:

```bash
git shortlog -sn --since=2025-07-08 --all
find . -type f | grep -Ei 'local_engines|artifacts|handoff|reference_archive|\\.sqlite|\\.zip|\\.wav|\\.npy' && exit 1 || true
git grep -nE 'sk-[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}' -- .
python scripts/export_claude_for_oss_evidence.py sinmb79/ai-language-partner --since=2025-07-08
python scripts/verify_claude_for_oss_readiness.py sinmb79/ai-language-partner
```

See `docs/community/PUBLISHING_AND_APPLICATION_CHECKLIST.md` for the full
publish, issue-seeding, and application sequence.
