# Security Policy

## Supported Versions

The `main` branch is the only supported development line until the project
publishes tagged releases.

## Reporting a Vulnerability

Please do not open public issues for exploitable security problems. Email the
maintainer listed on the GitHub profile or open a minimal private advisory if
GitHub advisories are enabled for the repository.

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

