#!/usr/bin/env python3
"""Write a non-failing Claude for OSS status snapshot.

This is for monitoring and GitHub Actions summaries. It reports the current
community-builder evidence without treating "not ready yet" as a CI failure.
Use verify_claude_for_oss_readiness.py for the strict pre-application gate.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from export_claude_for_oss_evidence import collect_evidence, default_since, markdown_table


def github_json(path_or_url: str, token: str | None) -> object:
    url = path_or_url if path_or_url.startswith("https://") else f"https://api.github.com{path_or_url}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-claude-for-oss-status",
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
    if not isinstance(data, dict):
        raise TypeError("GitHub search response was not an object")
    return int(data.get("total_count", 0))


def github_issue_count(repo: str, token: str | None) -> int:
    total = 0
    for page in range(1, 11):
        params = urllib.parse.urlencode({"state": "all", "per_page": "100", "page": str(page)})
        data = github_json(f"/repos/{repo}/issues?{params}", token)
        if not isinstance(data, list):
            raise TypeError("GitHub issues response was not a list")
        total += sum(1 for item in data if isinstance(item, dict) and "pull_request" not in item)
        if len(data) < 100:
            break
    return total


def write_snapshot(repo: str, since: str, out_dir: Path, token: str | None) -> dict[str, object]:
    evidence = collect_evidence(repo, since, set(), token)
    count = len(evidence)
    needed = max(0, 20 - count)
    merged_pr_count = github_search_count(f"repo:{repo} is:pr is:merged", token)
    issue_count = github_issue_count(repo, token)
    repo_data = github_json(f"/repos/{repo}", token)
    if not isinstance(repo_data, dict):
        raise TypeError("GitHub repo response was not an object")

    status = {
        "repo": repo,
        "repo_url": f"https://github.com/{repo}",
        "since": since,
        "phase_b_ready": count >= 20,
        "unique_external_contributors": count,
        "remaining_external_contributors_needed": needed,
        "merged_pr_count": merged_pr_count,
        "starter_issue_count": issue_count,
        "default_branch": repo_data.get("default_branch"),
        "pushed_at": repo_data.get("pushed_at"),
        "evidence_search_url": "https://github.com/" + repo + "/pulls?q=" + urllib.parse.quote(
            f"is:pr is:merged merged:>={since}",
            safe=":",
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "claude_for_oss_status.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        f"# Claude for OSS Status: `{repo}`",
        "",
        f"- Since: `{since}`",
        f"- Phase B ready: `{'yes' if status['phase_b_ready'] else 'no'}`",
        f"- Unique external merged PR contributors: `{count}`",
        f"- Remaining contributors needed: `{needed}`",
        f"- Total merged PRs: `{merged_pr_count}`",
        f"- Starter issues: `{issue_count}`",
        f"- Evidence search: {status['evidence_search_url']}",
        "",
        "## Counted External Contributor PRs",
        "",
        markdown_table(evidence, 20),
    ]
    if needed:
        lines.extend(
            [
                "",
                "Phase B is not ready yet. Continue the 20-contributor sprint and",
                "do not claim the community-builder threshold until this count reaches 20.",
            ]
        )
    markdown = "\n".join(lines) + "\n"
    (out_dir / "claude_for_oss_status.md").write_text(markdown, encoding="utf-8")
    return status


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--since", default=default_since(), help="Earliest merged date, YYYY-MM-DD")
    parser.add_argument("--out-dir", default=".claude-for-oss", help="Output directory")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    status = write_snapshot(args.repo, args.since, Path(args.out_dir), token)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
