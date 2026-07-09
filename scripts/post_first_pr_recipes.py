#!/usr/bin/env python3
"""Render and optionally upsert first-PR recipe comments for starter issues."""

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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "community" / "FIRST_PR_RECIPES.md"
MARKER = "<!-- ai-language-partner:first-pr-recipe -->"


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    url: str
    body: str
    labels: tuple[str, ...]


def github_json(url: str, token: str | None, method: str = "GET", payload: dict[str, object] | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-first-pr-recipes",
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
        return json.loads(response.read().decode("utf-8"))


def fetch_issues(repo: str, token: str | None, label: str) -> list[Issue]:
    issues: list[Issue] = []
    encoded_label = urllib.parse.quote(label)
    for page in range(1, 11):
        url = f"https://api.github.com/repos/{repo}/issues?state=open&labels={encoded_label}&per_page=100&page={page}"
        data = github_json(url, token)
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
                    body=str(item.get("body") or ""),
                    labels=tuple(str(label.get("name", "")) for label in labels if isinstance(label, dict)),
                )
            )
    return sorted(issues, key=lambda issue: issue.number)


def existing_recipe_comment(repo: str, number: int, token: str | None) -> dict[str, object] | None:
    for page in range(1, 6):
        url = f"https://api.github.com/repos/{repo}/issues/{number}/comments?per_page=100&page={page}"
        comments = github_json(url, token)
        if not isinstance(comments, list):
            raise TypeError("GitHub comments response was not a list")
        for comment in comments:
            if isinstance(comment, dict) and MARKER in str(comment.get("body") or ""):
                return comment
        if len(comments) < 100:
            break
    return None


def upsert_recipe(repo: str, number: int, token: str, body: str) -> tuple[str, str]:
    existing = existing_recipe_comment(repo, number, token)
    if existing:
        result = github_json(str(existing["url"]), token, method="PATCH", payload={"body": body})
        if not isinstance(result, dict):
            raise TypeError("GitHub comment response was not an object")
        return "updated", str(result.get("html_url") or "")
    url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    result = github_json(url, token, method="POST", payload={"body": body})
    if not isinstance(result, dict):
        raise TypeError("GitHub comment response was not an object")
    return "posted", str(result.get("html_url") or "")


def likely_files(issue: Issue) -> list[str]:
    title = issue.title.lower()
    labels = {label.lower() for label in issue.labels}
    files: list[str] = []

    if "backend mock" in title:
        files += ["docs/ko/index.md", "apps/api/README.md", "README.md"]
    elif "mobile mock" in title:
        files += ["docs/ja/index.md", "apps/mobile/README.md", "README.md"]
    elif "mock mode indicators" in title:
        files += ["docs/ARCHITECTURE.md", "docs/ja/index.md", "docs/ko/index.md"]
    elif "glossary" in title:
        files += ["docs/ARCHITECTURE.md", "README.md"]
    elif "cultural note review checklist" in title:
        files += ["docs/community/CONTRIBUTOR_LANDING.md", "apps/mobile/src/culture/cultureNotes.ts"]
    elif "yui" in title:
        files += ["packs/yui/v1/story.json", "packs/yui/v1/variants.csv"]
    elif "no-runtime-llm design" in title:
        files += ["docs/ja/index.md", "docs/index.md", "docs/ARCHITECTURE.md"]
    elif "restaurant" in title:
        files += ["packs/yui/v1/story.json", "packs/haruka/v1/story.json", "authoring/scenarios/"]
    elif "particle" in title:
        files += ["docs/ko/index.md", "apps/mobile/src/grammar/grammarData.ts", "apps/mobile/src/mistakes/mistakesData.ts"]
    elif "bottom tabs" in title:
        files += ["apps/mobile/App.tsx", "apps/mobile/src/theme.ts"]
    elif "daily talk" in title:
        files += ["apps/mobile/src/screens/DailyTalkScreen.tsx", "apps/mobile/src/dialogue/packManager.ts"]
    elif "korean ui" in title:
        files += ["apps/mobile/src/i18n.ts", "apps/mobile/src/text.ts", "apps/mobile/src/screens/"]
    elif "provider-status" in title or "provider status" in title:
        files += ["apps/api/README.md", "docs/backend/API_RUNBOOK.md", "contracts/openapi_v0.yaml"]
    elif "dialogue pack listing" in title:
        files += ["contracts/openapi_v0.yaml", "contracts/README_API_CONTRACT.md", "apps/api/tests/test_api_contract.py"]
    elif "path traversal" in title:
        files += ["apps/api/tests/test_api_contract.py", "apps/api/app/main.py"]
    elif "forbidden-file scan" in title:
        files += ["scripts/check_public_tree.py", "scripts/test_claude_for_oss_evidence.py"]
    elif "issue-label taxonomy" in title:
        files += ["docs/community/LABELS.md", "docs/community/ISSUE_SEEDS.md"]
    elif "first pr walkthrough" in title:
        files += ["docs/community/FIRST_PR_WALKTHROUGH.md", "docs/ko/index.md", "docs/ja/index.md"]
    elif "why no runtime llm" in title:
        files += ["README.md", "docs/ARCHITECTURE.md", "docs/index.md"]
    elif "maintainer review checklist" in title:
        files += ["docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md"]
    elif "cultural-safety review examples" in title:
        files += ["apps/mobile/src/culture/cultureNotes.ts", "docs/community/CONTRIBUTOR_LANDING.md"]
    elif "dialogue-bank packs" in title:
        files += ["docs/community/CONTRIBUTOR_GROWTH_PLAN.md", "docs/community/CONTRIBUTOR_SPRINT.md"]

    if not files:
        if "mobile" in labels or "accessibility" in labels:
            files += ["apps/mobile/App.tsx", "apps/mobile/src/screens/", "apps/mobile/src/components.tsx"]
        elif "backend" in labels:
            files += ["apps/api/README.md", "contracts/openapi_v0.yaml", "apps/api/tests/test_api_contract.py"]
        elif "content" in labels or "language-review" in labels:
            files += ["packs/yui/v1/story.json", "packs/haruka/v1/story.json", "packs/ren/v1/story.json"]
        elif "docs" in labels:
            files += ["README.md", "docs/index.md", "docs/community/"]
        elif "tests" in labels:
            files += ["scripts/", "apps/api/tests/test_api_contract.py"]

    seen: set[str] = set()
    unique = []
    for path in files:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique[:5]


def suggested_checks(issue: Issue, files: list[str]) -> list[str]:
    checks = ["python3 scripts/check_public_tree.py"]
    labels = {label.lower() for label in issue.labels}
    if "backend" in labels or any(path.startswith("apps/api/") or path.startswith("contracts/") for path in files):
        checks.append("cd apps/api && python -m pytest")
    if "mobile" in labels or any(path.startswith("apps/mobile/") for path in files):
        checks.append("cd apps/mobile && npm run verify")
    if "tests" in labels or any(path.startswith("scripts/") for path in files):
        checks.append("python3 -m unittest discover -s scripts -p 'test_*.py'")
    if "content" in labels or "language-review" in labels:
        checks.append("manual language/content review: explain what wording you checked")
    if len(checks) == 1:
        checks.append("manual docs review: verify links and wording")
    return checks


def acceptance(issue: Issue) -> str:
    body = issue.body.strip()
    if body:
        body = re.sub(r"\s+", " ", body)
        return body[:350]
    return "Make one focused, reviewable change that satisfies the issue title."


def render_recipe(repo: str, issue: Issue) -> str:
    owner, name = repo.split("/", 1)
    files = likely_files(issue)
    checks = suggested_checks(issue, files)
    file_lines = "\n".join(f"- `{path}`" for path in files) or "- Ask in the issue for a suggested file."
    check_lines = "\n".join(f"- `{check}`" for check in checks)
    return f"""{MARKER}
### First PR recipe

Thanks for considering this issue. A small useful PR is enough; please keep the
change focused and avoid generated/private assets.

**Likely files to inspect**

{file_lines}

**Acceptance signal**

{acceptance(issue)}

**Suggested checks**

{check_lines}

**PR body checklist**

- Link this issue: `Closes #{issue.number}` or `Refs #{issue.number}`
- Explain what changed and why it helps learners or contributors
- Say which check you ran, or say that it was docs/content review only
- Do not commit generated audio, archives, local engines, SQLite files, secrets,
  screenshots, or private notes

Useful links:

- Contributor page: https://{owner}.github.io/{name}/
- First issue matcher: https://github.com/{repo}/blob/main/docs/community/FIRST_ISSUE_MATCHER.md
- Language review first PR kit: https://github.com/{repo}/blob/main/docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md
- First PR walkthrough: https://github.com/{repo}/blob/main/docs/community/FIRST_PR_WALKTHROUGH.md
- Counting policy: https://github.com/{repo}/blob/main/docs/community/PR_REVIEW_AND_COUNTING_POLICY.md
"""


def render_markdown(repo: str, issues: list[Issue], generated_on: str) -> str:
    lines = [
        "# First PR Recipes",
        "",
        "These recipes are generated from open `good first issue` items. They are",
        "also posted as issue comments so first-time contributors can start without",
        "searching the whole repository.",
        "",
        f"- Repository: `https://github.com/{repo}`",
        f"- Generated on: `{generated_on}`",
        f"- Issues covered: `{len(issues)}`",
        "",
    ]
    for issue in issues:
        lines.extend([f"## [#{issue.number}: {issue.title}]({issue.url})", "", render_recipe(repo, issue), ""])
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--label", default="good first issue", help="Issue label to render")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Markdown file to write")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Generated date")
    parser.add_argument("--apply", action="store_true", help="Post missing recipe comments to GitHub issues")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    issues = fetch_issues(args.repo, token, args.label)
    markdown = render_markdown(args.repo, issues, args.date)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(f"wrote {out} with {len(issues)} issue recipe(s)")

    if args.apply:
        if not token:
            print("--apply requires GITHUB_TOKEN or GH_TOKEN", file=sys.stderr)
            return 2
        posted = 0
        updated = 0
        for issue in issues:
            action, url = upsert_recipe(args.repo, issue.number, token, render_recipe(args.repo, issue))
            if action == "posted":
                posted += 1
            else:
                updated += 1
            print(f"{action} #{issue.number}: {url}")
        print(f"posted={posted} updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
