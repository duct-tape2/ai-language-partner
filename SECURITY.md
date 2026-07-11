# Security Policy

## Supported Versions

The `main` branch is the only supported development line until the project
publishes tagged releases.

## Reporting a Vulnerability

Please do not open public issues for exploitable security problems. Report a
vulnerability through a [GitHub private security advisory](https://github.com/duct-tape2/ai-language-partner/security/advisories/new), or contact the
maintainer listed on the GitHub profile if private advisories are unavailable.

The maintainer aims to acknowledge validated vulnerability reports within 14
days. A remediation or coordinated-disclosure status update follows within 90
days unless the reporter and maintainer agree on a different timeline for a
complex vulnerability.

Helpful reports include:

- affected route, screen, or script
- reproduction steps
- expected impact
- whether credentials, learner data, or local files are exposed

## Project-Specific Security Rules

- Do not commit API keys, generated learner databases, voice clips, local engine
  binaries, or simulator captures.
- Runtime LLM and external generation APIs must not be added to the Daily Talk
  request path.
- Production builds must not include `EXPO_PUBLIC_DEVICE_ATTESTATION_SECRET`.
- Device trust, auth, and content-publishing changes need tests.
