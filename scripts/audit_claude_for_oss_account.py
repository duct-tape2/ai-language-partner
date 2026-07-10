#!/usr/bin/env python3
"""Audit GitHub-account eligibility signals for Claude for OSS.

This script checks the official tracks that can be measured from GitHub:

- Active contributor: merged PRs authored into repositories not owned by the
  maintainer account in the last 12 months.
- Community builder: unique external contributors with merged PRs in each
  maintained source repository in the last 12 months.

Other tracks, such as package downloads, foundation maintainer status, and
OpenSSF criticality score, are reported as manual checks because this repo does
not publish package-registry artifacts yet.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OWNER = "duct-tape2"
DEFAULT_MAINTAINERS = {"duct-tape2", "sinmb79"}
TARGET_REPO = "duct-tape2/ai-language-partner"
OFFICIAL_PROGRAM_URL = "https://claude.com/contact-sales/claude-for-oss"


@dataclass(frozen=True)
class RepoSummary:
    full_name: str
    url: str
    fork: bool
    archived: bool
    pushed_at: str


@dataclass(frozen=True)
class ExternalContributorSummary:
    repo: RepoSummary
    unique_authors: tuple[str, ...]
    merged_pr_count: int
    sample_prs: tuple[str, ...]


@dataclass(frozen=True)
class ActiveContributorSummary:
    login: str
    merged_pr_count: int | None
    sample_prs: tuple[str, ...]
    error: str | None = None


@dataclass(frozen=True)
class AccountAudit:
    owner: str
    login: str
    since: str
    generated_on: str
    maintained_repos: tuple[RepoSummary, ...]
    community_repos: tuple[ExternalContributorSummary, ...]
    active_contributor: ActiveContributorSummary

    @property
    def best_community_repo(self) -> ExternalContributorSummary | None:
        if not self.community_repos:
            return None
        return max(
            self.community_repos,
            key=lambda item: (
                len(item.unique_authors),
                item.merged_pr_count,
                item.repo.full_name == TARGET_REPO,
            ),
        )

    @property
    def community_builder_ready(self) -> bool:
        best = self.best_community_repo
        return bool(best and len(best.unique_authors) >= 20)

    @property
    def active_contributor_ready(self) -> bool:
        return self.active_contributor.merged_pr_count is not None and self.active_contributor.merged_pr_count >= 100


def utc_today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def default_since() -> str:
    return (utc_today() - dt.timedelta(days=365)).isoformat()


def token_from_env() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def github_json(url: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-language-partner-claude-oss-account-audit",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def is_bot(login: str, user_type: str | None) -> bool:
    return user_type == "Bot" or login.endswith("[bot]") or login in {"dependabot", "renovate-bot"}


def is_external_author(user: dict[str, Any], maintainers: set[str]) -> bool:
    login = str(user.get("login") or "")
    if not login:
        return False
    if login.lower() in {name.lower() for name in maintainers}:
        return False
    return not is_bot(login, str(user.get("type") or ""))


def repo_from_api(payload: dict[str, Any]) -> RepoSummary:
    return RepoSummary(
        full_name=str(payload.get("full_name") or ""),
        url=str(payload.get("html_url") or ""),
        fork=bool(payload.get("fork")),
        archived=bool(payload.get("archived")),
        pushed_at=str(payload.get("pushed_at") or ""),
    )


def list_repos(owner: str, token: str | None) -> list[RepoSummary]:
    repos: list[RepoSummary] = []
    for page in range(1, 11):
        params = urllib.parse.urlencode({"per_page": "100", "page": str(page), "sort": "updated"})
        data = github_json(f"https://api.github.com/users/{owner}/repos?{params}", token)
        if not isinstance(data, list):
            raise TypeError("GitHub repos response was not a list")
        repos.extend(repo_from_api(item) for item in data if isinstance(item, dict))
        if len(data) < 100:
            break
    return repos


def merged_external_prs_from_payloads(
    pulls: list[dict[str, Any]], since: str, maintainers: set[str]
) -> tuple[tuple[str, ...], int, tuple[str, ...]]:
    authors: dict[str, None] = {}
    samples: list[str] = []
    merged_count = 0
    for pull in pulls:
        merged_at = str(pull.get("merged_at") or "")
        if not merged_at or merged_at[:10] < since:
            continue
        user = pull.get("user") if isinstance(pull.get("user"), dict) else {}
        if not is_external_author(user, maintainers):
            continue
        login = str(user.get("login") or "")
        authors.setdefault(login, None)
        merged_count += 1
        if len(samples) < 5:
            samples.append(str(pull.get("html_url") or ""))
    return tuple(sorted(authors)), merged_count, tuple(sample for sample in samples if sample)


def closed_pulls(repo: str, token: str | None) -> list[dict[str, Any]]:
    pulls: list[dict[str, Any]] = []
    for page in range(1, 11):
        params = urllib.parse.urlencode(
            {
                "state": "closed",
                "sort": "updated",
                "direction": "desc",
                "per_page": "100",
                "page": str(page),
            }
        )
        data = github_json(f"https://api.github.com/repos/{repo}/pulls?{params}", token)
        if not isinstance(data, list):
            raise TypeError("GitHub pulls response was not a list")
        pulls.extend(item for item in data if isinstance(item, dict))
        if len(data) < 100:
            break
    return pulls


def community_summaries(
    repos: list[RepoSummary], since: str, maintainers: set[str], token: str | None
) -> tuple[ExternalContributorSummary, ...]:
    summaries: list[ExternalContributorSummary] = []
    for repo in repos:
        if repo.fork or repo.archived:
            continue
        authors, merged_count, sample_prs = merged_external_prs_from_payloads(
            closed_pulls(repo.full_name, token),
            since,
            maintainers,
        )
        summaries.append(ExternalContributorSummary(repo, authors, merged_count, sample_prs))
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                len(item.unique_authors),
                item.merged_pr_count,
                item.repo.full_name == TARGET_REPO,
                item.repo.pushed_at,
            ),
            reverse=True,
        )
    )


def active_contributor_summary(login: str, since: str, token: str | None) -> ActiveContributorSummary:
    query = f"is:pr is:merged author:{login} -user:{login} merged:>={since}"
    params = urllib.parse.urlencode({"q": query, "per_page": "100"})
    try:
        data = github_json(f"https://api.github.com/search/issues?{params}", token)
    except urllib.error.HTTPError as exc:
        return ActiveContributorSummary(login, None, (), f"GitHub search failed: HTTP {exc.code}")

    if not isinstance(data, dict):
        raise TypeError("GitHub search response was not an object")
    items = data.get("items") if isinstance(data.get("items"), list) else []
    samples = tuple(str(item.get("html_url") or "") for item in items[:10] if isinstance(item, dict))
    return ActiveContributorSummary(login, int(data.get("total_count") or 0), samples)


def authenticated_login(owner: str, token: str | None) -> str:
    if not token:
        return owner
    try:
        data = github_json("https://api.github.com/user", token)
    except urllib.error.HTTPError:
        return owner
    if isinstance(data, dict) and data.get("login"):
        return str(data["login"])
    return owner


def build_audit(owner: str, since: str, maintainers: set[str], token: str | None) -> AccountAudit:
    login = authenticated_login(owner, token)
    all_maintainers = set(maintainers) | {owner, login}
    repos = list_repos(owner, token)
    source_repos = tuple(repo for repo in repos if not repo.fork)
    return AccountAudit(
        owner=owner,
        login=login,
        since=since,
        generated_on=utc_today().isoformat(),
        maintained_repos=source_repos,
        community_repos=community_summaries(repos, since, all_maintainers, token),
        active_contributor=active_contributor_summary(login, since, token),
    )


def status(ok: bool) -> str:
    return "READY" if ok else "NOT READY"


def count_or_unknown(value: int | None) -> str:
    return "unknown" if value is None else str(value)


def render_markdown(audit: AccountAudit) -> str:
    best = audit.best_community_repo
    best_count = len(best.unique_authors) if best else 0
    active_count = audit.active_contributor.merged_pr_count
    rows = [
        "| Track | Current status | Count | Evidence |",
        "|---|---|---:|---|",
        (
            "| Maintainer/library author: dependent repos/packages or registry downloads "
            "| Manual / not claimed | - | No package-registry release or dependency evidence recorded |"
        ),
        (
            "| Core contributor to recognized foundation/language project "
            "| Manual / not claimed | - | Not used as the application basis |"
        ),
        (
            f"| Active contributor: 100+ merged PRs into repos not owned by `{audit.login}` "
            f"| {status(audit.active_contributor_ready)} | {count_or_unknown(active_count)}/100 | "
            f"GitHub search for merged PRs since `{audit.since}` |"
        ),
        (
            "| Community builder: one maintained repo with 20+ unique external merged PR contributors "
            f"| {status(audit.community_builder_ready)} | {best_count}/20 | "
            f"Best repo: `{best.repo.full_name if best else 'none'}` |"
        ),
        (
            "| Critical infrastructure: OpenSSF criticality score >= 0.4 "
            "| Manual / not claimed | - | Not expected for this new education OSS launch |"
        ),
    ]

    community_rows = [
        "| Repository | External contributors | Merged external PRs | Last push | Sample PRs |",
        "|---|---:|---:|---|---|",
    ]
    for item in audit.community_repos:
        sample = "<br>".join(item.sample_prs) if item.sample_prs else "-"
        community_rows.append(
            f"| [`{item.repo.full_name}`]({item.repo.url}) | {len(item.unique_authors)} | "
            f"{item.merged_pr_count} | `{item.repo.pushed_at[:10]}` | {sample} |"
        )

    active_samples = "\n".join(f"- {url}" for url in audit.active_contributor.sample_prs) or "- None found"
    if audit.active_contributor.error:
        active_samples = f"- {audit.active_contributor.error}"

    overall = "READY" if (audit.community_builder_ready or audit.active_contributor_ready) else "NOT READY"
    return "\n".join(
        [
            "# Claude for OSS Account Eligibility Audit",
            "",
            f"- Official program page: `{OFFICIAL_PROGRAM_URL}`",
            f"- GitHub owner audited: `{audit.owner}`",
            f"- Authenticated login used for active-contributor search: `{audit.login}`",
            f"- Evidence window starts: `{audit.since}`",
            f"- Generated on: `{audit.generated_on}`",
            f"- Overall verified status from GitHub API: `{overall}`",
            "",
            "This audit covers the GitHub-measurable criteria. It does not invent",
            "package downloads, foundation roles, criticality scores, or contributor",
            "activity that is not present in GitHub's public/API records.",
            "",
            "## Criteria Snapshot",
            "",
            *rows,
            "",
            "## Community-Builder Repo Scan",
            "",
            *community_rows,
            "",
            "## Active-Contributor Sample",
            "",
            active_samples,
            "",
            "## Decision",
            "",
            (
                "Do not submit a Phase B Claude for OSS application yet."
                if overall != "READY"
                else "A verified GitHub-measurable route is ready for application review."
            ),
            "",
            "The fastest current route remains the community-builder path for",
            "`duct-tape2/ai-language-partner`: recruit, review, and merge useful PRs",
            "from 20 unique external human contributors.",
            "",
        ]
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="GitHub owner whose maintained repos should be audited")
    parser.add_argument("--since", default=default_since(), help="Earliest merged date, YYYY-MM-DD")
    parser.add_argument("--maintainer", action="append", default=[], help="Additional maintainer login to exclude")
    parser.add_argument("--out", help="Optional Markdown report path")
    args = parser.parse_args(argv[1:])

    token = token_from_env()
    maintainers = DEFAULT_MAINTAINERS | set(args.maintainer)
    try:
        audit = build_audit(args.owner, args.since, maintainers, token)
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8"), file=sys.stderr)
        return 2

    markdown = render_markdown(audit)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    return 0 if (audit.community_builder_ready or audit.active_contributor_ready) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
