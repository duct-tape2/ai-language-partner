#!/usr/bin/env python3
"""Render a contributor-friendly starter issue index from GitHub issues."""

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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "community" / "STARTER_ISSUE_INDEX.md"

LANES = [
    ("Mobile/accessibility", "Expo, React Native, labels, touch targets, layout"),
    ("Backend/API docs", "FastAPI, OpenAPI, local STT/TTS setup, provider docs"),
    ("Tests/tooling", "Python, TypeScript, CI, repo checks, fixtures"),
    ("Dialogue/content review", "Japanese naturalness, Korean learner notes, JLPT review"),
    ("Release/community", "Issue taxonomy, review process, roadmap, sprint coordination"),
    ("Korean/Japanese docs", "Setup docs, architecture notes, learner-facing explanation"),
    ("Other", "Useful starter tasks that do not fit another lane"),
]


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    url: str
    labels: tuple[str, ...]


def github_json(url: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-starter-issue-index",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_open_issues(repo: str, token: str | None) -> list[Issue]:
    issues: list[Issue] = []
    for page in range(1, 11):
        params = urllib.parse.urlencode({"state": "open", "per_page": "100", "page": str(page)})
        data = github_json(f"https://api.github.com/repos/{repo}/issues?{params}", token)
        if not isinstance(data, list):
            raise TypeError("GitHub issues response was not a list")
        for item in data:
            if not isinstance(item, dict) or "pull_request" in item:
                continue
            labels = item.get("labels") if isinstance(item.get("labels"), list) else []
            issues.append(
                Issue(
                    number=int(item.get("number", 0)),
                    title=str(item.get("title", "")),
                    url=str(item.get("html_url", "")),
                    labels=tuple(str(label.get("name", "")) for label in labels if isinstance(label, dict)),
                )
            )
        if len(data) < 100:
            break
    return sorted(issues, key=lambda issue: issue.number)


def load_issues_from_file(path: Path) -> list[Issue]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise TypeError("fixture must be a list of issue objects")
    issues = []
    for item in data:
        if not isinstance(item, dict):
            continue
        issues.append(
            Issue(
                number=int(item["number"]),
                title=str(item["title"]),
                url=str(item["url"]),
                labels=tuple(str(label) for label in item.get("labels", [])),
            )
        )
    return sorted(issues, key=lambda issue: issue.number)


def lane_for(issue: Issue) -> str:
    labels = {label.lower() for label in issue.labels}
    title = issue.title.lower()
    if "mobile" in labels or "accessibility" in labels:
        return "Mobile/accessibility"
    if labels & {"backend", "stt", "tts", "security"}:
        return "Backend/API docs"
    if "tests" in labels:
        return "Tests/tooling"
    if labels & {"content", "language-review"}:
        return "Dialogue/content review"
    if labels & {"community", "release"}:
        return "Release/community"
    if "docs" in labels or title.startswith("docs:"):
        return "Korean/Japanese docs"
    return "Other"


def badge_labels(issue: Issue) -> str:
    if not issue.labels:
        return ""
    return ", ".join(f"`{label}`" for label in issue.labels)


def render_markdown(repo: str, issues: list[Issue], generated_on: str) -> str:
    grouped: dict[str, list[Issue]] = {lane: [] for lane, _ in LANES}
    for issue in issues:
        grouped.setdefault(lane_for(issue), []).append(issue)

    good_first = sum(1 for issue in issues if "good first issue" in {label.lower() for label in issue.labels})
    help_wanted = sum(1 for issue in issues if "help wanted" in {label.lower() for label in issue.labels})
    lines = [
        "# Starter Issue Index",
        "",
        "This is a snapshot of open issues that are useful for first-time",
        "contributors. Pick one focused issue, comment if you want to claim it,",
        "then follow the first PR walkthrough.",
        "",
        f"- Repository: `https://github.com/{repo}`",
        f"- Generated on: `{generated_on}`",
        f"- Open issues indexed: `{len(issues)}`",
        f"- Good first issues: `{good_first}`",
        f"- Help wanted issues: `{help_wanted}`",
        "- First PR walkthrough: [docs/community/FIRST_PR_WALKTHROUGH.md](FIRST_PR_WALKTHROUGH.md)",
        "- Contributor interest form: "
        f"`https://github.com/{repo}/issues/new?template=contributor_interest.yml`",
        "",
        "Only useful, reviewable PRs count toward the Claude for OSS",
        "community-builder evidence. Do not split trivial changes just to create",
        "more PRs.",
        "",
        "## Lane Summary",
        "",
        "| Lane | Open issues | Best for |",
        "|---|---:|---|",
    ]
    for lane, description in LANES:
        count = len(grouped.get(lane, []))
        if count:
            lines.append(f"| {lane} | {count} | {description} |")

    for lane, description in LANES:
        lane_issues = grouped.get(lane, [])
        if not lane_issues:
            continue
        lines.extend(["", f"## {lane}", "", description + ".", "", "| Issue | Labels |", "|---|---|"])
        for issue in lane_issues:
            title = issue.title.replace("|", "\\|")
            lines.append(f"| [#{issue.number}: {title}]({issue.url}) | {badge_labels(issue)} |")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Markdown file to write")
    parser.add_argument("--from-file", help="Read issue fixture JSON instead of GitHub")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Generated date")
    args = parser.parse_args(argv[1:])

    if args.from_file:
        issues = load_issues_from_file(Path(args.from_file))
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        issues = fetch_open_issues(args.repo, token)

    markdown = render_markdown(args.repo, issues, args.date)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"wrote {out_path} with {len(issues)} issue(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
