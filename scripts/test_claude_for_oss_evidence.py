#!/usr/bin/env python3
"""Unit tests for Claude for OSS evidence counting.

These tests use fixture GitHub search results so the contributor-counting rules
can be checked in CI without live API access.
"""

from __future__ import annotations

import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_claude_for_oss_evidence as evidence  # noqa: E402
import build_pr_review_packet as review_packet  # noqa: E402
import render_starter_issue_index as issue_index  # noqa: E402
import verify_github_governance as governance  # noqa: E402
import post_first_pr_recipes as first_pr_recipes  # noqa: E402
import apply_discovery_labels as discovery_labels  # noqa: E402
import snapshot_discovery_listings as discovery_snapshot  # noqa: E402
import post_no_install_first_pr_guides as no_install_guides  # noqa: E402
import post_pr_review_packet as pr_review_comment  # noqa: E402


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


class PrReviewPacketTest(unittest.TestCase):
    def test_packet_blocks_maintainer_generated_files_and_missing_issue(self) -> None:
        pr = {
            "number": 51,
            "title": "docs: update audio examples",
            "body": "",
            "html_url": "https://example.test/pull/51",
            "user": {"login": "duct-tape2", "type": "User"},
            "author_association": "OWNER",
            "draft": False,
            "merged": True,
            "labels": [{"name": "docs"}],
        }
        files = [{"filename": "docs/example.md"}, {"filename": "packs/haruka/v1/audio.wav"}]

        packet = review_packet.build_packet("duct-tape2/ai-language-partner", pr, files)

        self.assertFalse(packet.countable_candidate)
        self.assertIn("maintainer-authored PR", packet.blockers)
        self.assertIn("generated/private files changed", packet.blockers)
        self.assertIn("no issue reference", " ".join(packet.blockers))
        self.assertIn("packs/haruka/v1/audio.wav", packet.markdown)

    def test_packet_accepts_useful_external_merged_pr_candidate(self) -> None:
        pr = {
            "number": 88,
            "title": "docs: clarify setup, closes #34",
            "body": "Closes #34",
            "html_url": "https://example.test/pull/88",
            "user": {"login": "new-helper", "type": "User"},
            "author_association": "CONTRIBUTOR",
            "draft": False,
            "merged": True,
            "labels": [{"name": "docs"}],
        }
        files = [{"filename": "docs/community/CONTRIBUTOR_LANDING.md"}]

        packet = review_packet.build_packet("duct-tape2/ai-language-partner", pr, files)

        self.assertTrue(packet.countable_candidate)
        self.assertEqual(packet.blockers, ())
        self.assertIn("docs/content review: verify links and wording manually", packet.markdown)
        self.assertIn("Countable candidate: `yes`", packet.markdown)


class PrReviewPacketCommentTest(unittest.TestCase):
    def test_render_comment_wraps_packet_as_non_decision_triage_aid(self) -> None:
        packet = review_packet.ReviewPacket(
            markdown="# PR Review Packet: #88\n\n- Countable candidate: `no`",
            countable_candidate=False,
            blockers=("PR is not merged yet",),
        )

        with patch.object(pr_review_comment, "fetch_pr_packet", return_value=packet):
            comment = pr_review_comment.render_comment("duct-tape2/ai-language-partner", 88, "token")

        self.assertIn(pr_review_comment.MARKER, comment)
        self.assertIn("Automated Maintainer Review Packet", comment)
        self.assertIn("not a merge decision", comment)
        self.assertIn("not Claude for OSS evidence by itself", comment)
        self.assertIn("# PR Review Packet: #88", comment)
        self.assertIn("Countable candidate: `no`", comment)

    def test_pr_review_packet_workflow_uses_trusted_base_checkout(self) -> None:
        workflow = Path(".github/workflows/pr-review-packet.yml").read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("Checkout trusted base branch", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.base.ref }}", workflow)
        self.assertIn("pull-requests: read", workflow)
        self.assertIn("python scripts/post_pr_review_packet.py", workflow)
        self.assertNotIn("github.event.pull_request.head", workflow)


class GovernanceCheckTest(unittest.TestCase):
    def test_governance_check_prints_pass_fail_marker(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            self.assertTrue(governance.check("example", True, "ok"))
            self.assertFalse(governance.check("example", False, "not ok"))
        self.assertIn("PASS: example - ok", stream.getvalue())
        self.assertIn("FAIL: example - not ok", stream.getvalue())


class FirstPrRecipeTest(unittest.TestCase):
    def test_recipe_infers_backend_files_and_checks(self) -> None:
        issue = first_pr_recipes.Issue(
            number=40,
            title="backend: add OpenAPI example for dialogue pack listing",
            url="https://example.test/issues/40",
            body="Acceptance: includes response shape.",
            labels=("good first issue", "docs", "backend"),
        )

        recipe = first_pr_recipes.render_recipe("duct-tape2/ai-language-partner", issue)

        self.assertIn(first_pr_recipes.MARKER, recipe)
        self.assertIn("contracts/openapi_v0.yaml", recipe)
        self.assertIn("cd apps/api && python -m pytest", recipe)
        self.assertIn("Closes #40", recipe)

    def test_recipe_infers_language_review_manual_check(self) -> None:
        issue = first_pr_recipes.Issue(
            number=7,
            title="content: review yui v1 beginner dialogue Korean translations",
            url="https://example.test/issues/7",
            body="Acceptance: fixes unnatural Korean explanations.",
            labels=("good first issue", "content", "language-review"),
        )

        recipe = first_pr_recipes.render_recipe("duct-tape2/ai-language-partner", issue)

        self.assertIn("packs/yui/v1/story.json", recipe)
        self.assertIn("manual language/content review", recipe)
        self.assertIn("generated/private assets", recipe)


class WorkflowFixtureTest(unittest.TestCase):
    def test_contributor_interest_triage_workflow_has_lane_links(self) -> None:
        workflow = Path(".github/workflows/contributor-interest-triage.yml").read_text(encoding="utf-8")

        self.assertIn("ai-language-partner:contributor-interest-triage", workflow)
        self.assertIn("Korean docs or learner notes", workflow)
        self.assertIn("Japanese naturalness review", workflow)
        self.assertIn("FIRST_PR_RECIPES.md", workflow)
        self.assertIn("github.rest.issues.createComment", workflow)


class NoInstallFirstPrBoardTest(unittest.TestCase):
    def test_no_install_board_links_browser_edit_tasks_and_guardrails(self) -> None:
        board = Path("docs/community/NO_INSTALL_FIRST_PRS.md").read_text(encoding="utf-8")

        self.assertIn("https://github.com/duct-tape2/ai-language-partner/edit/main/", board)
        self.assertIn("first-timers-only", board)
        self.assertIn("No command-line check is required", board)
        self.assertIn("Do not split trivial", board)
        self.assertIn("Do not add `.wav`, `.zip`, `.npy`, `.sqlite`", board)

    def test_parse_no_install_board_and_render_comment(self) -> None:
        board = """
| Issue | Good PR shape | Source file | Direct edit link |
|---|---|---|---|
| [#44: first PR walkthrough](https://github.com/duct-tape2/ai-language-partner/issues/44) | Improve this repo's first-PR instructions | `docs/community/FIRST_PR_WALKTHROUGH.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/FIRST_PR_WALKTHROUGH.md) |
"""

        tasks = no_install_guides.parse_board(board)
        comment = no_install_guides.render_comment("duct-tape2/ai-language-partner", tasks[0])

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].number, 44)
        self.assertIn(no_install_guides.MARKER, comment)
        self.assertIn("Direct edit link", comment)
        self.assertIn("Closes #44", comment)
        self.assertIn("Tiny split", comment)

    def test_no_install_workflow_posts_only_outside_pull_requests(self) -> None:
        workflow = Path(".github/workflows/no-install-first-pr-guides.yml").read_text(encoding="utf-8")

        self.assertIn("post_no_install_first_pr_guides.py", workflow)
        self.assertIn("github.event_name != 'pull_request'", workflow)

    def test_generated_no_install_comments_cover_board_tasks(self) -> None:
        comments = Path("docs/community/NO_INSTALL_FIRST_PR_COMMENTS.md").read_text(encoding="utf-8")

        self.assertIn("Issues covered: `11`", comments)
        self.assertIn(no_install_guides.MARKER, comments)
        self.assertIn("Closes #1", comments)
        self.assertIn("Closes #44", comments)


class DiscoveryLabelsTest(unittest.TestCase):
    def test_first_timers_subset_is_not_empty_and_excludes_harder_issue(self) -> None:
        self.assertIn(1, discovery_labels.FIRST_TIMERS_ISSUES)
        self.assertIn(44, discovery_labels.FIRST_TIMERS_ISSUES)
        self.assertNotIn(22, discovery_labels.FIRST_TIMERS_ISSUES)
        self.assertIn("up-for-grabs", discovery_labels.DISCOVERY_LABELS)
        self.assertIn("first-timers-only", discovery_labels.DISCOVERY_LABELS)


class DiscoveryListingSnapshotTest(unittest.TestCase):
    def test_listing_prs_track_current_external_channels(self) -> None:
        names = {listing.name for listing in discovery_snapshot.LISTING_PRS}

        self.assertIn("Up For Grabs", names)
        self.assertIn("Awesome for Beginners", names)
        self.assertIn("Awesome for Non-Programmers", names)

    def test_build_markdown_keeps_listings_separate_from_contributor_evidence(self) -> None:
        listing_status = {
            "name": "Example Listing",
            "url": "https://example.test/pull/1",
            "state": "open",
            "merged": False,
            "mergeable": True,
            "draft": False,
            "checks": ["Project Changes: completed success"],
            "contributor_link": "https://example.test/labels/first-timers-only",
        }

        with patch.object(discovery_snapshot, "count_open_issues", side_effect=[18, 16]), patch.object(
            discovery_snapshot, "fetch_listing_pr", return_value=listing_status
        ):
            markdown = discovery_snapshot.build_markdown("duct-tape2/ai-language-partner", token=None)

        self.assertIn(discovery_snapshot.MARKER, markdown)
        self.assertIn("Open `up-for-grabs` issues: `18`", markdown)
        self.assertIn("Open `first-timers-only` issues: `16`", markdown)
        self.assertIn("do not", markdown)
        self.assertIn("count as Claude for OSS contributor evidence", markdown)
        self.assertIn("[PR](https://example.test/pull/1)", markdown)


if __name__ == "__main__":
    unittest.main()
