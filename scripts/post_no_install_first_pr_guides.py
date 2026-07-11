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
TRUSTED_COMMENT_LOGIN = "github-actions[bot]"
COMMUNITY_PAGES = "https://duct-tape2.github.io/ai-language-partner/community"
FIVE_MINUTE_FIRST_PR = f"{COMMUNITY_PAGES}/FIVE_MINUTE_FIRST_PR.html"
CODESPACES_FIRST_PR = f"{COMMUNITY_PAGES}/CODESPACES_FIRST_PR.html"
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


def authenticated_login(token: str) -> str:
    data = github_json("https://api.github.com/user", token)
    if not isinstance(data, dict) or not data.get("login"):
        raise TypeError("GitHub authenticated-user response did not include a login")
    return str(data["login"])


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


def verification(task: NoInstallTask) -> str:
    source = task.source_file.lower()
    if source.endswith((".ts", ".tsx")):
        return "Run `cd apps/mobile && npm run verify` in Codespaces or let the PR checks run it."
    if source.endswith((".yaml", ".yml")):
        return "Run `cd apps/api && .venv/bin/python -m pytest` in Codespaces or rely on the PR checks."
    if source.endswith(("story.json", "variants.csv")):
        return "Run `python3 scripts/verify_dialogue_pack_sources.py` or let `Dialogue Pack Sources` CI validate it."
    return "Use GitHub preview and name the wording, links, or examples you reviewed; no CLI check is required."


def render_comment(_repo: str, task: NoInstallTask) -> str:
    return f"""{MARKER}
### Edit this issue in your browser

No local app, backend, speech engine, private data, or API key is required.

**Change**

{task.good_pr_shape}

**Edit**

- File: `{task.source_file}`
- [Open the direct edit page]({task.edit_url})

**Finish**

- Comment `/claim`, make only this change, and write `Closes #{task.number}` in
  the PR body.
- {verification(task)}
- Do not add generated media, archives, databases, screenshots, secrets, local
  engines, or private data. Do not split trivial changes across PRs.

**Help**

- [Five-minute browser guide]({FIVE_MINUTE_FIRST_PR})
- [Run checks in Codespaces]({CODESPACES_FIRST_PR})
- [Ask the first PR help desk]({FIRST_PR_HELP_DESK})
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


def existing_guide_comment(
    repo: str,
    number: int,
    token: str,
    trusted_login: str = TRUSTED_COMMENT_LOGIN,
) -> dict[str, object] | None:
    for page in range(1, 6):
        comments_url = (
            f"https://api.github.com/repos/{repo}/issues/{number}/comments"
            f"?per_page=100&page={page}"
        )
        comments = github_json(comments_url, token)
        if not isinstance(comments, list):
            raise TypeError("GitHub comments response was not a list")
        for comment in comments:
            user = comment.get("user") if isinstance(comment, dict) else None
            if (
                isinstance(comment, dict)
                and isinstance(user, dict)
                and user.get("login") == trusted_login
                and MARKER in str(comment.get("body") or "")
            ):
                return comment
        if len(comments) < 100:
            break
    return None


def upsert_comment(
    repo: str,
    task: NoInstallTask,
    token: str,
    trusted_login: str = TRUSTED_COMMENT_LOGIN,
) -> tuple[str, str]:
    body = render_comment(repo, task)
    existing = existing_guide_comment(repo, task.number, token, trusted_login)
    if existing:
        if str(existing.get("body") or "") == body:
            return "unchanged", str(existing.get("html_url") or "")
        updated = github_json(str(existing["url"]), token, method="PATCH", payload={"body": body})
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
    parser.add_argument(
        "--comment-login",
        default="",
        help="Expected author for existing marker comments; PAT runs auto-detect it",
    )
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
        unchanged = 0
        trusted_login = args.comment_login or authenticated_login(token)
        for task in tasks:
            action, url = upsert_comment(args.repo, task, token, trusted_login)
            if action == "created":
                created += 1
            elif action == "updated":
                updated += 1
            else:
                unchanged += 1
            print(f"{action} #{task.number}: {url}")
        print(f"created={created} updated={updated} unchanged={unchanged}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
