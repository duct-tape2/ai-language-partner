---
layout: page
title: Open Science Labs Internship Idea Draft
---

# AI Language Partner

This is a pre-submission draft using the Open Science Labs OSS Internship
Project Ideas template. It is not an internship announcement and has not been
submitted. Project affiliation and mentor availability must be confirmed first.

AI Language Partner is a local-first Japanese speaking-practice application
for Korean learners. Its public Expo/React Native client, FastAPI backend,
dialogue fixtures, and OpenAPI contract are designed so learning content and
runtime behavior can be inspected without a paid runtime LLM dependency.

- **Project License:** https://github.com/duct-tape2/ai-language-partner/blob/main/LICENSE
- **Code of Conduct:** https://github.com/duct-tape2/ai-language-partner/blob/main/CODE_OF_CONDUCT.md
- **Documentation:** https://duct-tape2.github.io/ai-language-partner/
- **Compensation:** Unpaid unless a future mentor or sponsor explicitly
  confirms funding before applications open.

## Project Idea 1: Accessible And Reproducible Local-First Language Practice

### Abstract

Improve the project's learner and contributor experience across accessibility,
local speech-provider reproducibility, and bilingual content quality. The work
will turn the current mock-mode demo and source dialogue bank into a more
rigorously tested reference implementation for low-cost Japanese practice. It
will include product-facing improvements, automated checks, public
documentation, and a final demonstration rather than a collection of unrelated
small pull requests.

### Current State

The repository currently includes:

- an Expo/React Native mobile and web client;
- a FastAPI backend and versioned OpenAPI contract;
- fixture-backed mock mode and a hosted web demo;
- local whisper.cpp and VOICEVOX-compatible provider adapters;
- Korean/Japanese source dialogue fixtures without generated binary assets;
- accessibility, API, public-tree, and contributor workflow issues;
- CI for public-tree hygiene, mobile verification, backend smoke tests, and
  CodeQL.

Known improvement areas include incomplete accessibility regression coverage,
setup friction for local speech providers, mock/live parity documentation, and
the need for a repeatable human-review protocol for beginner dialogue content.

### Tasks

1. Establish a baseline and acceptance matrix.
   - Audit learner workflows in hosted mock mode and a local backend run.
   - Record accessibility, provider setup, and content-review gaps as scoped
     issues before implementation.
   - Define measurable checks for each selected workflow.
2. Improve mobile and web accessibility.
   - Fix labels, roles, touch targets, focus behavior, and narrow-screen layout
     in selected high-use learning screens.
   - Add focused regression checks for missing accessible names and unstable
     layout assumptions.
   - Document manual verification on at least one mobile-sized and one desktop
     viewport.
3. Make local STT/TTS setup reproducible.
   - Validate macOS/Linux setup for whisper.cpp and one
     VOICEVOX-compatible provider.
   - Improve provider-status examples, fallback labels, and troubleshooting
     without bundling models, engines, secrets, or generated audio.
   - Add contract or fixture tests that run without local engine binaries.
4. Strengthen bilingual dialogue review.
   - Define a small review rubric for Japanese naturalness, Korean learner
     clarity, cultural safety, and stable dialogue identifiers.
   - Apply the rubric to a bounded sample pack and record review provenance.
   - Add validation that catches structural errors without claiming automated
     language correctness.
5. Integrate, document, and demonstrate.
   - Keep each change issue-linked and reviewable while maintaining one project
     narrative and milestone plan.
   - Update contributor and architecture documentation to match shipped
     behavior.
   - Publish a final report covering outcomes, test evidence, limitations, and
     follow-up work, plus a demo of the improved workflows.

### Expected Outcomes

- A documented accessibility baseline and implemented improvements in selected
  learner workflows.
- Regression coverage for the accessibility behaviors in scope.
- Reproducible local speech-provider setup and clearer fallback reporting.
- Engine-independent API fixtures or tests that run in public CI.
- A reusable bilingual dialogue-review rubric applied to a bounded sample.
- Updated public documentation, green CI, and an inspectable final demo/report.
- No private data, generated binary packs, vendored engines, or unsupported
  claims introduced into the public repository.

### Details

- Prerequisites:
  - Working knowledge of TypeScript or Python and Git/GitHub pull requests.
  - Interest in accessibility, language-learning software, test automation, or
    local-first systems.
  - Ability to communicate progress and review feedback in English.
  - Korean or Japanese proficiency is useful for content-review work but is
    not required for all engineering tasks.
- Expected Time: 350 hours over approximately three months.
- Potential Mentor(s): GitHub `@duct-tape2`; mentor availability and the OSL
  expectation of at least five hours per week must be confirmed before this
  idea is submitted or advertised.

### References

- Repository: https://github.com/duct-tape2/ai-language-partner
- Hosted demo: https://duct-tape2.github.io/ai-language-partner/demo/
- Architecture: https://duct-tape2.github.io/ai-language-partner/ARCHITECTURE.html
- Contributor landing: https://duct-tape2.github.io/ai-language-partner/community/CONTRIBUTOR_LANDING.html
- First issue matcher: https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html
- OSL affiliation proposal: https://duct-tape2.github.io/ai-language-partner/community/OPEN_SCIENCE_LABS_AFFILIATION_PROPOSAL.html
- OSL project-idea template: https://opensciencelabs.org/opportunities/internships/templates/projects-ideas/

## Submission Gate

- [ ] Open Science Labs confirms project affiliation.
- [ ] The maintainer explicitly confirms mentor availability and at least five
  hours per week for reviews and guidance.
- [ ] Compensation language is confirmed before candidates apply.
- [ ] Tasks are reconciled with current open issues and current source state.
- [ ] The idea is sent to OSL only through its supported process.
