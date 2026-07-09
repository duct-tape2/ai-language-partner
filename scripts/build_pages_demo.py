#!/usr/bin/env python3
"""Build the Expo web demo into docs/demo for GitHub Pages."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOBILE_DIR = ROOT / "apps" / "mobile"
DIST_DIR = MOBILE_DIR / "dist"
DEMO_DIR = ROOT / "docs" / "demo"
EXPO_STATIC_DIR = "expo-static"


def run_export() -> None:
    env = os.environ.copy()
    env["EXPO_PUBLIC_USE_MOCK_API"] = "true"
    env["EXPO_PUBLIC_API_BASE_URL"] = ""
    subprocess.run(
        [
            "npx",
            "expo",
            "export",
            "--platform",
            "web",
            "--output-dir",
            str(DIST_DIR),
        ],
        cwd=MOBILE_DIR,
        env=env,
        check=True,
    )


def patch_index() -> None:
    index = DEMO_DIR / "index.html"
    text = index.read_text(encoding="utf-8")
    text = text.replace('href="/favicon.ico"', 'href="favicon.ico"')
    text = text.replace('src="/_expo/', f'src="{EXPO_STATIC_DIR}/')
    text = text.replace('src="/expo-static/', f'src="{EXPO_STATIC_DIR}/')
    if '"/_expo/' in text or '"/favicon.ico"' in text:
        raise RuntimeError("index.html still contains root-relative demo paths")
    index.write_text(text, encoding="utf-8")


def patch_javascript_assets() -> None:
    js_dir = DEMO_DIR / EXPO_STATIC_DIR / "static" / "js" / "web"
    if not js_dir.is_dir():
        raise RuntimeError(f"missing Expo JS directory: {js_dir}")
    for path in sorted(js_dir.glob("*.js")):
        text = path.read_text(encoding="utf-8")
        text = text.replace('uri:"/assets/', 'uri:"assets/')
        if 'uri:"/assets/' in text:
            raise RuntimeError(f"{path} still contains root-relative asset URIs")
        path.write_text(text, encoding="utf-8")


def stage_demo() -> None:
    if not (DIST_DIR / "index.html").is_file():
        raise RuntimeError(f"missing Expo export at {DIST_DIR}; run without --skip-export first")
    if DEMO_DIR.exists():
        shutil.rmtree(DEMO_DIR)
    shutil.copytree(DIST_DIR, DEMO_DIR)

    source_expo = DEMO_DIR / "_expo"
    target_expo = DEMO_DIR / EXPO_STATIC_DIR
    if source_expo.exists():
        source_expo.rename(target_expo)
    if (DEMO_DIR / "_expo").exists():
        raise RuntimeError("docs/demo/_expo must not exist; Jekyll ignores underscored directories")

    patch_index()
    patch_javascript_assets()

    metadata = {
        "generatedBy": "scripts/build_pages_demo.py",
        "mode": "mock",
        "apiBase": "",
        "notes": [
            "Hosted GitHub Pages demo for contributors and directory reviewers.",
            "Mock providers are intentional; no private API keys or local engines are required.",
        ],
    }
    (DEMO_DIR / "demo-build.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Stage the existing apps/mobile/dist export instead of running Expo.",
    )
    args = parser.parse_args(argv[1:])

    if not args.skip_export:
        run_export()
    stage_demo()
    print(f"GitHub Pages demo staged at {DEMO_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
