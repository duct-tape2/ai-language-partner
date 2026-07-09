#!/usr/bin/env python3
"""Create or update GitHub labels from docs/community/LABELS.md.

Usage:
  GITHUB_TOKEN=... python scripts/create_github_labels.py duct-tape2/ai-language-partner

The script uses only the Python standard library. It intentionally keeps label
metadata in docs/community/LABELS.md so public contributors can see the same
taxonomy maintainers apply in GitHub.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "docs" / "community" / "LABELS.md"

COLORS = {
    "good first issue": "7057ff",
    "help wanted": "008672",
    "up-for-grabs": "0e8a16",
    "first-timers-only": "7057ff",
    "docs": "0075ca",
    "content": "fbca04",
    "language-review": "d93f0b",
    "accessibility": "5319e7",
    "backend": "1d76db",
    "mobile": "0e8a16",
    "tests": "c2e0c6",
    "release": "bfd4f2",
    "security": "b60205",
    "community": "c5def5",
    "needs-triage": "ededed",
    "claimed": "d4c5f9",
}


def parse_labels(text: str) -> list[dict[str, str]]:
    labels: list[dict[str, str]] = []
    row = re.compile(r"^\|\s+`(?P<name>[^`]+)`\s+\|\s+(?P<description>[^|]+?)\s+\|$")
    for line in text.splitlines():
        match = row.match(line)
        if not match:
            continue
        name = match.group("name").strip()
        description = match.group("description").strip()
        labels.append(
            {
                "name": name,
                "description": description,
                "color": COLORS.get(name, "ededed"),
            }
        )
    return labels


def github_request(repo: str, token: str, method: str, path: str, payload: dict[str, str]) -> dict[str, object]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ai-language-partner-label-bootstrap",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def upsert_label(repo: str, token: str, label: dict[str, str]) -> tuple[str, str]:
    try:
        created = github_request(repo, token, "POST", "/labels", label)
        return "created", str(created.get("name", label["name"]))
    except urllib.error.HTTPError as exc:
        if exc.code != 422:
            raise

    encoded_name = urllib.parse.quote(label["name"], safe="")
    updated = github_request(repo, token, "PATCH", f"/labels/{encoded_name}", label)
    return "updated", str(updated.get("name", label["name"]))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: create_github_labels.py owner/repo", file=sys.stderr)
        return 2
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2

    labels = parse_labels(LABELS.read_text(encoding="utf-8"))
    if len(labels) < 10:
        print(f"expected at least 10 labels, parsed {len(labels)}", file=sys.stderr)
        return 1

    for label in labels:
        try:
            action, name = upsert_label(argv[1], token, label)
        except urllib.error.HTTPError as exc:
            print(exc.read().decode("utf-8"), file=sys.stderr)
            return 1
        print(f"{action}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
