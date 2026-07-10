# Open Science Labs Project Affiliation Proposal

## Project

**ai-language-partner** is an MIT-licensed, local-first Japanese speaking
practice application for Korean learners. Its core practice loop uses
pre-authored dialogue-bank content with local speech-to-text and text-to-speech
providers instead of requiring a runtime LLM or paid model API.

- Repository: https://github.com/duct-tape2/ai-language-partner
- Documentation: https://duct-tape2.github.io/ai-language-partner/
- Hosted mock-mode demo:
  https://duct-tape2.github.io/ai-language-partner/demo/
- License:
  https://github.com/duct-tape2/ai-language-partner/blob/main/LICENSE
- Code of Conduct:
  https://github.com/duct-tape2/ai-language-partner/blob/main/CODE_OF_CONDUCT.md
- Security policy:
  https://github.com/duct-tape2/ai-language-partner/blob/main/SECURITY.md
- Maintainer: https://github.com/duct-tape2

## Goals

The project aims to make spoken Japanese practice inspectable, affordable, and
adaptable for Korean-speaking learners. Its near-term goals are to:

1. improve beginner-safe Korean and Japanese learning content;
2. document reproducible local STT/TTS deployment paths;
3. improve mobile accessibility and low-cost device support;
4. expand tested API contracts and source dialogue fixtures; and
5. build a healthy contributor workflow for language reviewers, technical
   writers, testers, and developers.

## Current State

The public repository includes an Expo/React Native mobile application, a
FastAPI service, shared packages, OpenAPI contracts, sample dialogue fixtures,
CI, public governance documents, and a hosted mock-mode demo.

As of 2026-07-10, the contributor surface includes:

- 52 scoped public issues;
- 27 browser-only first-PR tasks that require no local environment;
- Korean, Japanese, accessibility, API, test, and release-documentation lanes;
- a five-minute first-PR guide and a Codespaces path;
- automated issue-claim guidance and pull-request review packets;
- protected `main`, required review, conversation resolution, and green CI;
- public discovery through Up For Grabs, CodeTriage, 24 Pull Requests, Help
  Wanted, and open project-listing submissions.

The project was recently made public and currently has no merged pull requests
from external contributors. This proposal does not present discovery activity
or maintainer-authored work as external community evidence.

## Alignment With OSL

The project aligns with Open Science Labs' open-source and technology mission
through:

- **Open educational infrastructure:** source code, dialogue fixtures,
  contracts, and setup documentation are public under an OSI-approved license.
- **Reproducibility:** the core practice loop can be inspected and run without
  an opaque runtime LLM dependency.
- **Inclusive participation:** useful work is available to non-programmers,
  language reviewers, accessibility reviewers, technical writers, and
  developers.
- **Public collaboration:** issues, decisions, review criteria, and contributor
  evidence are kept in public GitHub artifacts.
- **Responsible metrics:** bots, duplicate identities, maintainer-authored PRs,
  and trivial PR splitting are excluded from contributor counts.

## Collaboration Plan

If affiliated, the project would first ask OSL for community and project-health
review. After confirming mentor availability and OSL fit, the maintainer would
prepare a separate internship project idea using OSL's required template and
minimum-hour guidance.

Potential work packages include:

1. **Accessible local-first practice experience**
   - audit React Native labels, touch targets, and narrow-screen behavior;
   - improve mock-mode parity and accessibility regression checks;
   - document verification for contributors without mobile hardware.
2. **Reproducible local voice-provider integration**
   - improve macOS/Linux setup guidance for local STT/TTS;
   - add provider-status and fallback examples;
   - expand focused tests that do not require bundled model files.
3. **Reviewed beginner dialogue data**
   - review Japanese naturalness and Korean learner notes;
   - add culturally safe beginner examples and review checklists;
   - expand source fixtures while excluding generated audio and private data.
4. **Open contributor operations**
   - measure claim-to-PR and review latency without ranking contributors;
   - improve onboarding based on documented contributor feedback;
   - publish periodic progress and limitations in the repository.

No compensation is currently offered. Any future internship proposal would
state compensation and mentor availability explicitly before candidates apply.

## Requested Affiliation

The maintainer requests:

- review for OSL Project Affiliation;
- guidance on changes needed to meet OSL project-health expectations;
- inclusion in OSL visibility and community channels if accepted; and
- permission to submit a formal OSL internship project idea after mentor
  availability and scope are confirmed.

## Supporting Links

- Contributor landing:
  https://duct-tape2.github.io/ai-language-partner/community/CONTRIBUTOR_LANDING.html
- No-install first-PR board:
  https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html
- First-issue matcher:
  https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html
- Public contributor sprint:
  https://github.com/duct-tape2/ai-language-partner/issues/52
- Counting policy:
  https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md
- CI workflows:
  https://github.com/duct-tape2/ai-language-partner/actions
