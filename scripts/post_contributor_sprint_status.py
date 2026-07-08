#!/usr/bin/env python3
"""Create or update the public 20-contributor sprint status comment."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from export_claude_for_oss_evidence import collect_evidence, default_since
from post_no_install_first_pr_guides import BOARD as NO_INSTALL_BOARD_PATH
from post_no_install_first_pr_guides import parse_board as parse_no_install_board


MARKER = "<!-- ai-language-partner:contributor-sprint-status -->"
DEFAULT_ISSUE = 52
FIRST_PR_GUIDE = "https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md"
NO_INSTALL_BOARD = "https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md"
HELP_DESK = "https://github.com/duct-tape2/ai-language-partner/discussions/53"
INTEREST_FORM = "https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml"


@dataclass(frozen=True)
class SpotlightIssue:
    number: int
    title: str
    url: str
    labels: tuple[str, ...]


def github_json(url: str, token: str | None, method: str = "GET", payload: object | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-contributor-sprint-status",
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


def search_issues(repo: str, query: str, token: str | None, limit: int) -> list[SpotlightIssue]:
    params = urllib.parse.urlencode(
        {
            "q": f"repo:{repo} is:issue is:open {query}",
            "sort": "created",
            "order": "asc",
            "per_page": str(min(100, limit)),
        }
    )
    data = github_json(f"https://api.github.com/search/issues?{params}", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub search response was not an object")
    issues: list[SpotlightIssue] = []
    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue
        labels = item.get("labels") if isinstance(item.get("labels"), list) else []
        issues.append(
            SpotlightIssue(
                number=int(item.get("number", 0)),
                title=str(item.get("title", "")),
                url=str(item.get("html_url", "")),
                labels=tuple(str(label.get("name", "")) for label in labels if isinstance(label, dict)),
            )
        )
    return issues


def fetch_spotlight_issues(repo: str, token: str | None, limit: int = 10) -> list[SpotlightIssue]:
    seen: set[int] = set()
    issues: list[SpotlightIssue] = []
    queries = [
        'label:"first-timers-only"',
        'label:"up-for-grabs"',
        'label:"good first issue"',
    ]
    for query in queries:
        for issue in search_issues(repo, query, token, limit):
            if issue.number in seen:
                continue
            seen.add(issue.number)
            issues.append(issue)
            if len(issues) >= limit:
                return issues
    return issues


def label_summary(issue: SpotlightIssue) -> str:
    useful = [
        label
        for label in issue.labels
        if label
        in {
            "docs",
            "content",
            "language-review",
            "accessibility",
            "mobile",
            "backend",
            "tests",
            "community",
            "first-timers-only",
            "up-for-grabs",
            "good first issue",
        }
    ]
    return ", ".join(f"`{label}`" for label in useful[:5]) or "starter"


def escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|")


def no_install_task_count() -> int:
    try:
        return len(parse_no_install_board(NO_INSTALL_BOARD_PATH.read_text(encoding="utf-8")))
    except OSError:
        return 0


def render_status(
    repo: str,
    since: str,
    generated_on: str,
    contributor_count: int,
    issues: list[SpotlightIssue],
    no_install_count: int = 0,
) -> str:
    needed = max(0, 20 - contributor_count)
    phase = "ready" if contributor_count >= 20 else "not ready"
    issue_rows = [
        f"| [#{issue.number}: {escape_table_cell(issue.title)}]({issue.url}) | {label_summary(issue)} |"
        for issue in issues
    ]
    if not issue_rows:
        issue_rows = ["| No open starter issues found | Check the issue tracker manually |"]

    return "\n".join(
        [
            MARKER,
            "# 20 Contributor Sprint Status",
            "",
            "This comment is a public recruiting and tracking aid. It is not Claude",
            "for OSS evidence by itself; only useful merged PRs from real external",
            "contributors count.",
            "",
            f"- Repository: `https://github.com/{repo}`",
            f"- Updated: `{generated_on}`",
            f"- Evidence window starts: `{since}`",
            f"- Phase B readiness: `{phase}`",
            f"- Unique external merged PR contributors: `{contributor_count}/20`",
            f"- Remaining contributors needed: `{needed}`",
            "",
            "## Fastest First PR Path",
            "",
            f"- Five-minute first PR guide: {FIRST_PR_GUIDE}",
            f"- No-install first PR board: {NO_INSTALL_BOARD}",
            f"- Browser-only no-install issue slots: `{no_install_count}`",
            f"- First PR help desk: {HELP_DESK}",
            f"- Contributor interest form: {INTEREST_FORM}",
            "",
            "## Current Starter Issue Spotlight",
            "",
            "| Issue | Labels |",
            "|---|---|",
            *issue_rows,
            "",
            "## Counting Rules",
            "",
            "- One counted PR per unique external human contributor.",
            "- Maintainer-authored PRs, bots, duplicate identities, and metric-only",
            "  changes do not count.",
            "- Docs-only and language-review PRs are welcome when they improve real",
            "  learner or contributor experience.",
            "- Every counted PR needs an issue/problem link and a human maintainer",
            "  review comment before merge.",
        ]
    )


def upsert_issue_comment(repo: str, issue: int, body: str, token: str) -> str:
    comments_url = f"https://api.github.com/repos/{repo}/issues/{issue}/comments?per_page=100"
    comments = github_json(comments_url, token)
    if not isinstance(comments, list):
        raise TypeError("GitHub comments response was not a list")
    for comment in comments:
        if isinstance(comment, dict) and MARKER in str(comment.get("body") or ""):
            updated = github_json(str(comment["url"]), token, method="PATCH", payload={"body": body})
            if not isinstance(updated, dict):
                raise TypeError("GitHub comment response was not an object")
            return str(updated.get("html_url") or "")
    created = github_json(
        f"https://api.github.com/repos/{repo}/issues/{issue}/comments",
        token,
        method="POST",
        payload={"body": body},
    )
    if not isinstance(created, dict):
        raise TypeError("GitHub comment response was not an object")
    return str(created.get("html_url") or "")


def build_status(repo: str, since: str, generated_on: str, token: str | None) -> str:
    evidence = collect_evidence(repo, since, set(), token)
    issues = fetch_spotlight_issues(repo, token)
    return render_status(repo, since, generated_on, len(evidence), issues, no_install_task_count())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--issue", type=int, default=DEFAULT_ISSUE)
    parser.add_argument("--since", default=default_since(), help="Earliest merged date, YYYY-MM-DD")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Generated date")
    parser.add_argument("--out", help="Write the status Markdown to a file")
    parser.add_argument("--comment", action="store_true", help="Create or update the sprint issue status comment")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.comment and not token:
        print("GITHUB_TOKEN or GH_TOKEN is required for --comment", file=sys.stderr)
        return 2

    body = build_status(args.repo, args.since, args.date, token)
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
