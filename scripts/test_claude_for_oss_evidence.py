#!/usr/bin/env python3
"""Unit tests for Claude for OSS evidence counting.

These tests use fixture GitHub search results so the contributor-counting rules
can be checked in CI without live API access.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_claude_for_oss_evidence as evidence  # noqa: E402
import render_starter_issue_index as issue_index  # noqa: E402


def issue_item(
    login: str,
    number: int,
    title: str,
    *,
    association: str = "NONE",
    user_type: str = "User",
    labels: list[str] | None = None,
    closed_at: str = "2026-07-08T00:00:00Z",
) -> dict[str, object]:
    return {
        "number": number,
        "title": title,
        "html_url": f"https://github.com/duct-tape2/ai-language-partner/pull/{number}",
        "closed_at": closed_at,
        "author_association": association,
        "user": {"login": login, "type": user_type},
        "pull_request": {"url": f"https://api.github.com/repos/duct-tape2/ai-language-partner/pulls/{number}"},
        "labels": [{"name": label} for label in (labels or [])],
    }


class EvidenceCountingTest(unittest.TestCase):
    def test_collect_evidence_counts_unique_external_contributors_only(self) -> None:
        fixtures = [
            issue_item("duct-tape2", 10, "docs: maintainer update", association="OWNER"),
            issue_item("dependabot[bot]", 11, "build: bump dependency", user_type="Bot"),
            issue_item("trusted-helper", 12, "tests: collaborator update", association="COLLABORATOR"),
            issue_item("hana-reviewer", 13, "docs: improve Korean setup", labels=["docs"]),
            issue_item("hana-reviewer", 14, "content: second useful PR", labels=["content"]),
            issue_item("ren-sensei", 15, "content: fix N5 dialogue", labels=["language-review"]),
            issue_item("accessibility-pal", 16, "mobile: improve contrast", labels=["accessibility"]),
        ]
        merged_at = {
            "13": "2026-07-02T10:00:00Z",
            "15": "2026-07-03T10:00:00Z",
            "16": "2026-07-04T10:00:00Z",
        }

        def fake_merged_at(url: str, token: str | None, fallback: str) -> str:
            pr_number = url.rsplit("/", 1)[-1]
            return merged_at.get(pr_number, fallback)

        with patch.object(evidence, "search_merged_prs", return_value=fixtures), patch.object(
            evidence, "pr_merged_at", side_effect=fake_merged_at
        ):
            prs = evidence.collect_evidence(
                "duct-tape2/ai-language-partner",
                "2025-07-08",
                {"manual-exclude"},
                token=None,
            )

        self.assertEqual([pr.contributor for pr in prs], ["accessibility-pal", "ren-sensei", "hana-reviewer"])
        self.assertEqual([pr.area for pr in prs], ["accessibility", "language-review", "docs"])
        self.assertEqual([pr.number for pr in prs], [16, 15, 13])

    def test_collect_evidence_honors_manual_exclude(self) -> None:
        fixtures = [
            issue_item("manual-exclude", 20, "docs: helpful but excluded"),
            issue_item("new-helper", 21, "tests: add fixture", labels=["tests"]),
        ]

        with patch.object(evidence, "search_merged_prs", return_value=fixtures), patch.object(
            evidence, "pr_merged_at", return_value="2026-07-08T00:00:00Z"
        ):
            prs = evidence.collect_evidence(
                "duct-tape2/ai-language-partner",
                "2025-07-08",
                {"manual-exclude"},
                token=None,
            )

        self.assertEqual([pr.contributor for pr in prs], ["new-helper"])

    def test_markdown_table_escapes_pipe_in_title(self) -> None:
        pr = evidence.EvidencePr(
            contributor="new-helper",
            number=21,
            title="docs: Korean | Japanese quickstart",
            url="https://github.com/duct-tape2/ai-language-partner/pull/21",
            area="docs",
            merged_at="2026-07-08",
            author_association="NONE",
        )

        table = evidence.markdown_table([pr], limit=20)

        self.assertIn("Korean \\| Japanese", table)
        self.assertNotIn("Korean | Japanese quickstart](https", table)


class StarterIssueIndexTest(unittest.TestCase):
    def test_lane_for_prioritizes_work_area_labels(self) -> None:
        cases = [
            (("docs", "backend"), "Backend/API docs"),
            (("docs", "mobile"), "Mobile/accessibility"),
            (("docs", "tests"), "Tests/tooling"),
            (("content", "language-review"), "Dialogue/content review"),
            (("docs", "community"), "Release/community"),
            (("docs",), "Korean/Japanese docs"),
        ]

        for labels, expected in cases:
            with self.subTest(labels=labels):
                issue = issue_index.Issue(1, "docs: example", "https://example.test/1", labels)
                self.assertEqual(issue_index.lane_for(issue), expected)

    def test_render_markdown_groups_issues(self) -> None:
        issues = [
            issue_index.Issue(1, "docs: backend example", "https://example.test/1", ("docs", "backend")),
            issue_index.Issue(2, "mobile: label controls", "https://example.test/2", ("mobile", "accessibility")),
            issue_index.Issue(3, "content: review yui", "https://example.test/3", ("content", "good first issue")),
        ]

        markdown = issue_index.render_markdown("duct-tape2/ai-language-partner", issues, "2026-07-08")

        self.assertIn("Open issues indexed: `3`", markdown)
        self.assertIn("| Backend/API docs | 1 |", markdown)
        self.assertIn("| Mobile/accessibility | 1 |", markdown)
        self.assertIn("| Dialogue/content review | 1 |", markdown)
        self.assertIn("[#3: content: review yui](https://example.test/3)", markdown)


if __name__ == "__main__":
    unittest.main()
