#!/usr/bin/env python3
"""Create a GitHub pull request using a token copied to the macOS clipboard."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


TOKEN_PREFIXES = ("ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_")


def clipboard_text() -> str:
    try:
        return subprocess.check_output(["pbpaste"], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"pbpaste failed: {exc}") from exc


def env_token() -> str:
    return os.environ.get("GITHUB_TOKEN", "").strip() or os.environ.get("GH_TOKEN", "").strip()


def clear_clipboard() -> None:
    try:
        subprocess.run(["pbcopy"], input="", text=True, check=False)
    except OSError:
        pass


def github_json(method: str, url: str, token: str, payload: object | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-pr-helper",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {url} failed: {exc.code} {body}") from exc


def existing_open_pr(repo: str, head: str, token: str) -> str:
    params = urllib.parse.urlencode({"head": head, "state": "open", "per_page": "10"})
    data = github_json("GET", f"https://api.github.com/repos/{repo}/pulls?{params}", token)
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return str(first.get("html_url") or "")
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Target repo in owner/name form")
    parser.add_argument("--head", required=True, help="Head branch, e.g. owner:branch")
    parser.add_argument("--base", default="main")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--body-file")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--no-maintainer-can-modify", action="store_true")
    parser.add_argument("--token-source", choices=("clipboard", "env"), default="clipboard")
    args = parser.parse_args(argv[1:])

    token = (env_token() if args.token_source == "env" else clipboard_text()).replace("\r", "").replace("\n", "").strip()
    try:
        if not token:
            print("clipboard does not contain a GitHub token", file=sys.stderr)
            return 2
        if not token.startswith(TOKEN_PREFIXES):
            print("clipboard text does not look like a GitHub token; refusing to use it", file=sys.stderr)
            return 2

        body = args.body
        if args.body_file:
            with open(args.body_file, "r", encoding="utf-8") as handle:
                body = handle.read()

        existing = existing_open_pr(args.repo, args.head, token)
        if existing:
            print(existing)
            return 0

        payload = {
            "title": args.title,
            "head": args.head,
            "base": args.base,
            "body": body,
            "draft": bool(args.draft),
            "maintainer_can_modify": not args.no_maintainer_can_modify,
        }
        data = github_json("POST", f"https://api.github.com/repos/{args.repo}/pulls", token, payload)
        if not isinstance(data, dict):
            raise TypeError("GitHub create PR response was not an object")
        print(str(data.get("html_url") or ""))
        return 0
    finally:
        if args.token_source == "clipboard":
            clear_clipboard()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
