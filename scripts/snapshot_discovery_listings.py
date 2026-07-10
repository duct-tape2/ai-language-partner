#!/usr/bin/env python3
"""Snapshot external contributor discovery channels.

The output is operational evidence, not Claude for OSS contributor evidence.
Only useful merged PRs from unique external contributors count toward the
community-builder threshold.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from export_claude_for_oss_evidence import collect_evidence, default_since


MARKER = "<!-- discovery-listings-status -->"
DEFAULT_REPO = "duct-tape2/ai-language-partner"
DEFAULT_ISSUE = 52
DEMO_RELEASE_TAG = "demo-web-2026-07-09"
DEMO_RELEASE_ASSET = "ai-language-partner-web-demo-2026-07-09.zip"
HOSTED_DEMO_URL = "https://duct-tape2.github.io/ai-language-partner/demo/"
COMMUNITY_PAGES = "https://duct-tape2.github.io/ai-language-partner/community"
CONTRIBUTOR_LANDING_URL = f"{COMMUNITY_PAGES}/CONTRIBUTOR_LANDING.html"
DIRECTORY_FIRST_PR_URL = f"{COMMUNITY_PAGES}/DIRECTORY_FIRST_PR.html"
FIRST_ISSUE_MATCHER_URL = f"{COMMUNITY_PAGES}/FIRST_ISSUE_MATCHER.html"
FIVE_MINUTE_FIRST_PR_URL = f"{COMMUNITY_PAGES}/FIVE_MINUTE_FIRST_PR.html"
INSTALLABLE_DEMO_PLAN_URL = f"{COMMUNITY_PAGES}/INSTALLABLE_DEMO_RELEASE_PLAN.html"
GOOD_FIRST_ISSUE_PROJECT_URL = "https://github.com/DeepSourceCorp/good-first-issue"
GOOD_FIRST_ISSUE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdVUqZHnl6W1S_5mA7SJtEb-lbiXf6tF1uKk5wMFu3HfM9HDQ/viewform"
GOOD_FIRST_ISSUE_ORG_GUIDE_URL = "https://www.goodfirstissue.org/for-maintainers"
GOOD_FIRST_ISSUE_ORG_REQUEST_URL = "https://github.com/orgs/goodfirstissueorg/discussions/1"
FOR_GOOD_FIRST_ISSUE_URL = "https://github.com/github/forgoodfirstissue"
TWENTY_FOUR_PULL_REQUESTS_URL = "https://24pullrequests.com/projects?page=9"
TWENTY_FOUR_PULL_REQUESTS_MANAGE_URL = "https://24pullrequests.com/my_suggestions"
HELP_WANTED_PROJECT_URL = "https://helpwanted.dev/projects/duct-tape2/ai-language-partner"


@dataclass(frozen=True)
class ListingPr:
    name: str
    repo: str
    number: int
    contributor_link: str
    followup_url: str = ""


@dataclass(frozen=True)
class ListingIssue:
    name: str
    repo: str
    number: int
    contributor_link: str
    open_next_step: str = "awaiting maintainer acknowledgement"
    check_note: str = "issue submitted before PR per contribution guidelines"


LISTING_PRS = [
    ListingPr(
        name="First Contributions Project Discovery",
        repo="firstcontributions/firstcontributions.github.io",
        number=721,
        contributor_link="https://github.com/duct-tape2/ai-language-partner/contribute",
        followup_url="https://github.com/firstcontributions/firstcontributions.github.io/issues/1#issuecomment-4931220251",
    ),
    ListingPr(
        name="For Good First Issue",
        repo="github/forgoodfirstissue",
        number=494,
        contributor_link=DIRECTORY_FIRST_PR_URL,
    ),
    ListingPr(
        name="Up For Grabs",
        repo="up-for-grabs/up-for-grabs.net",
        number=5916,
        contributor_link="https://github.com/duct-tape2/ai-language-partner/labels/up-for-grabs",
    ),
    ListingPr(
        name="Awesome for Beginners",
        repo="MunGell/awesome-for-beginners",
        number=2072,
        contributor_link="https://github.com/duct-tape2/ai-language-partner/labels/first-timers-only",
        followup_url="https://github.com/MunGell/awesome-for-beginners/pull/2072#issuecomment-4921750431",
    ),
    ListingPr(
        name="Awesome for Non-Programmers",
        repo="szabgab/awesome-for-non-programmers",
        number=107,
        contributor_link=CONTRIBUTOR_LANDING_URL,
        followup_url="https://github.com/szabgab/awesome-for-non-programmers/pull/107#issuecomment-4921750475",
    ),
    ListingPr(
        name="Awesome Language Learning",
        repo="Vuizur/awesome-language-learning",
        number=31,
        contributor_link=FIVE_MINUTE_FIRST_PR_URL,
        followup_url="https://github.com/Vuizur/awesome-language-learning/pull/31#issuecomment-4921750535",
    ),
    ListingPr(
        name="Awesome Japanese Learning Resources",
        repo="ailanguagetutor/awesome-japanese-learning-resources",
        number=5,
        contributor_link=FIRST_ISSUE_MATCHER_URL,
    ),
    ListingPr(
        name="Awesome Japanese Study Materials",
        repo="naghim/Awesome-Japanese-Study-Materials",
        number=8,
        contributor_link=FIRST_ISSUE_MATCHER_URL,
    ),
    ListingPr(
        name="Awesome Japanese Resources",
        repo="Sara-Lib/Awesome-Japanese-resources",
        number=1,
        contributor_link=CONTRIBUTOR_LANDING_URL,
    ),
    ListingPr(
        name="Awesome Local-First",
        repo="alexanderop/awesome-local-first",
        number=46,
        contributor_link=FIRST_ISSUE_MATCHER_URL,
    ),
    ListingPr(
        name="Awesome Language Learning Japanese Page",
        repo="jqhoogland/awesome-language-learning",
        number=20,
        contributor_link=FIRST_ISSUE_MATCHER_URL,
    ),
    ListingPr(
        name="Awesome Open Source School",
        repo="zefanja/awesome-opensource-school",
        number=16,
        contributor_link="https://duct-tape2.github.io/ai-language-partner/demo/",
    ),
]


LISTING_ISSUES = [
    ListingIssue(
        name="Meaningful Code",
        repo="Meaningful-Code/meaningfulcode-frontend",
        number=147,
        contributor_link=CONTRIBUTOR_LANDING_URL,
        open_next_step="awaiting impactful-project review",
        check_note="official project-submission issue template used; education criteria documented",
    ),
    ListingIssue(
        name="Awesome Japanese",
        repo="yudataguy/Awesome-Japanese",
        number=149,
        contributor_link=FIVE_MINUTE_FIRST_PR_URL,
    ),
]


def github_json(url: str, token: str | None, method: str = "GET", payload: object | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-discovery-listings",
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


def count_open_issues(repo: str, label: str, token: str | None) -> int:
    encoded = urllib.parse.quote(label)
    total = 0
    for page in range(1, 11):
        url = f"https://api.github.com/repos/{repo}/issues?state=open&labels={encoded}&per_page=100&page={page}"
        data = github_json(url, token)
        if not isinstance(data, list):
            raise TypeError("GitHub issues response was not a list")
        total += sum(1 for issue in data if isinstance(issue, dict) and "pull_request" not in issue)
        if len(data) < 100:
            break
    return total


def fetch_listing_pr(pr: ListingPr, token: str | None) -> dict[str, object]:
    data = github_json(f"https://api.github.com/repos/{pr.repo}/pulls/{pr.number}", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub pull request response was not an object")
    checks: list[str] = []
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    sha = str(head.get("sha", ""))
    if sha:
        check_data = github_json(f"https://api.github.com/repos/{pr.repo}/commits/{sha}/check-runs?per_page=50", token)
        if isinstance(check_data, dict):
            for run in check_data.get("check_runs", []):
                if isinstance(run, dict):
                    checks.append(f"{run.get('name')}: {run.get('status')} {run.get('conclusion')}")
    return {
        "name": pr.name,
        "url": str(data.get("html_url", "")),
        "kind": "PR",
        "state": str(data.get("state", "")),
        "merged": bool(data.get("merged", False)),
        "mergeable": data.get("mergeable"),
        "draft": bool(data.get("draft", False)),
        "checks": checks,
        "contributor_link": pr.contributor_link,
        "followup_url": pr.followup_url,
    }


def fetch_listing_issue(issue: ListingIssue, token: str | None) -> dict[str, object]:
    data = github_json(f"https://api.github.com/repos/{issue.repo}/issues/{issue.number}", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub issue response was not an object")
    state = str(data.get("state", ""))
    reason = str(data.get("state_reason") or "")
    if state == "open":
        next_step = issue.open_next_step
    else:
        reason_label = f" ({reason})" if reason else ""
        next_step = f"closed{reason_label}; follow up only after maturity changes"
    return {
        "name": issue.name,
        "url": str(data.get("html_url", "")),
        "kind": "Issue",
        "state": state,
        "merged": "n/a",
        "mergeable": next_step,
        "draft": False,
        "checks": [issue.check_note],
        "contributor_link": issue.contributor_link,
        "followup_url": "",
    }


def fetch_demo_release(repo: str, token: str | None) -> dict[str, str]:
    try:
        data = github_json(f"https://api.github.com/repos/{repo}/releases/tags/{DEMO_RELEASE_TAG}", token)
    except Exception:
        return {"url": "", "asset": "", "status": "missing"}
    if not isinstance(data, dict):
        return {"url": "", "asset": "", "status": "missing"}
    asset_url = ""
    for asset in data.get("assets", []):
        if isinstance(asset, dict) and asset.get("name") == DEMO_RELEASE_ASSET:
            asset_url = str(asset.get("browser_download_url") or "")
            break
    status = "active" if asset_url else "release found, asset missing"
    return {"url": str(data.get("html_url") or ""), "asset": asset_url, "status": status}


def fetch_repo_topics(repo: str, token: str | None) -> list[str]:
    data = github_json(f"https://api.github.com/repos/{repo}/topics", token)
    if not isinstance(data, dict):
        raise TypeError("GitHub topics response was not an object")
    return sorted(name for name in data.get("names", []) if isinstance(name, str))


def directory_rows(repo: str, token: str | None) -> list[str]:
    contributors = len(collect_evidence(repo, default_since(), set(), token))
    codetriage_repo_url = f"https://www.codetriage.com/{repo}"
    state = "eligible" if contributors >= 10 else "locked"
    next_step = (
        "submit repository form"
        if contributors >= 10
        else f"requires 10 contributors; current {contributors}/10"
    )
    return [
        "| Good First Issue | Directory | {state} | n/a | {next_step} | [link]({project}) | "
        f"[entry]({FIRST_ISSUE_MATCHER_URL}) | "
        "[form]({form}) | README criteria |".format(
            state=state,
            next_step=next_step,
            project=GOOD_FIRST_ISSUE_PROJECT_URL,
            form=GOOD_FIRST_ISSUE_FORM_URL,
        ),
        "| CodeTriage | Directory | active | n/a | invite contributors to subscribe for issue triage | "
        f"[link]({codetriage_repo_url}) | [entry](https://github.com/{repo}/contribute) | "
        f"[subscribe]({codetriage_repo_url}) | public profile and issue sync active |",
        "| Good First Issue.org | Directory request | awaiting response | n/a | "
        "GitHub OAuth authorization is disabled; public Q&A submitted | "
        f"[link]({GOOD_FIRST_ISSUE_ORG_GUIDE_URL}) | "
        f"[entry](https://github.com/{repo}/contribute) | "
        f"[request]({GOOD_FIRST_ISSUE_ORG_REQUEST_URL}) | "
        "public request submitted 2026-07-10 |",
        "| 24 Pull Requests | Directory | active | n/a | public project #3564 | "
        f"[link]({TWENTY_FOUR_PULL_REQUESTS_URL}) | "
        f"[entry](https://github.com/{repo}/contribute) | "
        f"[manage]({TWENTY_FOUR_PULL_REQUESTS_MANAGE_URL}) | "
        "TypeScript; tests; good first issue; contribulator score 39 |",
        "| Help Wanted | Directory | active | n/a | 37 indexed help-wanted issues | "
        f"[link]({HELP_WANTED_PROJECT_URL}) | "
        f"[entry](https://github.com/{repo}/contribute) | "
        f"[browse]({HELP_WANTED_PROJECT_URL}) | "
        "public project page and sitemap confirmed 2026-07-10 |",
    ]


def build_markdown(repo: str, token: str | None) -> str:
    up_for_grabs = count_open_issues(repo, "up-for-grabs", token)
    first_timers = count_open_issues(repo, "first-timers-only", token)
    demo_release = fetch_demo_release(repo, token)
    topics = fetch_repo_topics(repo, token)
    topic_list = ", ".join(f"`{topic}`" for topic in topics) if topics else "none reported"
    listing_rows = []
    for pr in LISTING_PRS:
        status = fetch_listing_pr(pr, token)
        checks = "; ".join(status["checks"]) if status["checks"] else "none reported"
        followup = f"[update]({status['followup_url']})" if status["followup_url"] else "-"
        status = {**status, "checks": checks, "followup": followup}
        listing_rows.append(
            "| {name} | {kind} | {state} | {merged} | {mergeable} | [link]({url}) | [entry]({contributor_link}) | {followup} | {checks} |".format(
                **status,
            )
        )
    for issue in LISTING_ISSUES:
        status = fetch_listing_issue(issue, token)
        checks = "; ".join(status["checks"]) if status["checks"] else "none reported"
        followup = f"[update]({status['followup_url']})" if status["followup_url"] else "-"
        status = {**status, "checks": checks, "followup": followup}
        listing_rows.append(
            "| {name} | {kind} | {state} | {merged} | {mergeable} | [link]({url}) | [entry]({contributor_link}) | {followup} | {checks} |".format(
                **status,
            )
        )
    listing_rows.extend(directory_rows(repo, token))

    rows = [
        MARKER,
        "# Contributor Discovery Listing Status",
        "",
        "These channels help external contributors find starter issues. They do not",
        "count as Claude for OSS contributor evidence until real external PRs are",
        "merged in this repository.",
        "",
        f"- Repository: `https://github.com/{repo}`",
        f"- GitHub topics: {topic_list}",
        f"- Open `up-for-grabs` issues: `{up_for_grabs}`",
        f"- Open `first-timers-only` issues: `{first_timers}`",
        f"- Hosted web demo: {HOSTED_DEMO_URL}",
        f"- Web demo prerelease: `{demo_release['status']}`"
        + (f" - {demo_release['url']}" if demo_release["url"] else ""),
        f"- Web demo asset: {demo_release['asset'] or 'missing'}",
        "",
        "| Listing | Kind | State | Merged | Mergeable | Listing item | Contributor link | Follow-up | Checks |",
        "|---|---|---|---|---|---|---|---|---|",
        *listing_rows,
        "",
        "## Public Status Links",
        "",
        "- Public sprint update:",
        "  `https://github.com/duct-tape2/ai-language-partner/issues/52#issuecomment-4914030370`",
        "- Automated discovery status comment:",
        "  `https://github.com/duct-tape2/ai-language-partner/issues/52#issuecomment-4914054370`",
        "- Public contributor call:",
        "  `https://github.com/duct-tape2/ai-language-partner/discussions/55`",
        "- Canonical auto-updated contributor call comment:",
        "  `https://github.com/duct-tape2/ai-language-partner/discussions/55#discussioncomment-17582510`",
        "",
        "## Maintainer Follow-Up",
        "",
        "- Check open listing PRs daily until merged or reviewed.",
        "- If a maintainer requests changes, fix them in the listing fork and record the",
        "  resolution here.",
        "- After a listing merges, update `docs/CLAUDE_FOR_OSS_APPLICATION.md` with the",
        "  merged listing URL and keep the contributor count separate from listing",
        "  evidence.",
        "- For Awesome Japanese, wait for a stronger app-store or release-build story",
        "  before reopening.",
        "- Track that maturity work in",
        "  `docs/community/INSTALLABLE_DEMO_RELEASE_PLAN.md`.",
        "- Monitor the CodeTriage profile for new subscribers and confirm its issue",
        "  feed remains synchronized.",
        "- Monitor Good First Issue.org Discussion #1. If its GitHub OAuth flow is",
        "  restored, complete the supported submission once instead of duplicating",
        "  the public request.",
        "- Keep the 24 Pull Requests project active while reviewable starter issues",
        "  remain open; update its labels if the public taxonomy changes.",
        "- Monitor the Help Wanted project page and keep its indexed issue set current.",
        "- Track Meaningful Code issue #147 until the project is reviewed or listed;",
        "  do not duplicate it with the web form or a second PR.",
        "- Track For Good First Issue PR #494 until it is merged or reviewed.",
        "- Do not open duplicate listing PRs or use misleading beginner labels.",
        "",
        "## Useful Search Links",
        "",
        "- `up-for-grabs`: `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Aup-for-grabs`",
        "- `first-timers-only`: `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Afirst-timers-only`",
        "- `good first issue`: `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22`",
        "- `good-first-issue` topic: `https://github.com/topics/good-first-issue`",
        "- `good-first-pr` topic: `https://github.com/topics/good-first-pr`",
        "- `help-wanted` topic: `https://github.com/topics/help-wanted`",
        "- `japanese-learning` topic: `https://github.com/topics/japanese-learning`",
        "- `language-learning` topic: `https://github.com/topics/language-learning`",
        "- `learn-japanese` topic: `https://github.com/topics/learn-japanese`",
        "- `local-first` topic: `https://github.com/topics/local-first`",
        "- `react-native` topic: `https://github.com/topics/react-native`",
        "- Good First Issue project submission criteria:",
        "  `https://github.com/DeepSourceCorp/good-first-issue`",
        "- For Good First Issue repository:",
        f"  `{FOR_GOOD_FIRST_ISSUE_URL}`",
        "- CodeTriage project profile:",
        f"  `https://www.codetriage.com/{repo}`",
        "- Good First Issue.org indexing request:",
        f"  `{GOOD_FIRST_ISSUE_ORG_REQUEST_URL}`",
        "- 24 Pull Requests public project listing:",
        f"  `{TWENTY_FOUR_PULL_REQUESTS_URL}` (project `3564`)",
        "- Help Wanted indexed project page:",
        f"  `{HELP_WANTED_PROJECT_URL}` (37 issues observed 2026-07-10)",
        "- Meaningful Code project submission:",
        "  `https://github.com/Meaningful-Code/meaningfulcode-frontend/issues/147`",
    ]
    return "\n".join(rows)


def upsert_issue_comment(repo: str, issue: int, body: str, token: str) -> str:
    comments_url = f"https://api.github.com/repos/{repo}/issues/{issue}/comments?per_page=100"
    comments = github_json(comments_url, token)
    if not isinstance(comments, list):
        raise TypeError("GitHub comments response was not a list")
    for comment in comments:
        if isinstance(comment, dict) and MARKER in str(comment.get("body", "")):
            updated = github_json(str(comment["url"]), token, method="PATCH", payload={"body": body})
            if isinstance(updated, dict):
                return str(updated.get("html_url", ""))
    created = github_json(
        f"https://api.github.com/repos/{repo}/issues/{issue}/comments",
        token,
        method="POST",
        payload={"body": body},
    )
    if isinstance(created, dict):
        return str(created.get("html_url", ""))
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--issue", type=int, default=DEFAULT_ISSUE)
    parser.add_argument("--out", help="Write the Markdown snapshot to a file")
    parser.add_argument("--comment", action="store_true", help="Create or update the sprint issue status comment")
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.comment and not token:
        print("GITHUB_TOKEN or GH_TOKEN is required for --comment", file=sys.stderr)
        return 2

    body = build_markdown(args.repo, token)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body + "\n", encoding="utf-8")
    else:
        print(body)

    if args.comment:
        url = upsert_issue_comment(args.repo, args.issue, body, str(token))
        print(f"status comment: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
