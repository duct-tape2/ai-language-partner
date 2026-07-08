#!/usr/bin/env python3
"""Update docs/CLAUDE_FOR_OSS_APPLICATION.md with current PR evidence.

Usage:
  GITHUB_TOKEN=... python scripts/update_claude_application_evidence.py duct-tape2/ai-language-partner --since 2025-07-08

The script replaces only the "Contributor Evidence" section and leaves the
application copy untouched. It fails when GitHub cannot be queried so the
evidence packet never silently drifts out of date.
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
from pathlib import Path

from export_claude_for_oss_evidence import collect_evidence, default_since, markdown_table


ROOT = Path(__file__).resolve().parents[1]
APPLICATION_DOC = ROOT / "docs" / "CLAUDE_FOR_OSS_APPLICATION.md"
START = "## Contributor Evidence"
END = "## Verification Links"


def replace_section(text: str, section: str) -> str:
    start_index = text.index(START)
    end_index = text.index(END)
    return text[:start_index] + section.rstrip() + "\n\n" + text[end_index:]


def build_section(repo: str, since: str, excluded: set[str], token: str | None) -> tuple[str, int]:
    prs = collect_evidence(repo, since, excluded, token)
    count = len(prs)
    status = "READY for Phase B" if count >= 20 else "NOT READY for Phase B"
    missing = max(0, 20 - count)
    section = [
        START,
        "",
        "Fill this only with real merged PRs from unique external contributors. Do not",
        "count maintainer-authored PRs, bots, duplicate identities, or trivial spam.",
        "",
        f"- Evidence generated from: `{repo}`",
        f"- Since: `{since}`",
        f"- Unique external contributors counted: `{count}`",
        f"- Status: `{status}`",
    ]
    if missing:
        section.append(f"- Remaining contributors needed: `{missing}`")
    section.extend(["", markdown_table(prs, 20)])
    if count < 20:
        section.extend(
            [
                "",
                "Current table has fewer than 20 rows because the official community-builder",
                "threshold is not met yet. Do not submit Phase B with this status.",
            ]
        )
    return "\n".join(section), count


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="GitHub repo in owner/name form")
    parser.add_argument("--since", default=default_since(), help="Earliest merged date, YYYY-MM-DD")
    parser.add_argument("--exclude", action="append", default=[], help="Extra GitHub login to exclude")
    parser.add_argument("--dry-run", action="store_true", help="Print the replacement section without editing")
    parser.add_argument(
        "--allow-not-ready",
        action="store_true",
        help="Return success after updating even when the 20-contributor threshold is not met",
    )
    args = parser.parse_args(argv[1:])

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        section, count = build_section(args.repo, args.since, set(args.exclude), token)
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8"), file=sys.stderr)
        return 1

    if args.dry_run:
        print(section)
        return 0 if count >= 20 else 1

    text = APPLICATION_DOC.read_text(encoding="utf-8")
    updated = replace_section(text, section)
    APPLICATION_DOC.write_text(updated, encoding="utf-8")
    print(f"updated {APPLICATION_DOC}")
    print(f"unique external contributors counted: {count}")
    if args.allow_not_ready:
        return 0
    return 0 if count >= 20 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
