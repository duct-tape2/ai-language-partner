"""Serve the exported Expo web build and the API from one origin.

Usage:
    AI_LANGUAGE_PARTNER_TTS_PROVIDER=edge .venv/bin/python scripts/serve_demo.py [port]

The mobile web build must exist first:
    cd ../mobile && EXPO_PUBLIC_USE_MOCK_API=false EXPO_PUBLIC_API_BASE_URL="" npx expo export --platform web
"""
from __future__ import annotations

import sys
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

WEB_DIST = Path(__file__).resolve().parents[3] / "apps" / "mobile" / "dist"

if not WEB_DIST.exists():
    raise SystemExit(f"web build not found: {WEB_DIST} - run expo export first")

# API routes are registered before this catch-all mount, so /v1/* and /health win.
app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="webdemo")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
