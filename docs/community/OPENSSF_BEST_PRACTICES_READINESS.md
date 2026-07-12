---
layout: page
title: OpenSSF Best Practices Readiness
---

# OpenSSF Best Practices Readiness

Status: **pre-assessment only**. The project has not been registered or awarded
an OpenSSF Best Practices badge. Do not display a badge until the official
project page reports a passing status.

Registration remains gated by the authenticated and project-history checks
listed below. A configured scanner is evidence of a process, not evidence that
its findings are resolved.

Official criteria:
<https://www.bestpractices.dev/en/criteria/0>

OpenSSF Scorecard automation and the Best Practices badge are separate
programs. A successful Scorecard workflow is useful evidence, but it does not
grant the Best Practices badge.

## Evidence Already Public

| Area | Current evidence | Assessment |
|---|---|---|
| Project purpose and interaction | [`README.md`](../../README.md), [hosted Pages](https://duct-tape2.github.io/ai-language-partner/), issues, and Discussions | Verifiable |
| Contribution process | [`CONTRIBUTING.md`](../../CONTRIBUTING.md), PR template, issue templates, and contributor guides | Verifiable |
| FLOSS license | [`LICENSE`](../../LICENSE), MIT | Verifiable |
| User and API documentation | README run instructions, [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md), and [`contracts/openapi_v0.yaml`](../../contracts/openapi_v0.yaml) | Verifiable |
| Public change control | Git repository, PR review, protected `main`, and public history | Current authenticated governance check passes; recheck at registration |
| Release identification and notes | [`RELEASING.md`](../../RELEASING.md) and the [`demo-web-2026-07-09` prerelease](https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09) | Verifiable preview policy; no stable release yet |
| Bug and vulnerability reporting | GitHub issues, enabled private vulnerability reporting, and [`SECURITY.md`](../../SECURITY.md) with a 14-day initial-response target | Verifiable process; response history still needs review |
| Automated tests | Backend pytest, mobile strict TypeScript checks, regression scripts, and public CI | Verifiable |
| New-functionality test policy | Task-specific definition of done in [`CONTRIBUTING.md`](../../CONTRIBUTING.md) | Policy is public; recent-change evidence still needs review |
| Warning and lint enforcement | Strict TypeScript checking plus pinned Ruff checks for Python application, test, and maintenance code | Enforced on pull requests and `main`; scoped `E402` exceptions cover scripts that must set their import path first |
| Static analysis | CodeQL for Python and JavaScript/TypeScript, dependency review, Ruff, and OpenSSF Scorecard workflows | Automation is verifiable; authenticated findings must be rechecked at registration |
| Dependency vulnerability audit | Scheduled npm and `pip-audit` checks in the [dependency-audit workflow](https://github.com/duct-tape2/ai-language-partner/blob/main/.github/workflows/dependency-audit.yml) | Locked dependency audits pass; recheck GitHub alerts at registration |
| Container execution | API tests plus a required Docker runtime smoke in [`api-docker-smoke.yml`](https://github.com/duct-tape2/ai-language-partner/blob/main/.github/workflows/api-docker-smoke.yml) | CI asserts the container runtime and application dependency import evidence |
| Credential and generated-file controls | Public-tree scanner, production-secret guard, `.gitignore`, and security policy | Verifiable controls, not a guarantee |

## Items That Still Need Confirmation

These items must not be marked as met based only on repository files:

- Re-run authenticated CodeQL, dependency, malware, secret-scanning, and
  private-advisory checks immediately before registration. Do not register
  while a confirmed critical or high-severity issue remains open.
- Recheck Dependabot alerts and confirm that no medium-or-higher vulnerability
  has remained unpatched for more than 60 days.
- Review the private-advisory inbox and record whether any vulnerability report
  in the last six months received an initial response within 14 days. Use N/A
  only when there were no reports and the official form permits it.
- Confirm that at least one primary developer meets the official secure-design
  and common-error knowledge criteria.
- Audit the authentication and device-key paths to confirm that the project
  relies on reviewed platform/library cryptography and does not implement a
  custom cryptographic primitive.
- Select the most recent major functional changes and link the automated tests
  added with them; a written policy alone does not satisfy the separate
  `tests_are_added` criterion.
- Re-run the authenticated governance check immediately before registration;
  repository files alone do not prove that branch protection is still enabled.
- Reassess bug and enhancement response-rate criteria after the project has a
  meaningful 2-to-12-month public history.

## Registration Gate

1. Resolve or explicitly document every item above.
2. Sign in at <https://www.bestpractices.dev/en/projects/new> with the maintainer
   account and register the public repository.
3. Answer each criterion with a repository or release URL where possible.
4. Leave uncertain criteria unmet or not applicable with an honest
   justification; do not guess.
5. Add an official badge link only after the public OpenSSF project page reports
   `passing`.

This readiness work improves project trust. It does not count as an external
contribution and does not change Claude for OSS eligibility by itself.
