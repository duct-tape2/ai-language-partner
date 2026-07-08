#!/usr/bin/env python3
"""Create or update an automated maintainer PR review packet comment."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

from build_pr_review_packet import fetch_pr_packet


MARKER = "<!-- ai-language-partner:pr-review-packet -->"


def github_json(url: str, token: str, method: str = "GET", payload: dict[str, object] | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "ai-language-partner-pr-review-packet-comment",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def render_comment(repo: str, number: int, token: str | None) -> str:
    packet = fetch_pr_packet(repo, number, token)
    return "\n".join(
        [
            MARKER,
            "## Automated Maintainer Review Packet",
            "",
            "This is a triage aid for the maintainer. It is not a merge decision",
            "and it is not Claude for OSS evidence by itself.",
            "",
            packet.markdown,
        ]
    )


def upsert_comment(repo: str, number: int, body: str, token: str) -> tuple[str, str]:
    comments_url = f"https://api.github.com/repos/{repo}/issues/{number}/comments?per_page=100"
    comments = github_json(comments_url, token)
    if not isinstance(comments, list):
        raise TypeError("GitHub comments response was not a list")
    for comment in comments:
        if isinstance(comment, dict) and MARKER in str(comment.get("body") or ""):
            updated = github_json(str(comment["url"]), token, method="PATCH", payload={"body": body})
            if not isinstance(updated, dict):
                raise TypeError("GitHub comment response was not an object")
            return "updated", str(updated.get("html_url") or "")
    created = github_json(
        f"https://api.github.com/repos/{repo}/issues/{number}/comments",
        token,
        method="POST",
        payload={"body": body},
    )
    if not isinstance(created, dict):
        raise TypeError("GitHub comment response was not an object")
    return "created", str(created.get("html_url") or "")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("number", type=int, help="Pull request number")
    parser.add_argument("--print-only", action="store_true", help="Print the packet instead of posting a comment")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2

    body = render_comment(args.repo, args.number, token)
    if args.print_only:
        print(body)
        return 0

    action, url = upsert_comment(args.repo, args.number, body, token)
    print(f"{action}: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
