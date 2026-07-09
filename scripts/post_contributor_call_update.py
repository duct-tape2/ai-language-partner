#!/usr/bin/env python3
"""Create or update the public contributor-call discussion status comment."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

from export_claude_for_oss_evidence import collect_evidence, default_since
from post_no_install_first_pr_guides import BOARD as NO_INSTALL_BOARD_PATH
from post_no_install_first_pr_guides import parse_board as parse_no_install_board


MARKER = "<!-- ai-language-partner:contributor-call-update -->"
DEFAULT_REPO = "duct-tape2/ai-language-partner"
DEFAULT_DISCUSSION = 55
HOSTED_DEMO = "https://duct-tape2.github.io/ai-language-partner/demo/"
FIRST_ISSUE_MATCHER = "https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md"
FIVE_MINUTE_FIRST_PR = "https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md"
NO_INSTALL_BOARD = "https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md"
HELP_DESK = "https://github.com/duct-tape2/ai-language-partner/discussions/53"
CONTRIBUTOR_INTEREST = (
    "https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml"
)
DISCOVERY_STATUS = "https://github.com/duct-tape2/ai-language-partner/issues/52#issuecomment-4914054370"
FUNNEL_STATUS = "https://github.com/duct-tape2/ai-language-partner/issues/52#issuecomment-4921732560"
LOCAL_FIRST_PR = "https://github.com/alexanderop/awesome-local-first/pull/46"
UP_FOR_GRABS = "https://github.com/up-for-grabs/up-for-grabs.net/pull/5916"


def graphql(query: str, variables: dict[str, object], token: str) -> dict[str, object]:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ai-language-partner-contributor-call-update",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=2))
    return data


def no_install_task_count() -> int:
    try:
        return len(parse_no_install_board(NO_INSTALL_BOARD_PATH.read_text(encoding="utf-8")))
    except OSError:
        return 0


def render_comment(repo: str, since: str, generated_on: str, contributor_count: int, no_install_count: int) -> str:
    needed = max(0, 20 - contributor_count)
    phase = "ready" if contributor_count >= 20 else "not ready"

    return "\n".join(
        [
            MARKER,
            "# Current Contributor Call Update",
            "",
            "This is the live entry point for people arriving from discovery lists,",
            "GitHub topics, or shared links. It is not Claude for OSS evidence by",
            "itself; only useful merged PRs from real external contributors count.",
            "",
            f"- Updated: `{generated_on}`",
            f"- Evidence window starts: `{since}`",
            f"- Phase B readiness: `{phase}`",
            f"- Unique external merged PR contributors: `{contributor_count}/20`",
            f"- Remaining contributors needed: `{needed}`",
            f"- Browser-only no-install issue slots: `{no_install_count}`",
            "",
            "## Start Here",
            "",
            f"- Try the hosted mock-mode demo: {HOSTED_DEMO}",
            f"- Pick by time/skill: {FIRST_ISSUE_MATCHER}",
            f"- Fastest browser-only route: {FIVE_MINUTE_FIRST_PR}",
            f"- Full no-install board: {NO_INSTALL_BOARD}",
            f"- Ask for a suggested issue: {HELP_DESK}",
            f"- Open a contributor interest issue: {CONTRIBUTOR_INTEREST}",
            "",
            "## Discovery Channels",
            "",
            f"- Up For Grabs is merged and live: {UP_FOR_GRABS}",
            f"- Local-first discovery listing is open: {LOCAL_FIRST_PR}",
            f"- Listing tracker: {DISCOVERY_STATUS}",
            f"- Contributor funnel tracker: {FUNNEL_STATUS}",
            "",
            "## What Counts",
            "",
            "- One useful merged PR per unique external human contributor.",
            "- Docs, content review, Korean/Japanese wording, accessibility, API",
            "  examples, tests, and setup docs can all count after human review.",
            "- Maintainer-authored PRs, bots, duplicate identities, trivial typo",
            "  splits, and metric-only changes do not count.",
            "- If you want to avoid duplicate work, comment `/claim` on an issue.",
            "",
            f"Repository: https://github.com/{repo}",
        ]
    )


def discussion_and_marker_comment(
    repo: str,
    discussion_number: int,
    token: str,
) -> tuple[str, str | None, str | None]:
    owner, name = repo.split("/", 1)
    data = graphql(
        """
        query($owner: String!, $name: String!, $number: Int!) {
          repository(owner: $owner, name: $name) {
            discussion(number: $number) {
              id
              comments(first: 100) {
                nodes {
                  id
                  body
                  url
                }
              }
            }
          }
        }
        """,
        {"owner": owner, "name": name, "number": discussion_number},
        token,
    )
    repo_data = data.get("data", {}).get("repository")
    discussion = repo_data.get("discussion") if isinstance(repo_data, dict) else None
    if not isinstance(discussion, dict):
        raise RuntimeError(f"discussion #{discussion_number} was not found in {repo}")
    discussion_id = str(discussion.get("id") or "")
    comments = discussion.get("comments") if isinstance(discussion.get("comments"), dict) else {}
    for comment in comments.get("nodes", []):
        if isinstance(comment, dict) and MARKER in str(comment.get("body") or ""):
            return discussion_id, str(comment.get("id") or ""), str(comment.get("url") or "")
    return discussion_id, None, None


def upsert_discussion_comment(repo: str, discussion_number: int, body: str, token: str) -> str:
    discussion_id, comment_id, existing_url = discussion_and_marker_comment(repo, discussion_number, token)
    if comment_id:
        data = graphql(
            """
            mutation($commentId: ID!, $body: String!) {
              updateDiscussionComment(input: {commentId: $commentId, body: $body}) {
                comment {
                  url
                }
              }
            }
            """,
            {"commentId": comment_id, "body": body},
            token,
        )
        comment = data.get("data", {}).get("updateDiscussionComment", {}).get("comment", {})
        return str(comment.get("url") or existing_url or "")

    data = graphql(
        """
        mutation($discussionId: ID!, $body: String!) {
          addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
            comment {
              url
            }
          }
        }
        """,
        {"discussionId": discussion_id, "body": body},
        token,
    )
    comment = data.get("data", {}).get("addDiscussionComment", {}).get("comment", {})
    return str(comment.get("url") or "")


def build_comment(repo: str, since: str, generated_on: str, token: str | None) -> str:
    evidence = collect_evidence(repo, since, set(), token)
    return render_comment(repo, since, generated_on, len(evidence), no_install_task_count())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--discussion", type=int, default=DEFAULT_DISCUSSION)
    parser.add_argument("--since", default=default_since())
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--comment", action="store_true")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.comment and not token:
        print("GITHUB_TOKEN or GH_TOKEN is required for --comment", file=sys.stderr)
        return 2

    body = build_comment(args.repo, args.since, args.date, token)
    print(body)
    if args.comment:
        url = upsert_discussion_comment(args.repo, args.discussion, body, str(token))
        print(f"discussion comment: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
