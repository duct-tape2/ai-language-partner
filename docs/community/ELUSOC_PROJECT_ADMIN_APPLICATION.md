---
layout: page
title: ELUSOC Project Admin Application Packet
---

# ELUSOC 2026 Project Admin Application Packet

Use this packet for the official EduLinkUp Summer of Code 2026 project-admin
registration. It contains only public, verifiable project information. The
applicant must enter their own legal/display name, account password, LinkedIn
profile, and any other personal fields directly.

## Registration Status

- Official project-admin window: April 5 through July 15, 2026.
- Unstop registration: required before EduLinkUp registration.
- EduLinkUp account/profile: requires the applicant's own name and login.
- The live form also requires the applicant to choose `Student` or
  `Professional` and provide contact/profile details before submission.
- GitHub repository topics: `edulinkup` and `elusoc` are already present.
- The signed-in EduLinkUp session reaches the project-admin form and the public
  repository fields are prefilled, but the applicant profile and required
  personal fields are not complete.
- Unstop registration is not complete; its candidate profile still requires
  applicant-selected identity/contact fields, user type, and terms review.
- Repository registration: not complete until the official platform confirms
  the project-admin application.
- Program labels: do not apply `elusoc`, `newbie`, `adventurer`, or `veteran`
  until the project is registered or accepted by the program.

Official entry points:

- Unstop registration: https://unstop.com/competitions/1664587/register
- ELUSOC: https://www.edulinkup.dev/elusoc
- EduLinkUp login: https://www.edulinkup.dev/login
- Guidelines: https://www.edulinkup.dev/elusoc/guidelines

## Personal Fields The Applicant Must Complete

Do not infer or generate these values:

| Field | Value |
|---|---|
| User type | Applicant selects `Student` or `Professional` truthfully |
| Full name | Applicant enters directly |
| College / university | Applicant answers truthfully; ask the organizer if it is not applicable |
| Branch / major | Applicant enters directly if applicable |
| Graduation year | Applicant selects directly if applicable |
| Email | Applicant confirms directly |
| Password / login secret | Applicant enters directly |
| LinkedIn URL | Applicant supplies directly; the live form marks it required |
| WhatsApp number and country code | Applicant supplies directly |
| Telegram username | Applicant supplies directly |
| Unstop registration confirmation | Applicant completes and confirms directly |
| Availability and time commitment | Applicant confirms directly |

## Project Fields

| Field | Verified value |
|---|---|
| Project name | AI Language Partner |
| Repository | https://github.com/duct-tape2/ai-language-partner |
| Hosted demo | https://duct-tape2.github.io/ai-language-partner/demo/ |
| Contributor page | https://duct-tape2.github.io/ai-language-partner/ |
| License | MIT |
| Primary language | TypeScript |
| Other technologies | React Native, Expo, FastAPI, Python, OpenAPI, GitHub Actions |
| Domain | Education, language learning, accessibility, local-first software |
| Target audience | Korean-speaking learners of Japanese |
| Current contributor count | 2 verified unique external merged-PR contributors as of 2026-07-11 |

## Paste-Ready Live Form Values

The live project-admin form was rechecked on 2026-07-11. These values cover
only public project fields; they do not complete or submit the application.

**GitHub username**

```text
duct-tape2
```

**Repository URL**

```text
https://github.com/duct-tape2/ai-language-partner
```

**Description (under the form's 200-word limit)**

```text
AI Language Partner is an MIT-licensed, local-first Japanese speaking-practice app for Korean learners. It combines an Expo/React Native client, FastAPI backend, curated dialogue-bank content, local speech-to-text, and local text-to-speech. The Daily Talk path does not require a runtime LLM or paid hosted model API, keeping practice predictable, reviewable, and suitable for low-cost deployments. Contributors can work on Korean and Japanese content review, mobile accessibility, API examples, local provider documentation, and focused regression tests. The repository includes a hosted fixture-backed demo, scoped issues, contribution governance, and public CI.
```

**Tech-stack tags**

```text
TypeScript, React Native, Expo, Python, FastAPI, OpenAPI, GitHub Actions
```

**Deployment link**

```text
https://duct-tape2.github.io/ai-language-partner/demo/
```

**Project admin / mentorship plan**

```text
I will assign one clearly scoped issue to one contributor on a first-come, first-served basis, keep acceptance criteria and verification commands in each issue, and review first-time contributor PRs within 24 hours whenever possible. Every merged contribution must link its issue, pass the relevant checks, and receive a human review comment. I will reject copied, spammy, secret-bearing, binary-asset, or metric-only submissions. Difficulty labels will reflect actual complexity, and program scoring will remain separate from the project's Claude for OSS evidence record.
```

Do not select the Unstop or Code of Conduct confirmations until the applicant
has personally completed the required registration and reviewed the linked
terms.

## Short Project Description

AI Language Partner is an MIT-licensed, local-first Japanese speaking-practice
app for Korean learners. It combines an Expo/React Native client with a FastAPI
backend, curated dialogue-bank content, local STT, and local TTS. The Daily
Talk path does not require a runtime LLM or paid hosted model API, which keeps
the learner workflow predictable, reviewable, and suitable for low-cost
deployments.

## Problem And Impact

Many speaking-practice tools depend on recurring hosted AI costs and generated
answers that are difficult for beginner learners to verify. This project keeps
the runtime conversation path deterministic: learner speech is transcribed,
matched to reviewed dialogue choices, and answered with a pre-authored line.
The public repository also exposes Korean/Japanese language-review work,
accessibility improvements, API examples, and tests as meaningful contribution
paths for people who are not ready to modify core application code.

## Why It Is Ready For Contributors

- Public README, MIT license, contribution guide, code of conduct, security
  policy, issue templates, and pull-request template.
- Hosted fixture-backed web demo that needs no private key or local engine.
- More than 30 open `help wanted` issues and more than 20
  `first-timers-only` issues with acceptance criteria.
- Browser-only tasks for Korean/Japanese review and documentation.
- Codespaces and local setup paths for code and test contributions.
- Automated public-tree, mobile, backend smoke, and CodeQL checks.
- Maintainer review and external-contributor counting policy that rejects
  bots, duplicate identities, trivial metric-only work, and unreviewed PRs.

## Contribution Lanes

1. Korean learner documentation and troubleshooting notes.
2. Japanese naturalness and beginner-safety review.
3. Dialogue-bank content and cultural-safety review.
4. React Native accessibility and small-screen behavior.
5. FastAPI/OpenAPI examples and provider-status documentation.
6. Focused regression tests and public-tree tooling.

Entry links:

- Issue matcher: https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html
- Browser-only tasks: https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html
- Five-minute first PR: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- GitHub contribution page: https://github.com/duct-tape2/ai-language-partner/contribute

## Project Admin Operating Plan

- Assign one clearly scoped issue to one contributor on a first-come,
  first-served basis.
- Require the issue link in every PR and review the actual user value before
  merging.
- Respond to first-time contributor PRs within 24 hours whenever possible.
- Run relevant checks and leave an auditable human review comment.
- Reject copied, generated-dump, secret-bearing, binary-asset, or metric-only
  submissions.
- Keep program scoring separate from the Claude for OSS evidence record.

## ELUSOC Label Plan After Registration

Only after official registration or acceptance:

| Program label | Intended use |
|---|---|
| `elusoc` | Issues and PRs explicitly participating in ELUSOC |
| `newbie` | Focused docs/content or minor UI work with low setup cost |
| `adventurer` | Bug fixes, components, API improvements, or focused tests |
| `veteran` | Architecture, performance, or complex integration work |

Difficulty must reflect actual complexity. Do not lower difficulty to inflate
participation or split one useful change into multiple PRs.

## Application Answer: Why Should This Project Be Selected?

AI Language Partner offers contributors a working education product with
several genuine entry levels: browser-only bilingual review, accessibility,
mobile code, backend contracts, and tests. Its local-first architecture makes
cost, privacy, and quality tradeoffs inspectable in source, while the hosted
demo lets contributors understand the learner experience before installing a
toolchain. The maintainer has prepared explicit issue scopes, CI, review rules,
and anti-spam safeguards and is applying to mentor useful contributions rather
than collect superficial pull requests.

## Final Submission Checklist

- [ ] Applicant completed Unstop registration personally.
- [ ] Applicant completed EduLinkUp profile and GitHub OAuth personally.
- [ ] Applicant supplied the mandatory full name, institution, LinkedIn,
  WhatsApp, and Telegram fields personally.
- [ ] Project-admin form uses the repository and demo URLs above.
- [ ] Personal fields were entered or confirmed by the applicant.
- [ ] Repository topics still include `edulinkup` and `elusoc`.
- [ ] Official platform shows the project as submitted, under review, or
  accepted.
- [ ] Program labels are created only when ELUSOC confirms the project route.
- [ ] Acceptance email or platform URL is recorded without exposing private
  account data.
