#!/usr/bin/env python3
"""Verify whether this repo is ready for a Claude for OSS application.

Usage:
  GITHUB_TOKEN=... python scripts/verify_claude_for_oss_readiness.py duct-tape2/ai-language-partner

This script is intentionally strict: failing means "do not apply yet" unless
using the Phase A exception text that explicitly says the numeric criterion has
not been met.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from export_claude_for_oss_evidence import collect_evidence, default_since


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/contributor_interest.yml",
    ".github/workflows/repo-hygiene.yml",
    ".github/workflows/mobile-verify.yml",
    ".github/workflows/api-docker-smoke.yml",
    ".github/workflows/claude-oss-monitor.yml",
    ".github/workflows/contributor-sprint-kickoff.yml",
    ".github/workflows/issue-welcome.yml",
    ".github/workflows/pr-welcome.yml",
    "docs/CLAUDE_FOR_OSS_APPLICATION.md",
    "docs/community/ISSUE_SEEDS.md",
    "docs/community/CONTRIBUTOR_LANDING.md",
    "docs/community/CONTRIBUTOR_SPRINT.md",
    "docs/community/OUTREACH_QUEUE.json",
    "docs/community/PUBLISHING_AND_APPLICATION_CHECKLIST.md",
    "scripts/snapshot_claude_for_oss_status.py",
    "scripts/create_contributor_sprint_kickoff_issue.py",
    "scripts/verify_outreach_queue.py",
]


def run_local(command: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def github_json(path_or_url: str, token: str | None) -> dict[str, object]:
    url = path_or_url if path_or_url.startswith("https://") else f"https://api.github.com{path_or_url}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-claude-for-oss-readiness",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def github_search_count(query: str, token: str | None) -> int:
    params = urllib.parse.urlencode({"q": query, "per_page": "1"})
    data = github_json(f"/search/issues?{params}", token)
    return int(data.get("total_count", 0))


def github_issue_count(repo: str, token: str | None) -> int:
    total = 0
    for page in range(1, 11):
        params = urllib.parse.urlencode({"state": "all", "per_page": "100", "page": str(page)})
        issues = github_json(f"/repos/{repo}/issues?{params}", token)
        if not isinstance(issues, list):
            break
        issue_count = sum(1 for issue in issues if isinstance(issue, dict) and "pull_request" not in issue)
        total += issue_count
        if len(issues) < 100:
            break
    return total


def check(name: str, passed: bool, detail: str) -> bool:
    marker = "PASS" if passed else "FAIL"
    print(f"{marker}: {name} - {detail}")
    return passed


def main(argv: list[str]) -> int:
    if len(argv) != 2 or "/" not in argv[1]:
        print("usage: verify_claude_for_oss_readiness.py owner/repo", file=sys.stderr)
        return 2
    repo = argv[1]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    passed = True

    ok, output = run_local(["python3", "scripts/check_public_tree.py"])
    passed &= check("local public tree hygiene", ok, output or "ok")

    outreach_ok, outreach_output = run_local(["python3", "scripts/verify_outreach_queue.py"])
    passed &= check("outreach queue", outreach_ok, outreach_output or "ok")

    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    passed &= check("required public files", not missing, ", ".join(missing) if missing else "all present")

    status_ok, status_output = run_local(["git", "status", "--short"])
    passed &= check("clean git worktree", status_ok and not status_output, status_output or "clean")

    try:
        repo_data = github_json(f"/repos/{repo}", token)
        repo_public = not bool(repo_data.get("private"))
        default_branch = str(repo_data.get("default_branch") or "")
        pushed = bool(repo_data.get("pushed_at"))
        passed &= check("GitHub repo exists and is public", repo_public, str(repo_data.get("html_url")))
        passed &= check("GitHub default branch", default_branch == "main", default_branch or "missing")
        passed &= check("GitHub repo has pushed source", pushed, str(repo_data.get("pushed_at") or "missing"))
    except urllib.error.HTTPError as exc:
        passed &= check("GitHub repo exists and is public", False, exc.read().decode("utf-8"))

    try:
        issues = github_issue_count(repo, token)
        merged_prs = github_search_count(f"repo:{repo} is:pr is:merged", token)
        passed &= check("starter issues exist", issues >= 30, f"{issues} issue(s)")
        passed &= check("merged PRs exist", merged_prs >= 20, f"{merged_prs} merged PR(s)")
    except urllib.error.HTTPError as exc:
        passed &= check("GitHub issue/PR search", False, exc.read().decode("utf-8"))

    since = default_since()
    try:
        evidence = collect_evidence(repo, since, set(), token)
        passed &= check(
            "20 unique external merged PR contributors",
            len(evidence) >= 20,
            f"{len(evidence)} counted since {since}",
        )
    except urllib.error.HTTPError as exc:
        passed &= check("20 unique external merged PR contributors", False, exc.read().decode("utf-8"))

    if not passed:
        print("\nResult: not ready for Phase B Claude for OSS application.")
        return 1
    print("\nResult: ready for Phase B Claude for OSS application.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
