#!/usr/bin/env python3
"""Create the public 20-contributor sprint kickoff issue once.

The issue is a public entry point for people who want to help the project reach
the Claude for OSS community-builder route. It is intentionally idempotent.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request


TITLE = "community: 20 contributor sprint kickoff"


BODY = """\
This is the public coordination issue for the 20-contributor sprint.

Goal: make it easy for real external contributors to open useful, reviewable
PRs. This is not a metric-inflation thread. Maintainer-authored PRs, bots,
duplicate identities, and trivial PR splits do not count toward Claude for OSS
evidence.

Start here:

- Sprint lanes: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/CONTRIBUTOR_SPRINT.md
- Good first issues: https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22
- First PR walkthrough: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md

Useful contribution lanes:

- Korean docs and learner notes
- Japanese naturalness and beginner-safety review
- Dialogue source content review
- Expo / React Native accessibility
- FastAPI and OpenAPI examples
- Focused tests and repo checks
- Release and maintainer process docs

Maintainer promise:

- First response target: within 24 hours when possible
- No private context required for `good first issue` tasks
- Docs and content-review PRs are welcome when they improve real learner or
  contributor experience
- Every counted PR needs a human maintainer review comment before merge
"""


def request_json(url: str, token: str, method: str = "GET", payload: dict[str, object] | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "ai-language-partner-contributor-sprint",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def find_existing_issue(repo: str, token: str) -> dict[str, object] | None:
    query = f'repo:{repo} is:issue in:title "{TITLE}"'
    params = urllib.parse.urlencode({"q": query, "per_page": "5"})
    data = request_json(f"https://api.github.com/search/issues?{params}", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub search response was not an object")
    items = data.get("items", [])
    if not isinstance(items, list):
        raise TypeError("GitHub search response did not include an item list")
    for item in items:
        if isinstance(item, dict) and item.get("title") == TITLE:
            return item
    return None


def create_issue(repo: str, token: str) -> dict[str, object]:
    payload = {
        "title": TITLE,
        "body": BODY,
        "labels": ["community", "help wanted"],
    }
    data = request_json(f"https://api.github.com/repos/{repo}/issues", token, method="POST", payload=payload)
    if not isinstance(data, dict):
        raise TypeError("GitHub create issue response was not an object")
    return data


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--dry-run", action="store_true", help="Print the issue payload without creating it")
    args = parser.parse_args(argv[1:])

    if args.dry_run:
        print(json.dumps({"title": TITLE, "body": BODY, "labels": ["community", "help wanted"]}, indent=2))
        return 0

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2

    existing = find_existing_issue(args.repo, token)
    if existing:
        print(json.dumps({"created": False, "number": existing.get("number"), "url": existing.get("html_url")}))
        return 0

    issue = create_issue(args.repo, token)
    print(json.dumps({"created": True, "number": issue.get("number"), "url": issue.get("html_url")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
