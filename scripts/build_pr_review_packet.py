#!/usr/bin/env python3
"""Build a maintainer review packet for a pull request.

The output is a Markdown checklist that helps maintainers review useful external
PRs quickly without overstating Claude for OSS contributor evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


FORBIDDEN_PATH = re.compile(
    r"(^|/)(local_engines|artifacts|handoff|reference_archive)(/|$)"
    r"|(\.sqlite|\.sqlite-shm|\.sqlite-wal|\.db|\.zip|\.wav|\.mp3|\.m4a|\.aac|\.flac|\.ogg|\.npy|\.bin|\.pyc|\.log)$",
    re.IGNORECASE,
)
ISSUE_REF = re.compile(r"(?i)(close[sd]?|fix(e[sd])?|resolve[sd]?|refs?)\s+#\d+|#\d+")


@dataclass(frozen=True)
class ReviewPacket:
    markdown: str
    countable_candidate: bool
    blockers: tuple[str, ...]


def github_json(url: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-pr-review-packet",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def paged_github_json(url: str, token: str | None) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    separator = "&" if "?" in url else "?"
    for page in range(1, 11):
        page_url = f"{url}{separator}per_page=100&page={page}"
        data = github_json(page_url, token)
        if not isinstance(data, list):
            raise TypeError("GitHub response was not a list")
        items.extend(item for item in data if isinstance(item, dict))
        if len(data) < 100:
            break
    return items


def suggested_checks(paths: list[str]) -> list[str]:
    checks = ["python3 scripts/check_public_tree.py"]
    if any(path.startswith("apps/api/") or path.startswith("contracts/") for path in paths):
        checks.append("cd apps/api && .venv/bin/python -m pytest")
    if any(path.startswith("apps/mobile/") or path.startswith("packages/shared/") for path in paths):
        checks.append("cd apps/mobile && npm run verify")
    if any(path.startswith("scripts/") for path in paths):
        checks.append("python3 -m unittest discover -s scripts -p 'test_*.py'")
    if any(path.startswith("docs/community/OUTREACH_QUEUE") for path in paths):
        checks.append("python3 scripts/verify_outreach_queue.py")
    if any(path.startswith("docs/") for path in paths) and len(checks) == 1:
        checks.append("docs/content review: verify links and wording manually")
    return checks


def infer_area(paths: list[str], labels: list[str], title: str) -> str:
    lower_labels = {label.lower() for label in labels}
    for candidate in ("docs", "content", "language-review", "accessibility", "mobile", "backend", "tests", "community"):
        if candidate in lower_labels:
            return candidate
    if any(path.startswith("apps/mobile/") for path in paths):
        return "mobile"
    if any(path.startswith("apps/api/") or path.startswith("contracts/") for path in paths):
        return "backend"
    if any(path.startswith("docs/") for path in paths):
        return "docs"
    if any(path.startswith("scripts/") for path in paths):
        return "tests"
    if ":" in title:
        return title.split(":", 1)[0]
    return "TBD"


def is_bot(login: str, user_type: str) -> bool:
    return user_type == "Bot" or login.endswith("[bot]") or login in {"dependabot", "renovate-bot"}


def build_packet(repo: str, pr: dict[str, object], files: list[dict[str, object]]) -> ReviewPacket:
    owner = repo.split("/", 1)[0].lower()
    number = int(pr.get("number", 0))
    title = str(pr.get("title") or "")
    body = str(pr.get("body") or "")
    html_url = str(pr.get("html_url") or "")
    user = pr.get("user") if isinstance(pr.get("user"), dict) else {}
    login = str(user.get("login") or "")
    user_type = str(user.get("type") or "")
    association = str(pr.get("author_association") or "")
    draft = bool(pr.get("draft"))
    merged = bool(pr.get("merged"))
    labels = [str(label.get("name", "")) for label in pr.get("labels", []) if isinstance(label, dict)]
    paths = [str(file.get("filename") or "") for file in files]
    forbidden = [path for path in paths if FORBIDDEN_PATH.search(path)]
    issue_linked = bool(ISSUE_REF.search(title + "\n" + body))
    checks = suggested_checks(paths)
    area = infer_area(paths, labels, title)

    blockers: list[str] = []
    if not login:
        blockers.append("missing PR author")
    if login.lower() == owner:
        blockers.append("maintainer-authored PR")
    if is_bot(login, user_type):
        blockers.append("bot-authored PR")
    if association in {"OWNER", "MEMBER", "COLLABORATOR"}:
        blockers.append(f"author association is {association}")
    if draft:
        blockers.append("PR is still draft")
    if forbidden:
        blockers.append("generated/private files changed")
    if not issue_linked:
        blockers.append("no issue reference or problem statement detected")
    if not merged:
        blockers.append("PR is not merged yet")

    countable_candidate = not blockers
    changed_files = "\n".join(f"- `{path}`" for path in paths[:40]) or "- none reported"
    forbidden_lines = "\n".join(f"- `{path}`" for path in forbidden) if forbidden else "- none detected"
    check_lines = "\n".join(f"- [ ] `{check}`" for check in checks)
    blocker_lines = "\n".join(f"- {blocker}" for blocker in blockers) if blockers else "- none"
    decision = "merged-counted candidate" if countable_candidate else "not countable yet"

    markdown = f"""# PR Review Packet: #{number}

- PR: [{title}]({html_url})
- Author: `{login}` ({association or 'NONE'}, {user_type or 'unknown'})
- Draft: `{str(draft).lower()}`
- Merged: `{str(merged).lower()}`
- Inferred area: `{area}`
- Countable candidate: `{'yes' if countable_candidate else 'no'}`
- Preliminary decision: `{decision}`

## Blocking / Counting Notes

{blocker_lines}

## Changed Files

{changed_files}

## Generated / Private File Check

{forbidden_lines}

## Suggested Checks

{check_lines}

## Maintainer Review Comment

```text
Thanks for the focused contribution. I checked:

- linked issue / problem statement: {'yes' if issue_linked else 'needs clarification'}
- user or contributor value:
- no generated/private assets: {'yes' if not forbidden else 'no'}
- no runtime-LLM dependency added:
- relevant check:

Decision: merge / request changes / merge but do not count for Claude for OSS evidence.
```

Update `docs/CLAUDE_FOR_OSS_APPLICATION.md` only after the PR is merged and the
counting policy still supports counting it.
"""
    return ReviewPacket(markdown=markdown, countable_candidate=countable_candidate, blockers=tuple(blockers))


def fetch_pr_packet(repo: str, number: int, token: str | None) -> ReviewPacket:
    base = f"https://api.github.com/repos/{repo}"
    pr_data = github_json(f"{base}/pulls/{number}", token)
    if not isinstance(pr_data, dict):
        raise TypeError("GitHub PR response was not an object")
    files = paged_github_json(f"{base}/pulls/{number}/files", token)
    return build_packet(repo, pr_data, files)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("number", type=int, help="Pull request number")
    parser.add_argument("--out", help="Optional Markdown output file")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    packet = fetch_pr_packet(args.repo, args.number, token)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(packet.markdown, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(packet.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
