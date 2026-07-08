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


def existing_issue_titles(repo: str, token: str) -> set[str]:
    titles: set[str] = set()
    for page in range(1, 11):
        params = f"state=all&per_page=100&page={page}"
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues?{params}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "ai-language-partner-issue-seeder",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            issues = json.loads(response.read().decode("utf-8"))
        if not isinstance(issues, list):
            break
        for issue in issues:
            if isinstance(issue, dict) and "pull_request" not in issue:
                title = issue.get("title")
                if isinstance(title, str):
                    titles.add(title)
        if len(issues) < 100:
            break
    return titles


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: create_github_issue_seeds.py owner/repo", file=sys.stderr)
        return 2
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2
    issues = parse_seeds(SEEDS.read_text(encoding="utf-8"))
    if len(issues) < 30:
        print(f"expected at least 30 issues, parsed {len(issues)}", file=sys.stderr)
        return 1
    existing_titles = existing_issue_titles(argv[1], token)
    for issue in issues:
        title = str(issue.get("title") or "")
        if title in existing_titles:
            print(f"skipped existing issue: {title}")
            continue
        try:
            created = post_issue(argv[1], token, issue)
        except urllib.error.HTTPError as exc:
            print(exc.read().decode("utf-8"), file=sys.stderr)
            return 1
        print(f"created #{created.get('number')}: {created.get('html_url')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
