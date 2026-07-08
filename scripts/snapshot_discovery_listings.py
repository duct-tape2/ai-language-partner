#!/usr/bin/env python3
"""Snapshot external contributor discovery channels.

The output is operational evidence, not Claude for OSS contributor evidence.
Only useful merged PRs from unique external contributors count toward the
community-builder threshold.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


MARKER = "<!-- discovery-listings-status -->"
DEFAULT_REPO = "duct-tape2/ai-language-partner"
DEFAULT_ISSUE = 52


@dataclass(frozen=True)
class ListingPr:
    name: str
    repo: str
    number: int
    contributor_link: str


LISTING_PRS = [
    ListingPr(
        name="Up For Grabs",
        repo="up-for-grabs/up-for-grabs.net",
        number=5916,
        contributor_link="https://github.com/duct-tape2/ai-language-partner/labels/up-for-grabs",
    ),
    ListingPr(
        name="Awesome for Beginners",
        repo="MunGell/awesome-for-beginners",
        number=2072,
        contributor_link="https://github.com/duct-tape2/ai-language-partner/labels/first-timers-only",
    ),
]


def github_json(url: str, token: str | None, method: str = "GET", payload: object | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-discovery-listings",
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


def count_open_issues(repo: str, label: str, token: str | None) -> int:
    encoded = urllib.parse.quote(label)
    total = 0
    for page in range(1, 11):
        url = f"https://api.github.com/repos/{repo}/issues?state=open&labels={encoded}&per_page=100&page={page}"
        data = github_json(url, token)
        if not isinstance(data, list):
            raise TypeError("GitHub issues response was not a list")
        total += sum(1 for issue in data if isinstance(issue, dict) and "pull_request" not in issue)
        if len(data) < 100:
            break
    return total


def fetch_listing_pr(pr: ListingPr, token: str | None) -> dict[str, object]:
    data = github_json(f"https://api.github.com/repos/{pr.repo}/pulls/{pr.number}", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub pull request response was not an object")
    checks: list[str] = []
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    sha = str(head.get("sha", ""))
    if sha:
        check_data = github_json(f"https://api.github.com/repos/{pr.repo}/commits/{sha}/check-runs?per_page=50", token)
        if isinstance(check_data, dict):
            for run in check_data.get("check_runs", []):
                if isinstance(run, dict):
                    checks.append(f"{run.get('name')}: {run.get('status')} {run.get('conclusion')}")
    return {
        "name": pr.name,
        "url": str(data.get("html_url", "")),
        "state": str(data.get("state", "")),
        "merged": bool(data.get("merged", False)),
        "mergeable": data.get("mergeable"),
        "draft": bool(data.get("draft", False)),
        "checks": checks,
        "contributor_link": pr.contributor_link,
    }


def build_markdown(repo: str, token: str | None) -> str:
    up_for_grabs = count_open_issues(repo, "up-for-grabs", token)
    first_timers = count_open_issues(repo, "first-timers-only", token)
    listing_rows = []
    for pr in LISTING_PRS:
        status = fetch_listing_pr(pr, token)
        checks = "; ".join(status["checks"]) if status["checks"] else "none reported"
        status = {**status, "checks": checks}
        listing_rows.append(
            "| {name} | {state} | {merged} | {mergeable} | [PR]({url}) | [issues]({contributor_link}) | {checks} |".format(
                **status,
            )
        )

    rows = [
        MARKER,
        "# Contributor Discovery Listing Status",
        "",
        "These channels help external contributors find starter issues. They do not",
        "count as Claude for OSS contributor evidence until real external PRs are",
        "merged in this repository.",
        "",
        f"- Repository: `https://github.com/{repo}`",
        f"- Open `up-for-grabs` issues: `{up_for_grabs}`",
        f"- Open `first-timers-only` issues: `{first_timers}`",
        "",
        "| Listing | State | Merged | Mergeable | PR | Contributor link | Checks |",
        "|---|---|---|---|---|---|---|",
        *listing_rows,
    ]
    return "\n".join(rows)


def upsert_issue_comment(repo: str, issue: int, body: str, token: str) -> str:
    comments_url = f"https://api.github.com/repos/{repo}/issues/{issue}/comments?per_page=100"
    comments = github_json(comments_url, token)
    if not isinstance(comments, list):
        raise TypeError("GitHub comments response was not a list")
    for comment in comments:
        if isinstance(comment, dict) and MARKER in str(comment.get("body", "")):
            updated = github_json(str(comment["url"]), token, method="PATCH", payload={"body": body})
            if isinstance(updated, dict):
                return str(updated.get("html_url", ""))
    created = github_json(
        f"https://api.github.com/repos/{repo}/issues/{issue}/comments",
        token,
        method="POST",
        payload={"body": body},
    )
    if isinstance(created, dict):
        return str(created.get("html_url", ""))
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--issue", type=int, default=DEFAULT_ISSUE)
    parser.add_argument("--out", help="Write the Markdown snapshot to a file")
    parser.add_argument("--comment", action="store_true", help="Create or update the sprint issue status comment")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.comment and not token:
        print("GITHUB_TOKEN or GH_TOKEN is required for --comment", file=sys.stderr)
        return 2

    body = build_markdown(args.repo, token)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body + "\n", encoding="utf-8")
    else:
        print(body)

    if args.comment:
        url = upsert_issue_comment(args.repo, args.issue, body, str(token))
        print(f"status comment: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
