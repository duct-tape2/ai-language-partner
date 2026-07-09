# First PR Walkthrough

Thank you for considering a contribution. This repository is intentionally set
up so small documentation, content-review, accessibility, test, and API-example
changes can be useful without private context.

## Pick an Issue

Start here:

`https://duct-tape2.github.io/ai-language-partner/demo/`

`https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html`

`https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22`

If you want to avoid local setup entirely, use the no-install board:

`https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html`

To avoid duplicate work, comment `/claim` on the issue before you start. The
repo will reply with the short PR checklist for that issue.

Good first issues should include:

- A clear goal
- Suggested files
- Acceptance criteria
- No requirement for generated audio, local engines, private datasets, or
  maintainer-only credentials

## Make the Change

### Browser-Only Docs Or Language Review

For docs, Korean/Japanese wording, and dialogue text review, you can use the
GitHub web editor:

1. Open an issue from the no-install board.
2. Click the direct edit link for the suggested file.
3. Edit one focused piece of text.
4. Choose "Create a new branch for this commit and start a pull request".

No local STT/TTS engine, generated audio, private data, or API key is needed for
these PRs.

### Local Development

```bash
git clone https://github.com/duct-tape2/ai-language-partner.git
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
