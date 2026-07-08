#!/usr/bin/env python3
"""Export merged-PR contributor evidence for Claude for OSS.

Usage:
  python scripts/export_claude_for_oss_evidence.py duct-tape2/ai-language-partner
  GITHUB_TOKEN=... python scripts/export_claude_for_oss_evidence.py duct-tape2/ai-language-partner --since 2025-07-08

The output is a Markdown table suitable for docs/CLAUDE_FOR_OSS_APPLICATION.md.
It counts unique external PR authors only once and excludes the repo owner,
bots, and users named with --exclude.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class EvidencePr:
    contributor: str
    number: int
    title: str
    url: str
    area: str
    merged_at: str
    author_association: str


def request_json(url: str, token: str | None) -> dict[str, object]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-claude-for-oss-evidence",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def default_since() -> str:
    return (dt.date.today() - dt.timedelta(days=365)).isoformat()


def is_bot(login: str, user_type: str | None) -> bool:
    return user_type == "Bot" or login.endswith("[bot]") or login in {"dependabot", "renovate-bot"}


def infer_area(labels: list[dict[str, object]], title: str) -> str:
    names = [str(label.get("name", "")) for label in labels]
    for candidate in ("docs", "content", "language-review", "accessibility", "mobile", "backend", "tests", "release", "security"):
        if candidate in names:
            return candidate
    if ":" in title:
        return title.split(":", 1)[0]
    return "TBD"


def search_merged_prs(repo: str, since: str, token: str | None) -> list[dict[str, object]]:
    query = f"repo:{repo} is:pr is:merged merged:>={since}"
    all_items: list[dict[str, object]] = []
    for page in range(1, 11):
        params = urllib.parse.urlencode(
            {
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": "100",
                "page": str(page),
            }
        )
        data = request_json(f"https://api.github.com/search/issues?{params}", token)
        items = data.get("items", [])
        if not isinstance(items, list):
            raise TypeError("GitHub search response did not include an item list")
        all_items.extend(items)
        if len(items) < 100:
            break
    return all_items


def pr_merged_at(pr_api_url: str, token: str | None, fallback: str) -> str:
    try:
        data = request_json(pr_api_url, token)
    except urllib.error.HTTPError:
        return fallback
    return str(data.get("merged_at") or fallback)


def collect_evidence(repo: str, since: str, excluded: set[str], token: str | None) -> list[EvidencePr]:
    owner = repo.split("/", 1)[0].lower()
    excluded_lower = {name.lower() for name in excluded} | {owner}
    by_contributor: dict[str, EvidencePr] = {}

    for item in search_merged_prs(repo, since, token):
        user = item.get("user") or {}
        if not isinstance(user, dict):
            continue
        login = str(user.get("login", ""))
        if not login or login.lower() in excluded_lower:
            continue
        if is_bot(login, str(user.get("type", ""))):
            continue
        association = str(item.get("author_association") or "")
        if association in {"OWNER", "MEMBER", "COLLABORATOR"}:
            continue
        if login in by_contributor:
            continue

        pull_request = item.get("pull_request") or {}
        if not isinstance(pull_request, dict):
            continue
        pr_api_url = str(pull_request.get("url") or "")
        closed_at = str(item.get("closed_at") or "")
        merged_at = pr_merged_at(pr_api_url, token, closed_at) if pr_api_url else closed_at
        labels = item.get("labels") if isinstance(item.get("labels"), list) else []
        title = str(item.get("title", ""))

        evidence = EvidencePr(
            contributor=login,
            number=int(item.get("number", 0)),
            title=title,
            url=str(item.get("html_url", "")),
            area=infer_area(labels, title),
            merged_at=merged_at[:10],
            author_association=association or "NONE",
        )
        by_contributor[login] = evidence

    return sorted(by_contributor.values(), key=lambda pr: (pr.merged_at, pr.number), reverse=True)


def markdown_table(prs: list[EvidencePr], limit: int) -> str:
    rows = [
        "| # | Contributor | PR URL | Area | Merged date | Review note |",
        "|---|---|---|---|---|---|",
    ]
    for index, pr in enumerate(prs[:limit], start=1):
        title = pr.title.replace("|", "\\|")
        rows.append(
            f"| {index} | `{pr.contributor}` | [#{pr.number}: {title}]({pr.url}) | "
            f"{pr.area} | {pr.merged_at} | Linked issue + maintainer review |"
        )
    return "\n".join(rows)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--since", default=default_since(), help="Earliest merged date, YYYY-MM-DD")
    parser.add_argument("--require", type=int, default=20, help="Minimum unique external contributors")
    parser.add_argument("--limit", type=int, default=20, help="Rows to print")
    parser.add_argument("--exclude", action="append", default=[], help="Extra GitHub login to exclude")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        prs = collect_evidence(args.repo, args.since, set(args.exclude), token)
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8"), file=sys.stderr)
        return 1

    search_url = "https://github.com/" + args.repo + "/pulls?q=" + urllib.parse.quote(
        f"is:pr is:merged merged:>={args.since}",
        safe=":",
    )
    print(f"# Claude for OSS contributor evidence for `{args.repo}`")
    print()
    print(f"- Since: `{args.since}`")
    print(f"- Unique external contributors counted: `{len(prs)}`")
    print(f"- Merged PR search: {search_url}")
    print()
    print(markdown_table(prs, args.limit))

    if len(prs) < args.require:
        print(
            f"\nNeed {args.require - len(prs)} more unique external merged PR contributor(s) "
            f"to reach the community-builder threshold.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
