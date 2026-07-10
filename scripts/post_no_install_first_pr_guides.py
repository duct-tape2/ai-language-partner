#!/usr/bin/env python3
"""Render and optionally post no-install first-PR guide comments."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "docs" / "community" / "NO_INSTALL_FIRST_PRS.md"
DEFAULT_OUT = ROOT / "docs" / "community" / "NO_INSTALL_FIRST_PR_COMMENTS.md"
MARKER = "<!-- ai-language-partner:no-install-first-pr -->"
COMMUNITY_PAGES = "https://duct-tape2.github.io/ai-language-partner/community"
DIRECTORY_FIRST_PR = f"{COMMUNITY_PAGES}/DIRECTORY_FIRST_PR.html"
FIRST_ISSUE_MATCHER = f"{COMMUNITY_PAGES}/FIRST_ISSUE_MATCHER.html"
FIVE_MINUTE_FIRST_PR = f"{COMMUNITY_PAGES}/FIVE_MINUTE_FIRST_PR.html"
CODESPACES_FIRST_PR = f"{COMMUNITY_PAGES}/CODESPACES_FIRST_PR.html"
KOREAN_FIVE_MINUTE_FIRST_PR = f"{COMMUNITY_PAGES}/FIVE_MINUTE_FIRST_PR_KO.html"
KOREAN_CONTRIBUTOR_INTEREST_TEMPLATE = "contributor_interest_ko.yml"
JAPANESE_FIVE_MINUTE_FIRST_PR = f"{COMMUNITY_PAGES}/FIVE_MINUTE_FIRST_PR_JA.html"
JAPANESE_CONTRIBUTOR_INTEREST_TEMPLATE = "contributor_interest_ja.yml"
LANGUAGE_REVIEW_KIT = f"{COMMUNITY_PAGES}/LANGUAGE_REVIEW_FIRST_PR_KIT.html"
NO_INSTALL_BOARD = f"{COMMUNITY_PAGES}/NO_INSTALL_FIRST_PRS.html"
FIRST_PR_HELP_DESK = "https://github.com/duct-tape2/ai-language-partner/discussions/53"


@dataclass(frozen=True)
class NoInstallTask:
    number: int
    title: str
    issue_url: str
    good_pr_shape: str
    source_file: str
    edit_url: str


def github_json(url: str, token: str | None, method: str = "GET", payload: dict[str, object] | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-no-install-guides",
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


def strip_inline_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def parse_board(text: str) -> list[NoInstallTask]:
    tasks: list[NoInstallTask] = []
    row = re.compile(
        r"^\|\s+\[#(?P<number>\d+): (?P<title>[^\]]+)\]\((?P<issue>[^)]+)\)\s+"
        r"\|\s+(?P<shape>.*?)\s+"
        r"\|\s+(?P<source>`[^`]+`)\s+"
        r"\|\s+\[edit\]\((?P<edit>[^)]+)\)\s+\|$"
    )
    for line in text.splitlines():
        match = row.match(line)
        if not match:
            continue
        tasks.append(
            NoInstallTask(
                number=int(match.group("number")),
                title=match.group("title").strip(),
                issue_url=match.group("issue").strip(),
                good_pr_shape=match.group("shape").strip(),
                source_file=strip_inline_code(match.group("source")),
                edit_url=match.group("edit").strip(),
            )
        )
    return tasks


def render_comment(repo: str, task: NoInstallTask) -> str:
    return f"""{MARKER}
### No-install first PR path

This issue can be started in the GitHub web editor. No local Expo app, FastAPI
backend, STT/TTS engine, generated audio, private data, or API key is needed.

**Suggested browser-only change**

{task.good_pr_shape}

**Start here**

- Hosted web demo: https://duct-tape2.github.io/ai-language-partner/demo/
- Directory first PR fast lane: {DIRECTORY_FIRST_PR}
- First issue matcher: {FIRST_ISSUE_MATCHER}
- Five-minute first PR: {FIVE_MINUTE_FIRST_PR}
- Codespaces first PR guide: {CODESPACES_FIRST_PR}
- Korean five-minute first PR: {KOREAN_FIVE_MINUTE_FIRST_PR}
- Korean contributor interest form: https://github.com/{repo}/issues/new?template={KOREAN_CONTRIBUTOR_INTEREST_TEMPLATE}
- Japanese five-minute first PR: {JAPANESE_FIVE_MINUTE_FIRST_PR}
- Japanese contributor interest form: https://github.com/{repo}/issues/new?template={JAPANESE_CONTRIBUTOR_INTEREST_TEMPLATE}
- Language review first PR kit: {LANGUAGE_REVIEW_KIT}
- First PR help desk: {FIRST_PR_HELP_DESK}
- Source file: `{task.source_file}`
- Direct edit link: {task.edit_url}
- No-install board: {NO_INSTALL_BOARD}

**PR checklist**

- Keep the PR focused on this issue.
- In the PR body, write `Closes #{task.number}`.
- Say that this was docs/content/language review only if no command-line check
  was needed.
- Do not add generated `.wav`, `.zip`, `.npy`, `.sqlite`, screenshot, local
  engine, secret, private note, or private dataset files.

Only useful, reviewable PRs count toward Claude for OSS evidence. Tiny split
PRs made only to increase the count do not count.
"""


def render_markdown(repo: str, tasks: list[NoInstallTask], generated_on: str) -> str:
    lines = [
        "# No-Install First PR Issue Comments",
        "",
        "These comments are generated from `docs/community/NO_INSTALL_FIRST_PRS.md`.",
        "They are posted to matching issues with a marker so reruns update the same",
        "comment instead of creating duplicates.",
        "",
        f"- Repository: `https://github.com/{repo}`",
        f"- Generated on: `{generated_on}`",
        f"- Issues covered: `{len(tasks)}`",
        "",
    ]
    for task in tasks:
        lines.extend([f"## [#{task.number}: {task.title}]({task.issue_url})", "", render_comment(repo, task), ""])
    return "\n".join(lines).rstrip() + "\n"


def upsert_comment(repo: str, task: NoInstallTask, token: str) -> tuple[str, str]:
    comments_url = f"https://api.github.com/repos/{repo}/issues/{task.number}/comments?per_page=100"
    comments = github_json(comments_url, token)
    if not isinstance(comments, list):
        raise TypeError("GitHub comments response was not a list")
    body = render_comment(repo, task)
    for comment in comments:
        if isinstance(comment, dict) and MARKER in str(comment.get("body") or ""):
            updated = github_json(str(comment["url"]), token, method="PATCH", payload={"body": body})
            if not isinstance(updated, dict):
                raise TypeError("GitHub comment response was not an object")
            return "updated", str(updated.get("html_url") or "")
    created = github_json(
        f"https://api.github.com/repos/{repo}/issues/{task.number}/comments",
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
    parser.add_argument("--board", default=str(BOARD), help="No-install board Markdown file")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Markdown file to write")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Generated date")
    parser.add_argument("--apply", action="store_true", help="Create or update GitHub issue comments")
    args = parser.parse_args(argv[1:])

    tasks = parse_board(Path(args.board).read_text(encoding="utf-8"))
    if not tasks:
        print(f"no no-install tasks parsed from {args.board}", file=sys.stderr)
        return 1

    markdown = render_markdown(args.repo, tasks, args.date)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(f"wrote {out} with {len(tasks)} issue guide(s)")

    if args.apply:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            print("--apply requires GITHUB_TOKEN or GH_TOKEN", file=sys.stderr)
            return 2
        created = 0
        updated = 0
        for task in tasks:
            action, url = upsert_comment(args.repo, task, token)
            if action == "created":
                created += 1
            else:
                updated += 1
            print(f"{action} #{task.number}: {url}")
        print(f"created={created} updated={updated}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
