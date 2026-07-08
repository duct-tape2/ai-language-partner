#!/usr/bin/env python3
"""Create GitHub issues from docs/community/ISSUE_SEEDS.md.

Usage:
  GITHUB_TOKEN=... python scripts/create_github_issue_seeds.py sinmb79/ai-language-partner

The script uses only the Python standard library. It expects the seed file to
use numbered entries with title lines, a following Labels line, and an
Acceptance paragraph.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "docs" / "community" / "ISSUE_SEEDS.md"


def parse_seeds(text: str) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    pattern = re.compile(
        r"^\d+\.\s+`(?P<title>[^`]+)`\n"
        r"\s+Labels:\s+(?P<labels>.+?)\n(?P<rest>.*?)(?=\n\d+\.\s+`|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        labels = re.findall(r"`([^`]+)`", match.group("labels"))
        body = match.group("rest").strip()
        issues.append({"title": match.group("title"), "labels": labels, "body": body})
    return issues


def post_issue(repo: str, token: str, issue: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps(issue).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ai-language-partner-issue-seeder",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: create_github_issue_seeds.py owner/repo", file=sys.stderr)
        return 2
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 2
    issues = parse_seeds(SEEDS.read_text(encoding="utf-8"))
    if len(issues) < 30:
        print(f"expected at least 30 issues, parsed {len(issues)}", file=sys.stderr)
        return 1
    for issue in issues:
        try:
            created = post_issue(argv[1], token, issue)
        except urllib.error.HTTPError as exc:
            print(exc.read().decode("utf-8"), file=sys.stderr)
            return 1
        print(f"created #{created.get('number')}: {created.get('html_url')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
