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
EXPO_PUBLIC_USE_MOCK_API=true EXPO_PUBLIC_API_BASE_URL="" npx expo export --platform web

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

## Hosted Web Demo

Current hosted mock-mode demo:

- URL: `https://duct-tape2.github.io/ai-language-partner/demo/`
- Build command: `python3 scripts/build_pages_demo.py`
- Source path: `docs/demo/`
- Mode: fixture-backed mock providers; no private API keys, generated audio, or
  local speech engines required

The Pages demo is a contributor and directory-review aid. It is not an
app-store release and should not be counted as Claude for OSS contributor
evidence.

## Published Demo Artifact

Current prerelease:

- Release: `https://github.com/duct-tape2/ai-language-partner/releases/tag/demo-web-2026-07-09`
- Download: `https://github.com/duct-tape2/ai-language-partner/releases/download/demo-web-2026-07-09/ai-language-partner-web-demo-2026-07-09.zip`
- SHA-256:
  `10adfbeed89e3d3af5904533e8bc3b8f19c3710dc0c74ee102d76522c32e6c8d`
- Source commit: `5d1cf3be1e8fdba86e89a7b2ca949c9edd7ed9e1`

This satisfies the downloadable release-artifact step. A hosted web demo or
app-store/TestFlight-style build would be stronger for mainstream directory
listings.

## Local Verification Log

Verified on `2026-07-09`:

| Gate | Result | Evidence |
|---|---|---|
| Mobile verify | PASS | `cd apps/mobile && npm run verify` |
| Backend pytest | PASS | `cd apps/api && .venv/bin/python -m pytest` reported 61 passed |
| Expo web export | PASS | `EXPO_PUBLIC_USE_MOCK_API=true EXPO_PUBLIC_API_BASE_URL="" npx expo export --platform web` exported `apps/mobile/dist` |
| One-origin demo server | PASS | `cd apps/api && .venv/bin/python scripts/serve_demo.py 8123` served `/health` and `/` with HTTP 200 |
| Pages hosted demo build | PASS | `python3 scripts/build_pages_demo.py` staged `docs/demo/` with project-page-safe paths |

The generated `apps/mobile/dist` directory is ignored and should remain a
local/release artifact. The checked-in `docs/demo/` tree is the GitHub Pages
hosted demo snapshot and must be regenerated with `scripts/build_pages_demo.py`.

## Release Ladder

| Stage | Target | Evidence to publish |
|---|---|---|
| Local source demo | Contributors can run web/mock mode locally | README commands, passing CI, no private assets |
| Hosted web demo | Readers can click and inspect the app in a browser | `https://duct-tape2.github.io/ai-language-partner/demo/`, mock-mode disclosure |
| Downloadable release | Testers can install or run a packaged build | GitHub Release notes, platform artifact, checksums if applicable |
| App-store-ready build | Directory maintainers can send normal learners to it | App Store/TestFlight/Play/Internal Testing link or equivalent |

## External Listing Follow-Up

Awesome Japanese asked us to come back when the app is more mature and easier
for readers to use. The hosted web demo now satisfies the click-to-inspect step,
but prefer waiting for a stronger app-store-ready build before reopening that
route.

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
