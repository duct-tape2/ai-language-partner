# Installable Demo Release Plan

This plan exists because external directory maintainers need to understand how
readers can try the app. The repo already has contributor-friendly source and
first-PR lanes; the next discovery bottleneck is a clear install or demo path.

## Current Local Demo Path

The project can run without private assets, API keys, local speech engines, or
generated audio.

Backend mock mode:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Mobile web mock mode:

```bash
cd apps/mobile
npm install
npm run web
```

One-origin exported web demo:

```bash
cd apps/mobile
EXPO_PUBLIC_USE_MOCK_API=false EXPO_PUBLIC_API_BASE_URL="" npx expo export --platform web

cd ../api
source .venv/bin/activate
python scripts/serve_demo.py 8000
```

The `serve_demo.py` path mounts the exported Expo web build at `/` while
FastAPI keeps `/health` and `/v1/*`.

## Public Demo Gate

A public demo is ready when all of these are true:

- `npm run verify` passes in `apps/mobile`.
- `python -m pytest` passes in `apps/api`.
- `npx expo export --platform web` succeeds from `apps/mobile`.
- `python scripts/serve_demo.py 8000` serves the exported app and `/health`
  from one origin.
- The demo visibly labels mock providers, fixture-backed content, and any
  missing local STT/TTS engine behavior.
- The README links to either a hosted demo URL or a release artifact with clear
  "what works in this build" notes.

## Local Verification Log

Verified on `2026-07-09`:

| Gate | Result | Evidence |
|---|---|---|
| Mobile verify | PASS | `cd apps/mobile && npm run verify` |
| Backend pytest | PASS | `cd apps/api && .venv/bin/python -m pytest` reported 61 passed |
| Expo web export | PASS | `EXPO_PUBLIC_USE_MOCK_API=false EXPO_PUBLIC_API_BASE_URL="" npx expo export --platform web` exported `apps/mobile/dist` |
| One-origin demo server | PASS | `cd apps/api && .venv/bin/python scripts/serve_demo.py 8123` served `/health` and `/` with HTTP 200 |

The generated `apps/mobile/dist` directory is ignored and should remain a
local/release artifact unless a release workflow explicitly packages it.

## Release Ladder

| Stage | Target | Evidence to publish |
|---|---|---|
| Local source demo | Contributors can run web/mock mode locally | README commands, passing CI, no private assets |
| Hosted web demo | Readers can click and inspect the app in a browser | Demo URL, `/health`, mock-mode disclosure |
| Downloadable release | Testers can install or run a packaged build | GitHub Release notes, platform artifact, checksums if applicable |
| App-store-ready build | Directory maintainers can send normal learners to it | App Store/TestFlight/Play/Internal Testing link or equivalent |

## External Listing Follow-Up

Awesome Japanese asked us to come back when the app is more mature and easier
for readers to use. Do not reopen that route until at least the hosted web demo
stage is complete, and prefer waiting for an app-store-ready build.

Up For Grabs is already live, so contributor discovery can continue through
starter issues while the user-facing demo path matures.

## Good Contributor Tasks

- Verify the one-origin web demo command sequence on macOS.
- Add screenshots or a short demo video only as release artifacts, not tracked
  source files.
- Improve README wording so non-maintainers can tell what works in mock mode.
- Add a CI check for `expo export --platform web` if build time stays
  reasonable.
- Draft release notes that separate source-only repo contents from generated
  voice/audio assets.
