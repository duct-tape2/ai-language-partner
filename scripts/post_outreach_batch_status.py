#!/usr/bin/env python3
"""Post the next contributor outreach batch to the public sprint issue."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "docs" / "community" / "OUTREACH_QUEUE.json"
MARKER = "<!-- ai-language-partner:outreach-batch-status -->"
DEFAULT_REPO = "duct-tape2/ai-language-partner"
DEFAULT_ISSUE = 52
DEFAULT_LIMIT = 5
SHARE_KIT = "https://duct-tape2.github.io/ai-language-partner/community/SHARE_KIT.html"
OUTREACH_MESSAGES = "https://duct-tape2.github.io/ai-language-partner/community/OUTREACH_MESSAGES.html"
HELP_DESK = "https://github.com/duct-tape2/ai-language-partner/discussions/53"


def github_json(url: str, token: str | None, method: str = "GET", payload: object | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-outreach-batch",
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


def load_queue(path: Path = QUEUE) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("outreach queue must be an object")
    items = payload.get("items")
    if not isinstance(items, list):
        raise TypeError("outreach queue items must be a list")
    return payload


def next_batch(items: list[dict[str, object]], limit: int = DEFAULT_LIMIT) -> list[dict[str, object]]:
    priority = {"responded": 0, "draft": 1, "posted": 2, "pr-open": 3}
    candidates = [
        item
        for item in items
        if str(item.get("status", "")) in priority and str(item.get("status", "")) != "merged-counted"
    ]
    candidates.sort(key=lambda item: (priority[str(item.get("status", ""))], str(item.get("id", ""))))
    return candidates[:limit]


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def render_batch_row(item: dict[str, object]) -> str:
    item_id = str(item.get("id", ""))
    audience = escape_cell(str(item.get("audience", "")))
    lane = escape_cell(str(item.get("lane", "")))
    status = str(item.get("status", ""))
    issue_query = str(item.get("issue_query", ""))
    notes = escape_cell(str(item.get("notes", "")))
    return (
        f"| `{item_id}` | {audience} | `{lane}` | `{status}` | "
        f"[target]({issue_query}) | {notes} |"
    )


def build_markdown(repo: str, generated_on: str, limit: int = DEFAULT_LIMIT, queue_path: Path = QUEUE) -> str:
    payload = load_queue(queue_path)
    items = [item for item in payload["items"] if isinstance(item, dict)]
    batch = next_batch(items, limit)
    posted = sum(1 for item in items if str(item.get("posted_url", "")))
    merged_counted = sum(1 for item in items if str(item.get("status", "")) == "merged-counted")
    rows = [render_batch_row(item) for item in batch] or ["| No active outreach items found | - | - | - | - | - |"]

    return "\n".join(
        [
            MARKER,
            "# Outreach Batch Status",
            "",
            "This is an execution checklist for finding real contributors. It is",
            "not Claude for OSS evidence by itself; only useful merged PRs from",
            "real external contributors count.",
            "",
            f"- Repository: `https://github.com/{repo}`",
            f"- Updated: `{generated_on}`",
            f"- Queue items: `{len(items)}`",
            f"- Posted URLs recorded: `{posted}`",
            f"- Outreach items marked merged-counted: `{merged_counted}`",
            f"- Today's batch size: `{len(batch)}`",
            f"- Contributor share kit: {SHARE_KIT}",
            f"- Full rendered outreach messages: {OUTREACH_MESSAGES}",
            f"- First PR help desk: {HELP_DESK}",
            "",
            "## Next Outreach Batch",
            "",
            "| Item | Audience | Lane | Status | Target | Notes |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Posting Rules",
            "",
            "- Tailor each post to the community before posting.",
            "- Do not mass-post identical text.",
            "- Record `posted_url` only after a real public post exists.",
            "- Move an item to `pr-open` only after a real external PR is opened.",
            "- Move an item to `merged-counted` only after the PR passes the",
            "  counting policy and is merged.",
            "- If someone is interested, send them to the help desk or ask them to",
            "  comment `/claim` on a specific issue.",
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
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--out", help="Write the batch Markdown to a file")
    parser.add_argument("--comment", action="store_true", help="Create or update the batch status issue comment")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.comment and not token:
        print("GITHUB_TOKEN or GH_TOKEN is required for --comment", file=sys.stderr)
        return 2

    body = build_markdown(args.repo, args.date, args.limit)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body + "\n", encoding="utf-8")
    else:
        print(body)
    if args.comment:
        url = upsert_issue_comment(args.repo, args.issue, body, str(token))
        print(f"outreach batch comment: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
