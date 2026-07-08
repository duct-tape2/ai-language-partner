#!/usr/bin/env python3
"""Create the public GitHub repository used for the Claude for OSS campaign.

Usage:
  GITHUB_TOKEN=... python scripts/create_github_repository.py sinmb79/ai-language-partner

The token should belong to the repository owner and have permission to create
public repositories. The script does not configure a git remote or push source;
that remains an explicit local git action so credentials are not written into
the remote URL by accident.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


DESCRIPTION = (
    "Local-first Japanese speaking practice for Korean learners using "
    "pre-authored dialogue banks and local STT/TTS, with no runtime LLM calls."
)
TOPICS = [
    "language-learning",
    "japanese",
    "korean",
    "local-first",
    "fastapi",
    "react-native",
    "expo",
    "tts",
    "stt",
    "open-source-education",
]


def github_request(method: str, url: str, token: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ai-language-partner-repo-bootstrap",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 2 or "/" not in argv[1]:
        print("usage: create_github_repository.py owner/repo", file=sys.stderr)
        return 2

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2

    owner, repo_name = argv[1].split("/", 1)
    viewer = github_request("GET", "https://api.github.com/user", token)
    viewer_login = str(viewer.get("login") or "")
    if viewer_login.lower() != owner.lower():
        print(
            f"token is authenticated as {viewer_login!r}, expected owner {owner!r}; "
            "use the owner's token or create the repo manually",
            file=sys.stderr,
        )
        return 1

    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    try:
        existing = github_request("GET", repo_url, token)
        print(f"exists: {existing.get('html_url')}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            print(exc.read().decode("utf-8"), file=sys.stderr)
            return 1
        payload = {
            "name": repo_name,
            "description": DESCRIPTION,
            "private": False,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
            "auto_init": False,
            "delete_branch_on_merge": True,
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
        }
        created = github_request("POST", "https://api.github.com/user/repos", token, payload)
        print(f"created: {created.get('html_url')}")

    github_request("PATCH", repo_url, token, {"description": DESCRIPTION, "has_issues": True, "has_wiki": False})
    github_request(
        "PUT",
        f"{repo_url}/topics",
        token,
        {"names": TOPICS},
    )
    print("configured: description, issues, wiki=false, topics")
    print("next: git remote add origin git@github.com:sinmb79/ai-language-partner.git && git push -u origin main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
