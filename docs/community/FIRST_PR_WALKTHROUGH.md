# First PR Walkthrough

Thank you for considering a contribution. This repository is intentionally set
up so small documentation, content-review, accessibility, test, and API-example
changes can be useful without private context.

## Pick an Issue

Start here:

`https://github.com/sinmb79/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22`

Good first issues should include:

- A clear goal
- Suggested files
- Acceptance criteria
- No requirement for generated audio, local engines, private datasets, or
  maintainer-only credentials

## Make the Change

```bash
git clone https://github.com/sinmb79/ai-language-partner.git
cd ai-language-partner
git checkout -b docs/my-first-contribution
```

For docs or content review, edit the relevant Markdown, JSON, or CSV source
file only. Do not commit generated `.wav`, `.zip`, `.sqlite`, `.npy`, local
engine folders, screenshots, or private notes.

## Run the Smallest Relevant Check

For repo hygiene:

```bash
python3 scripts/check_public_tree.py
```

For backend work:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest
```

For mobile work:

```bash
cd apps/mobile
npm install
npm run verify
```

## Open the PR

In the PR body:

- Link the issue
- Explain what changed
- Name which check you ran, or say why a check was not needed
- Mention if the PR is language/content review and what you verified

## Review

A maintainer should check:

- The change is focused
- The no-runtime-LLM rule is preserved
- No generated/private assets are committed
- The issue acceptance criteria are met
- The review comment names what was verified

Docs and language-review PRs are welcome when they improve learner experience,
setup clarity, or contributor onboarding.
