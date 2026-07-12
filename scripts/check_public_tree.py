#!/usr/bin/env python3
"""Fail if private/generated files are tracked in the public repository."""

from __future__ import annotations

import re
import subprocess
import sys


FORBIDDEN_PATH = re.compile(
    r"(^|/)(local_engines|artifacts|handoff|reference_archive)(/|$)"
    r"|(\.sqlite|\.sqlite-shm|\.sqlite-wal|\.db|\.zip|\.wav|\.mp3|\.m4a|\.aac|\.flac|\.ogg|\.npy|\.bin|\.pyc|\.log)$",
    re.IGNORECASE,
)

SECRET_LIKE = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})"
)
URL_USERINFO = re.compile(r"(?P<scheme>\b[a-z][a-z0-9+.-]*://)(?P<userinfo>[^/?#@\s]+)@", re.IGNORECASE)


def _safe_path_diagnostic(path: str) -> str:
    """Keep the path useful for CI while never printing URL credentials or token-shaped path segments."""
    redacted = URL_USERINFO.sub(r"\g<scheme><redacted>@", path)
    return SECRET_LIKE.sub("<redacted-token>", redacted)


def tracked_files() -> list[str]:
    proc = subprocess.run(["git", "ls-files"], check=True, capture_output=True, text=True)
    return [line for line in proc.stdout.splitlines() if line]


def main() -> int:
    paths = tracked_files()
    bad_paths = [path for path in paths if FORBIDDEN_PATH.search(path)]
    if bad_paths:
        print("Forbidden generated/private paths are tracked:", file=sys.stderr)
        for path in bad_paths:
            print(f"  {_safe_path_diagnostic(path)}", file=sys.stderr)
        return 1

    bad_secret_hits: list[str] = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except (UnicodeDecodeError, OSError):
            continue
        if SECRET_LIKE.search(text):
            bad_secret_hits.append(path)
    if bad_secret_hits:
        print("Secret-like tokens found:", file=sys.stderr)
        for path in bad_secret_hits:
            print(f"  {_safe_path_diagnostic(path)}", file=sys.stderr)
        return 1
    print("Public tree check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
