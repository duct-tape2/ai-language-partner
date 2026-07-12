# Release Policy

AI Language Partner currently publishes source from `main` and may publish
clearly labeled preview artifacts for contributor testing. It does not yet have
a stable end-user release.

## Version Identifiers

- Stable user-facing releases will use Semantic Versioning tags in the form
  `vMAJOR.MINOR.PATCH`.
- Contributor previews may use descriptive, date-based tags such as
  `demo-web-YYYY-MM-DD`. They must be marked as prereleases and must not be
  described as stable or app-store-ready builds.
- Every public artifact must identify the exact source commit used to build it.

## Release Requirements

Every public release or preview must include:

1. A Git tag that uniquely identifies the source.
2. Human-written GitHub release notes describing user-visible changes and
   upgrade or compatibility impact.
3. The verification commands and results relevant to the artifact.
4. A clear support statement, including whether the artifact is a preview.
5. Checksums for downloadable generated artifacts.
6. A list of fixed publicly known runtime vulnerabilities that already have a
   CVE or equivalent identifier, or an explicit statement that the release
   fixes none.

Before publishing, the maintainer must review open code-scanning and dependency
alerts. A release must not knowingly ship an unaddressed critical vulnerability.
Any accepted medium or high risk must be documented with its impact and
mitigation instead of being silently omitted.

## Current Preview

[`demo-web-2026-07-09`](https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09)
is an Expo web snapshot for contributors and directory reviewers. It is a
prerelease, identifies its source commit, records verification results, and
publishes a SHA-256 checksum. Its release notes state that it does not claim to
fix a CVE-assigned runtime vulnerability. It is not a supported production
release.

## Release Notes And Security

Release notes are maintained on the corresponding GitHub Release page. Security
reporting, response targets, and disclosure guidance are documented in
[`SECURITY.md`](SECURITY.md).
