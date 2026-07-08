#!/usr/bin/env python3
"""Apply discovery labels to starter issues.

The labels help external contributors find scoped work through GitHub search.
They are not contributor evidence by themselves.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


DISCOVERY_LABELS = {
    "up-for-grabs": {
        "color": "0e8a16",
        "description": "Scoped and available for external contributors",
    },
    "first-timers-only": {
        "color": "7057ff",
        "description": "Lowest-context starter task suitable for a first OSS PR",
    },
}

FIRST_TIMERS_ISSUES = {
    1,
    2,
    5,
    7,
    11,
    15,
    18,
    19,
    25,
    29,
    31,
    34,
    36,
    40,
    42,
    44,
    8,
    12,
    16,
    35,
    45,
    46,
    47,
    50,
}

UP_FOR_GRABS_ISSUES = FIRST_TIMERS_ISSUES | {
    3,
    4,
    6,
    20,
    23,
    24,
    41,
}


def github_json(url: str, token: str | None, method: str = "GET", payload: object | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-discovery-labels",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def ensure_label(repo: str, token: str | None, name: str, color: str, description: str) -> None:
    base = f"https://api.github.com/repos/{repo}/labels"
    label_url = f"{base}/{urllib.parse.quote(name)}"
    payload = {"name": name, "color": color, "description": description}
    try:
        github_json(label_url, token, method="PATCH", payload=payload)
        print(f"updated label: {name}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        github_json(base, token, method="POST", payload=payload)
        print(f"created label: {name}")


def fetch_good_first_issues(repo: str, token: str | None) -> list[dict[str, object]]:
    encoded_label = urllib.parse.quote("good first issue")
    issues: list[dict[str, object]] = []
    for page in range(1, 11):
        url = (
            f"https://api.github.com/repos/{repo}/issues"
            f"?state=open&labels={encoded_label}&per_page=100&page={page}"
        )
        data = github_json(url, token)
        if not isinstance(data, list):
            raise TypeError("GitHub issues response was not a list")
        issues.extend(issue for issue in data if isinstance(issue, dict) and "pull_request" not in issue)
        if len(data) < 100:
            break
    return sorted(issues, key=lambda issue: int(issue.get("number", 0)))


def fetch_issue(repo: str, token: str | None, number: int) -> dict[str, object]:
    data = github_json(f"https://api.github.com/repos/{repo}/issues/{number}", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub issue response was not an object")
    return data


def fetch_discovery_issues(repo: str, token: str | None) -> list[dict[str, object]]:
    issues_by_number = {
        int(issue.get("number", 0)): issue
        for issue in fetch_good_first_issues(repo, token)
        if int(issue.get("number", 0))
    }
    for number in sorted(UP_FOR_GRABS_ISSUES):
        if number not in issues_by_number:
            issues_by_number[number] = fetch_issue(repo, token, number)
    return [issues_by_number[number] for number in sorted(issues_by_number)]


def apply_labels(repo: str, token: str | None, dry_run: bool) -> tuple[int, int]:
    issues = fetch_discovery_issues(repo, token)
    updated = 0
    skipped = 0
    for issue in issues:
        number = int(issue.get("number", 0))
        existing = {str(label.get("name", "")) for label in issue.get("labels", []) if isinstance(label, dict)}
        desired = {"up-for-grabs"}
        if number in FIRST_TIMERS_ISSUES:
            desired.add("good first issue")
            desired.add("first-timers-only")
        missing = sorted(desired - existing)
        if not missing:
            skipped += 1
            print(f"skip #{number}: labels already present")
            continue
        print(f"{'would label' if dry_run else 'label'} #{number}: {', '.join(missing)}")
        if not dry_run:
            url = f"https://api.github.com/repos/{repo}/issues/{number}/labels"
            github_json(url, token, method="POST", payload={"labels": missing})
        updated += 1
    return updated, skipped


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying labels")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token and not args.dry_run:
        print("GITHUB_TOKEN or GH_TOKEN is required unless --dry-run is used", file=sys.stderr)
        return 2

    if not args.dry_run:
        for name, meta in DISCOVERY_LABELS.items():
            ensure_label(args.repo, token, name, meta["color"], meta["description"])
    updated, skipped = apply_labels(args.repo, token, args.dry_run)
    print(f"updated={updated} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
