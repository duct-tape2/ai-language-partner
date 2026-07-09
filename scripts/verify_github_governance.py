#!/usr/bin/env python3
"""Verify public GitHub governance settings used for contributor trust."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


DISCOVERY_TOPICS = {
    "beginner-friendly",
    "contributions-welcome",
    "first-contributions",
    "first-timers-only",
    "good-first-issue",
    "good-first-pr",
    "help-wanted",
    "learn-japanese",
    "up-for-grabs",
}


def github_json(path_or_url: str, token: str | None) -> object:
    url = path_or_url if path_or_url.startswith("https://") else f"https://api.github.com{path_or_url}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-governance-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def github_graphql(query: str, variables: dict[str, object], token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "ai-language-partner-governance-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def check(name: str, passed: bool, detail: str) -> bool:
    marker = "PASS" if passed else "FAIL"
    print(f"{marker}: {name} - {detail}")
    return passed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = args.repo
    passed = True

    repo_data = github_json(f"/repos/{repo}", token)
    if not isinstance(repo_data, dict):
        raise TypeError("repo response was not an object")
    passed &= check("repository is public", not bool(repo_data.get("private")), str(repo_data.get("html_url")))
    passed &= check("issues enabled", bool(repo_data.get("has_issues")), str(repo_data.get("has_issues")))
    passed &= check("discussions enabled", bool(repo_data.get("has_discussions")), str(repo_data.get("has_discussions")))
    passed &= check(
        "homepage is contributor page",
        str(repo_data.get("homepage")) == f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/",
        str(repo_data.get("homepage")),
    )

    topics = github_json(f"/repos/{repo}/topics", token)
    if not isinstance(topics, dict):
        raise TypeError("topics response was not an object")
    topic_names = set(str(name) for name in topics.get("names", []) if isinstance(name, str))
    missing_topics = sorted(DISCOVERY_TOPICS - topic_names)
    passed &= check(
        "contributor discovery topics",
        not missing_topics,
        "missing " + ", ".join(missing_topics) if missing_topics else ", ".join(sorted(DISCOVERY_TOPICS)),
    )

    pages = github_json(f"/repos/{repo}/pages", token)
    if not isinstance(pages, dict):
        raise TypeError("pages response was not an object")
    source = pages.get("source") if isinstance(pages.get("source"), dict) else {}
    build_type = str(pages.get("build_type") or "")
    passed &= check("GitHub Pages built", str(pages.get("status")) == "built", str(pages.get("html_url")))
    source_ok = build_type == "workflow" or (source.get("branch") == "main" and source.get("path") == "/docs")
    source_detail = build_type if build_type == "workflow" else str(source)
    passed &= check("GitHub Pages source", source_ok, source_detail)

    profile = github_json(f"/repos/{repo}/community/profile", token)
    if not isinstance(profile, dict):
        raise TypeError("community profile response was not an object")
    passed &= check("community profile health", int(profile.get("health_percentage") or 0) >= 100, str(profile.get("health_percentage")))

    owner, name = repo.split("/", 1)
    pinned = github_graphql(
        """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            pinnedIssues(first: 6) {
              nodes {
                issue {
                  number
                  title
                  url
                }
              }
            }
          }
        }
        """,
        {"owner": owner, "name": name},
        token,
    )
    if not isinstance(pinned, dict):
        raise TypeError("pinned issues response was not an object")
    repo_payload = pinned.get("data", {}).get("repository", {}) if isinstance(pinned.get("data"), dict) else {}
    pinned_nodes = repo_payload.get("pinnedIssues", {}).get("nodes", []) if isinstance(repo_payload, dict) else []
    pinned_issues = [node.get("issue", {}) for node in pinned_nodes if isinstance(node, dict)]
    sprint_pin = next((issue for issue in pinned_issues if isinstance(issue, dict) and issue.get("number") == 52), None)
    pinned_detail = ", ".join(f"#{issue.get('number')}: {issue.get('title')}" for issue in pinned_issues if isinstance(issue, dict))
    passed &= check("20 contributor sprint kickoff pinned", sprint_pin is not None, pinned_detail or "no pinned issues")

    try:
        protection = github_json(f"/repos/{repo}/branches/main/protection", token)
    except urllib.error.HTTPError as exc:
        passed &= check("main branch protection", False, exc.read().decode("utf-8"))
    else:
        if not isinstance(protection, dict):
            raise TypeError("branch protection response was not an object")
        force_push = protection.get("allow_force_pushes") if isinstance(protection.get("allow_force_pushes"), dict) else {}
        deletions = protection.get("allow_deletions") if isinstance(protection.get("allow_deletions"), dict) else {}
        reviews = (
            protection.get("required_pull_request_reviews")
            if isinstance(protection.get("required_pull_request_reviews"), dict)
            else {}
        )
        conversations = (
            protection.get("required_conversation_resolution")
            if isinstance(protection.get("required_conversation_resolution"), dict)
            else {}
        )
        passed &= check("main branch protection", True, str(protection.get("url")))
        passed &= check("pull request review required", int(reviews.get("required_approving_review_count") or 0) >= 1, str(reviews))
        passed &= check("force pushes disabled", not bool(force_push.get("enabled")), str(force_push))
        passed &= check("branch deletions disabled", not bool(deletions.get("enabled")), str(deletions))
        passed &= check("conversation resolution required", bool(conversations.get("enabled")), str(conversations))

    if not passed:
        print("\nResult: GitHub governance needs attention.")
        return 1
    print("\nResult: GitHub governance checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
