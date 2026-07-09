#!/usr/bin/env python3
"""Snapshot the contributor funnel for the Claude for OSS community-builder path."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from export_claude_for_oss_evidence import collect_evidence, default_since
from post_no_install_first_pr_guides import BOARD as NO_INSTALL_BOARD_PATH
from post_no_install_first_pr_guides import parse_board as parse_no_install_board


MARKER = "<!-- ai-language-partner:contributor-funnel-status -->"
DEFAULT_REPO = "duct-tape2/ai-language-partner"
DEFAULT_ISSUE = 52
MAINTAINER_LOGINS = {"duct-tape2", "sinmb79"}
HOSTED_DEMO = "https://duct-tape2.github.io/ai-language-partner/demo/"
FIRST_PR_GUIDE = "https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md"
NO_INSTALL_BOARD = "https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md"
HELP_DESK = "https://github.com/duct-tape2/ai-language-partner/discussions/53"
CALL_DISCUSSION = "https://github.com/duct-tape2/ai-language-partner/discussions/55"
CLAIM_RE = re.compile(
    r"(^|\n)\s*/claim\b|(^|\n)\s*claim\b|\bi can work on this\b|\bi'll take this\b|\bcan i take this\b|"
    r"제가\s*(해볼게요|하겠습니다|맡겠습니다)|작업해도\s*될까요|やります|担当します|取り組みます",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class IssueItem:
    number: int
    title: str
    url: str
    login: str
    created_at: str
    updated_at: str
    labels: tuple[str, ...]


@dataclass(frozen=True)
class ClaimSignal:
    issue_number: int
    issue_title: str
    issue_url: str
    login: str
    comment_url: str
    created_at: str


def github_json(url: str, token: str | None, method: str = "GET", payload: object | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-contributor-funnel",
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


def search_issues(repo: str, query: str, token: str | None, limit: int = 25) -> list[IssueItem]:
    params = urllib.parse.urlencode(
        {
            "q": f"repo:{repo} {query}",
            "sort": "updated",
            "order": "desc",
            "per_page": str(min(100, limit)),
        }
    )
    data = github_json(f"https://api.github.com/search/issues?{params}", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub search response was not an object")
    items: list[IssueItem] = []
    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue
        user = item.get("user") if isinstance(item.get("user"), dict) else {}
        labels = item.get("labels") if isinstance(item.get("labels"), list) else []
        items.append(
            IssueItem(
                number=int(item.get("number", 0)),
                title=str(item.get("title", "")),
                url=str(item.get("html_url", "")),
                login=str(user.get("login", "")),
                created_at=str(item.get("created_at", "")),
                updated_at=str(item.get("updated_at", "")),
                labels=tuple(str(label.get("name", "")) for label in labels if isinstance(label, dict)),
            )
        )
    return items


def count_open_issues(repo: str, label: str, token: str | None) -> int:
    encoded = urllib.parse.quote(label)
    total = 0
    for page in range(1, 11):
        data = github_json(
            f"https://api.github.com/repos/{repo}/issues?state=open&labels={encoded}&per_page=100&page={page}",
            token,
        )
        if not isinstance(data, list):
            raise TypeError("GitHub issues response was not a list")
        total += sum(1 for issue in data if isinstance(issue, dict) and "pull_request" not in issue)
        if len(data) < 100:
            break
    return total


def no_install_task_count() -> int:
    try:
        return len(parse_no_install_board(NO_INSTALL_BOARD_PATH.read_text(encoding="utf-8")))
    except OSError:
        return 0


def is_external(item: IssueItem) -> bool:
    return bool(item.login) and item.login not in MAINTAINER_LOGINS and not item.login.endswith("[bot]")


def open_external_prs(repo: str, token: str | None) -> list[IssueItem]:
    return [item for item in search_issues(repo, "is:pr is:open", token, limit=50) if is_external(item)]


def contributor_interest_issues(repo: str, token: str | None) -> list[IssueItem]:
    return [item for item in search_issues(repo, 'is:issue is:open "Contribution lane"', token, limit=20) if is_external(item)]


def open_starter_issues(repo: str, token: str | None) -> list[IssueItem]:
    return search_issues(repo, 'is:issue is:open label:"first-timers-only"', token, limit=10)


def issue_claim_signals(repo: str, token: str | None, max_issues: int = 100) -> list[ClaimSignal]:
    data = github_json(f"https://api.github.com/repos/{repo}/issues?state=open&per_page={max_issues}", token)
    if not isinstance(data, list):
        raise TypeError("GitHub issues response was not a list")
    claims: list[ClaimSignal] = []
    for issue in data:
        if not isinstance(issue, dict) or "pull_request" in issue:
            continue
        comments_url = str(issue.get("comments_url") or "")
        if not comments_url:
            continue
        comments = github_json(f"{comments_url}?per_page=100", token)
        if not isinstance(comments, list):
            continue
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            body = str(comment.get("body") or "")
            user = comment.get("user") if isinstance(comment.get("user"), dict) else {}
            login = str(user.get("login", ""))
            if login.endswith("[bot]") or not CLAIM_RE.search(body):
                continue
            claims.append(
                ClaimSignal(
                    issue_number=int(issue.get("number", 0)),
                    issue_title=str(issue.get("title", "")),
                    issue_url=str(issue.get("html_url", "")),
                    login=login,
                    comment_url=str(comment.get("html_url", "")),
                    created_at=str(comment.get("created_at", "")),
                )
            )
    return sorted(claims, key=lambda claim: claim.created_at, reverse=True)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def render_issue_rows(items: list[IssueItem], empty: str) -> list[str]:
    if not items:
        return [f"| {empty} | - | - |"]
    rows = []
    for item in items[:10]:
        rows.append(f"| [#{item.number}: {escape_cell(item.title)}]({item.url}) | `{item.login}` | `{item.updated_at[:10]}` |")
    return rows


def render_claim_rows(claims: list[ClaimSignal]) -> list[str]:
    if not claims:
        return ["| No active claim signals found | - | - |"]
    rows = []
    for claim in claims[:10]:
        rows.append(
            f"| [#{claim.issue_number}: {escape_cell(claim.issue_title)}]({claim.issue_url}) | "
            f"`{claim.login}` | [comment]({claim.comment_url}) |"
        )
    return rows


def build_markdown(repo: str, since: str, generated_on: str, token: str | None) -> str:
    evidence = collect_evidence(repo, since, set(), token)
    external_prs = open_external_prs(repo, token)
    claims = issue_claim_signals(repo, token)
    interests = contributor_interest_issues(repo, token)
    starter_issues = open_starter_issues(repo, token)
    up_for_grabs = count_open_issues(repo, "up-for-grabs", token)
    first_timers = count_open_issues(repo, "first-timers-only", token)
    needed = max(0, 20 - len(evidence))
    phase = "ready" if len(evidence) >= 20 else "not ready"

    return "\n".join(
        [
            MARKER,
            "# Contributor Funnel Status",
            "",
            "This is an operating dashboard for the Claude for OSS community-builder",
            "route. It is not evidence by itself; only useful merged PRs from real",
            "external contributors count.",
            "",
            f"- Repository: `https://github.com/{repo}`",
            f"- Updated: `{generated_on}`",
            f"- Evidence window starts: `{since}`",
            f"- Phase B readiness: `{phase}`",
            f"- Unique external merged PR contributors: `{len(evidence)}/20`",
            f"- Remaining contributors needed: `{needed}`",
            f"- Open external PRs needing maintainer attention: `{len(external_prs)}`",
            f"- Active claim signals on open issues: `{len(claims)}`",
            f"- Open contributor interest issues: `{len(interests)}`",
            f"- Open `up-for-grabs` issues: `{up_for_grabs}`",
            f"- Open `first-timers-only` issues: `{first_timers}`",
            f"- Browser-only no-install issue slots: `{no_install_task_count()}`",
            "",
            "## Fastest Contributor Entry Points",
            "",
            f"- Hosted web demo: {HOSTED_DEMO}",
            f"- Call for contributors discussion: {CALL_DISCUSSION}",
            f"- Five-minute first PR guide: {FIRST_PR_GUIDE}",
            f"- No-install first PR board: {NO_INSTALL_BOARD}",
            f"- First PR help desk: {HELP_DESK}",
            "",
            "## Open External PRs",
            "",
            "| PR | Author | Updated |",
            "|---|---|---|",
            *render_issue_rows(external_prs, "No open external PRs"),
            "",
            "## Active Claim Signals",
            "",
            "| Issue | Contributor | Claim comment |",
            "|---|---|---|",
            *render_claim_rows(claims),
            "",
            "## Contributor Interest Issues",
            "",
            "| Issue | Author | Updated |",
            "|---|---|---|",
            *render_issue_rows(interests, "No contributor interest issues"),
            "",
            "## Starter Issue Spotlight",
            "",
            "| Issue | Author | Updated |",
            "|---|---|---|",
            *render_issue_rows(starter_issues, "No first-timers-only issues found"),
            "",
            "## Maintainer SLA",
            "",
            "- Reply to external PRs and claim signals within 24 hours when possible.",
            "- Merge only focused, useful PRs after human review.",
            "- Do not count bots, duplicate identities, maintainer-authored PRs, or",
            "  metric-only changes.",
        ]
    )


def upsert_issue_comment(repo: str, issue: int, body: str, token: str) -> str:
    comments = github_json(f"https://api.github.com/repos/{repo}/issues/{issue}/comments?per_page=100", token)
    if not isinstance(comments, list):
        raise TypeError("GitHub comments response was not a list")
    for comment in comments:
        if isinstance(comment, dict) and MARKER in str(comment.get("body") or ""):
            updated = github_json(str(comment["url"]), token, method="PATCH", payload={"body": body})
            if isinstance(updated, dict):
                return str(updated.get("html_url") or "")
    created = github_json(
        f"https://api.github.com/repos/{repo}/issues/{issue}/comments",
        token,
        method="POST",
        payload={"body": body},
    )
    if isinstance(created, dict):
        return str(created.get("html_url") or "")
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--issue", type=int, default=DEFAULT_ISSUE)
    parser.add_argument("--since", default=default_since())
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--out", help="Write the funnel Markdown to a file")
    parser.add_argument("--comment", action="store_true", help="Create or update the funnel status issue comment")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.comment and not token:
        print("GITHUB_TOKEN or GH_TOKEN is required for --comment", file=sys.stderr)
        return 2

    body = build_markdown(args.repo, args.since, args.date, token)
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
