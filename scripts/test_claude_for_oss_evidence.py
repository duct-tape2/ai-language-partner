#!/usr/bin/env python3
"""Unit tests for Claude for OSS evidence counting.

These tests use fixture GitHub search results so the contributor-counting rules
can be checked in CI without live API access.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
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
import post_contributor_sprint_status as sprint_status  # noqa: E402
import update_claude_application_evidence as evidence_update  # noqa: E402
import snapshot_contributor_funnel as contributor_funnel  # noqa: E402
import audit_claude_for_oss_account as account_audit  # noqa: E402
import post_contributor_call_update as contributor_call_update  # noqa: E402
import verify_claude_for_oss_readiness as readiness  # noqa: E402
import post_outreach_batch_status as outreach_batch  # noqa: E402


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
    def test_default_since_uses_a_rolling_utc_date(self) -> None:
        today = dt.date(2026, 7, 10)

        with patch.object(evidence, "utc_today", return_value=today):
            self.assertEqual(evidence.default_since(), "2025-07-10")
        with patch.object(account_audit, "utc_today", return_value=today):
            self.assertEqual(account_audit.default_since(), "2025-07-10")

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

        self.assertIn("Open issues observed: `3`", markdown)
        self.assertIn("Currently available starter issues: `3`", markdown)
        self.assertIn("| Backend/API docs | 1 |", markdown)
        self.assertIn("| Mobile/accessibility | 1 |", markdown)
        self.assertIn("| Dialogue/content review | 1 |", markdown)
        self.assertIn("[#3: content: review yui](https://example.test/3)", markdown)

    def test_render_markdown_excludes_claimed_and_assigned_issues(self) -> None:
        issues = [
            issue_index.Issue(1, "docs: available", "https://example.test/1", ("docs",)),
            issue_index.Issue(2, "docs: claimed", "https://example.test/2", ("docs", "claimed")),
            issue_index.Issue(3, "docs: assigned", "https://example.test/3", ("docs",), ("new-helper",)),
        ]

        markdown = issue_index.render_markdown("duct-tape2/ai-language-partner", issues, "2026-07-08")

        self.assertIn("Currently available starter issues: `1`", markdown)
        self.assertIn("Reserved or assigned issues excluded: `2`", markdown)
        self.assertIn("[#1: docs: available](https://example.test/1)", markdown)
        self.assertNotIn("[#2: docs: claimed]", markdown)
        self.assertNotIn("[#3: docs: assigned]", markdown)


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

    def test_pr_review_packet_suggests_codespaces_backend_check(self) -> None:
        pr = {
            "number": 88,
            "title": "backend: clarify provider status, closes #19",
            "body": "Closes #19",
            "html_url": "https://example.test/pull/88",
            "user": {"login": "api-helper", "type": "User"},
            "author_association": "CONTRIBUTOR",
            "draft": False,
            "merged": True,
            "labels": [{"name": "backend"}],
        }
        files = [{"filename": "apps/api/README.md"}]

        packet = review_packet.build_packet("duct-tape2/ai-language-partner", pr, files)

        self.assertIn("cd apps/api && .venv/bin/python -m pytest", packet.markdown)


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
        self.assertIn("branches: [main]", workflow)
        self.assertIn("Checkout trusted base branch", workflow)
        self.assertIn("ref: main", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("python scripts/post_pr_review_packet.py", workflow)
        self.assertNotIn("github.event.pull_request.head", workflow)
        self.assertNotIn("github.event.pull_request.base.ref", workflow)


class GovernanceCheckTest(unittest.TestCase):
    def test_governance_check_prints_pass_fail_marker(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            self.assertTrue(governance.check("example", True, "ok"))
            self.assertFalse(governance.check("example", False, "not ok"))
        self.assertIn("PASS: example - ok", stream.getvalue())
        self.assertIn("FAIL: example - not ok", stream.getvalue())

    def test_governance_script_checks_pinned_sprint_issue(self) -> None:
        source = Path("scripts/verify_github_governance.py").read_text(encoding="utf-8")

        self.assertIn("pinnedIssues", source)
        self.assertIn("20 contributor sprint kickoff pinned", source)
        self.assertIn("issue.get(\"number\") == 52", source)

    def test_governance_script_checks_discovery_topics(self) -> None:
        source = Path("scripts/verify_github_governance.py").read_text(encoding="utf-8")

        self.assertIn("DISCOVERY_TOPICS", source)
        self.assertIn("DOMAIN_TOPICS", source)
        self.assertIn("PROGRAM_TOPICS", source)
        self.assertIn("help-wanted", source)
        self.assertIn("edulinkup", source)
        self.assertIn("elusoc", source)
        self.assertIn("contributor discovery topics", source)
        self.assertIn("domain discovery topics", source)
        self.assertIn("active contributor program topics", source)
        self.assertIn('build_type == "workflow"', source)

    def test_pages_workflow_deploys_docs_with_jekyll(self) -> None:
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")

        self.assertIn("actions/configure-pages", workflow)
        self.assertIn("actions/jekyll-build-pages", workflow)
        self.assertIn("source: docs", workflow)
        self.assertIn("actions/deploy-pages", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)

    def test_scorecard_workflow_uses_pinned_default_branch_analysis(self) -> None:
        workflow = Path(".github/workflows/scorecard.yml").read_text(encoding="utf-8")

        self.assertIn("branches: [main]", workflow)
        self.assertIn("schedule:", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("permissions: read-all", workflow)
        self.assertIn("security-events: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("ossf/scorecard-action@4eaacf0543bb3f2c246792bd56e8cdeffafb205a", workflow)
        self.assertIn("publish_results: true", workflow)
        self.assertIn("github/codeql-action/upload-sarif@e46ed2cbd01164d986452f91f178727624ae40d7", workflow)
        self.assertNotIn("pull_request:", workflow)

    def test_security_workflows_use_least_privilege_defaults(self) -> None:
        for path in (
            ".github/workflows/api-docker-smoke.yml",
            ".github/workflows/mobile-verify.yml",
            ".github/workflows/repo-hygiene.yml",
        ):
            with self.subTest(path=path):
                workflow = Path(path).read_text(encoding="utf-8")
                self.assertIn("permissions:\n  contents: read", workflow)
                self.assertIn("actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5", workflow)

        for path in (
            ".github/workflows/claude-oss-evidence-refresh.yml",
            ".github/workflows/starter-issue-index.yml",
        ):
            with self.subTest(path=path):
                workflow = Path(path).read_text(encoding="utf-8")
                self.assertIn("permissions: read-all", workflow)
                self.assertIn("permissions:\n      contents: write", workflow)
                self.assertIn("issues: read", workflow)
                self.assertIn("pull-requests: write", workflow)
                self.assertIn("actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5", workflow)
                self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)

        review_packet = Path(".github/workflows/pr-review-packet.yml").read_text(encoding="utf-8")
        mobile = Path(".github/workflows/mobile-verify.yml").read_text(encoding="utf-8")
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", review_packet)
        self.assertIn("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020", mobile)

    def test_security_policy_has_private_reporting_link_and_timeline(self) -> None:
        policy = Path("SECURITY.md").read_text(encoding="utf-8")

        self.assertIn("security/advisories/new", policy)
        self.assertIn("14\ndays", policy)
        self.assertIn("90\ndays", policy)
        self.assertIn("coordinated-disclosure", policy)


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
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", recipe)
        self.assertIn("CODESPACES_FIRST_PR.html", recipe)
        self.assertIn("discussions/53", recipe)
        self.assertNotIn("DIRECTORY_FIRST_PR.html", recipe)
        self.assertNotIn("FIRST_ISSUE_MATCHER.html", recipe)
        self.assertLessEqual(recipe.count("https://"), 3)
        self.assertLess(len(recipe), 2_000)
        self.assertIn("contracts/openapi_v0.yaml", recipe)
        self.assertIn("cd apps/api && .venv/bin/python -m pytest", recipe)
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
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", recipe)
        self.assertIn("CODESPACES_FIRST_PR.html", recipe)
        self.assertIn("generated media", recipe)

    def test_recipe_infers_malformed_multipart_test_and_handler_files(self) -> None:
        issue = first_pr_recipes.Issue(
            number=49,
            title="backend: add malformed multipart upload test for STT endpoint",
            url="https://example.test/issues/49",
            body="Acceptance: missing multipart file returns 422.",
            labels=("good first issue", "backend", "tests"),
        )

        recipe = first_pr_recipes.render_recipe("duct-tape2/ai-language-partner", issue)

        self.assertIn("apps/api/tests/test_api_contract.py", recipe)
        self.assertIn("apps/api/app/main.py", recipe)
        self.assertNotIn("contracts/openapi_v0.yaml", recipe)
        self.assertIn("cd apps/api && .venv/bin/python -m pytest", recipe)

    def test_first_pr_walkthrough_recipe_stays_browser_only_and_one_file(self) -> None:
        issue = first_pr_recipes.Issue(
            number=44,
            title="docs: improve first PR walkthrough",
            url="https://example.test/issues/44",
            body="Acceptance: improve the browser-only walkthrough.",
            labels=("good first issue", "docs", "community"),
        )

        recipe = first_pr_recipes.render_recipe("duct-tape2/ai-language-partner", issue)

        self.assertIn("docs/community/FIRST_PR_WALKTHROUGH.md", recipe)
        self.assertNotIn("docs/ko/index.md", recipe)
        self.assertNotIn("docs/ja/index.md", recipe)
        self.assertIn("GitHub Markdown preview", recipe)
        self.assertNotIn("python3 scripts/check_public_tree.py", recipe)

    def test_recipe_extracts_markdown_acceptance_section_without_flattening_issue_body(self) -> None:
        issue = first_pr_recipes.Issue(
            number=13,
            title="mobile: audit touch target sizes in bottom tabs",
            url="https://example.test/issues/13",
            body="""## Goal

Guarantee stable bottom navigation targets.

## Acceptance criteria

- Each tab has at least 48 logical pixels of target height.
- The frontend regression check fails if the guarantee is removed.

## Non-goals

- No navigation redesign.
""",
            labels=("good first issue", "first-timers-only", "accessibility", "mobile"),
        )

        recipe = first_pr_recipes.render_recipe("duct-tape2/ai-language-partner", issue)

        self.assertIn("apps/mobile/scripts/verify-frontend-regressions.mjs", recipe)
        self.assertIn("Each tab has at least 48 logical pixels", recipe)
        self.assertIn("frontend regression check fails", recipe)
        self.assertNotIn("Guarantee stable bottom navigation targets", recipe)
        self.assertNotIn("No navigation redesign", recipe)

    def test_upsert_recipe_skips_patch_when_comment_is_unchanged(self) -> None:
        existing = {
            "url": "https://api.github.test/comments/1",
            "html_url": "https://github.test/issues/1#issuecomment-1",
            "body": "same recipe",
        }

        with patch.object(first_pr_recipes, "existing_recipe_comment", return_value=existing), patch.object(
            first_pr_recipes, "github_json"
        ) as github_json:
            action, url = first_pr_recipes.upsert_recipe(
                "duct-tape2/ai-language-partner",
                1,
                "token",
                "same recipe",
            )

        self.assertEqual(action, "unchanged")
        self.assertEqual(url, existing["html_url"])
        github_json.assert_not_called()

    def test_upsert_recipe_patches_when_comment_changed(self) -> None:
        existing = {
            "url": "https://api.github.test/comments/1",
            "html_url": "https://github.test/issues/1#issuecomment-1",
            "body": "old recipe",
        }
        updated = {"html_url": existing["html_url"]}

        with patch.object(first_pr_recipes, "existing_recipe_comment", return_value=existing), patch.object(
            first_pr_recipes, "github_json", return_value=updated
        ) as github_json:
            action, url = first_pr_recipes.upsert_recipe(
                "duct-tape2/ai-language-partner",
                1,
                "token",
                "new recipe",
            )

        self.assertEqual(action, "updated")
        self.assertEqual(url, existing["html_url"])
        github_json.assert_called_once_with(
            existing["url"],
            "token",
            method="PATCH",
            payload={"body": "new recipe"},
        )

    def test_existing_recipe_comment_ignores_foreign_marker_and_finds_page_two(self) -> None:
        foreign = {
            "id": 1,
            "user": {"login": "other-app[bot]"},
            "body": first_pr_recipes.MARKER,
        }
        page_one = [foreign] + [
            {"id": index + 2, "user": {"login": "someone"}, "body": "plain"}
            for index in range(99)
        ]
        owned = {
            "id": 200,
            "user": {"login": first_pr_recipes.TRUSTED_COMMENT_LOGIN},
            "body": first_pr_recipes.MARKER,
        }

        with patch.object(first_pr_recipes, "github_json", side_effect=[page_one, [owned]]) as github_json:
            result = first_pr_recipes.existing_recipe_comment(
                "duct-tape2/ai-language-partner", 44, "token"
            )

        self.assertEqual(result, owned)
        self.assertEqual(github_json.call_count, 2)
        self.assertIn("page=2", github_json.call_args_list[1].args[0])

    def test_existing_recipe_comment_uses_first_owned_duplicate(self) -> None:
        first = {
            "id": 10,
            "user": {"login": first_pr_recipes.TRUSTED_COMMENT_LOGIN},
            "body": first_pr_recipes.MARKER,
        }
        second = {**first, "id": 11}

        with patch.object(first_pr_recipes, "github_json", return_value=[first, second]):
            result = first_pr_recipes.existing_recipe_comment(
                "duct-tape2/ai-language-partner", 44, "token"
            )

        self.assertEqual(result, first)


class WorkflowFixtureTest(unittest.TestCase):
    def test_claude_oss_evidence_refresh_opens_pr_not_direct_main_push(self) -> None:
        workflow = Path(".github/workflows/claude-oss-evidence-refresh.yml").read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("github.event.pull_request.merged == true", workflow)
        self.assertIn("--allow-not-ready", workflow)
        self.assertNotIn("--since", workflow)
        self.assertIn("automation/claude-oss-evidence", workflow)
        self.assertIn("github.rest.pulls.create", workflow)
        self.assertIn("ref: main", workflow)

    def test_contributor_interest_triage_workflow_has_lane_links(self) -> None:
        workflow = Path(".github/workflows/contributor-interest-triage.yml").read_text(encoding="utf-8")

        self.assertIn("ai-language-partner:contributor-interest-triage", workflow)
        self.assertIn("DIRECTORY_FIRST_PR.html", workflow)
        self.assertIn("FIRST_ISSUE_MATCHER.html", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR_KO.html", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", workflow)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", workflow)
        self.assertIn("NO_INSTALL_FIRST_PRS.html", workflow)
        self.assertIn("CODESPACES_FIRST_PR.html", workflow)
        self.assertIn("discussions/53", workflow)
        self.assertIn("기여 분야", workflow)
        self.assertIn("貢献分野", workflow)
        self.assertIn("Korean docs or learner notes", workflow)
        self.assertIn("Japanese naturalness review", workflow)
        self.assertIn("CALL_FOR_CONTRIBUTORS_JA.html", workflow)
        self.assertIn("FIRST_PR_RECIPES.html", workflow)
        self.assertIn("github.rest.issues.createComment", workflow)
        self.assertIn("issues/6", workflow)
        self.assertIn("issues/27", workflow)
        self.assertIn("issues/49", workflow)
        self.assertNotIn("issues/22", workflow)
        self.assertNotIn("issues/40", workflow)
        self.assertNotIn("issues/42", workflow)

    def test_first_pr_recipes_workflow_upserts_issue_comments(self) -> None:
        workflow = Path(".github/workflows/first-pr-recipes.yml").read_text(encoding="utf-8")
        starter_workflow = Path(".github/workflows/starter-issue-index.yml").read_text(encoding="utf-8")

        self.assertIn("issues:", workflow)
        self.assertIn("Checkout trusted main", workflow)
        self.assertIn("post_first_pr_recipes.py", workflow)
        self.assertIn("--apply", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("pull_request", workflow)
        self.assertIn("types: [opened, edited, labeled, reopened]", workflow)
        self.assertNotIn("unlabeled", workflow)
        self.assertIn("github.event.label.name == 'good first issue'", workflow)
        self.assertIn("scripts/post_first_pr_recipes.py", starter_workflow)

    def test_contributor_sprint_status_workflow_posts_single_status_comment(self) -> None:
        workflow = Path(".github/workflows/contributor-sprint-status.yml").read_text(encoding="utf-8")

        self.assertIn("post_contributor_sprint_status.py", workflow)
        self.assertIn("--comment", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR.md", workflow)
        status_script = Path("scripts/post_contributor_sprint_status.py").read_text(encoding="utf-8")
        self.assertIn("DIRECTORY_FIRST_PR.html", status_script)
        self.assertIn("FIVE_MINUTE_FIRST_PR_KO.html", status_script)
        self.assertIn("contributor_interest_ko.yml", status_script)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", status_script)
        self.assertIn("contributor_interest_ja.yml", status_script)
        self.assertIn("CODESPACES_FIRST_PR.html", status_script)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", status_script)

    def test_issue_claim_guidance_workflow_handles_claim_comments(self) -> None:
        workflow = Path(".github/workflows/issue-claim-guidance.yml").read_text(encoding="utf-8")

        self.assertIn("issue_comment:", workflow)
        self.assertIn("/claim", workflow)
        self.assertIn("/renew", workflow)
        self.assertIn("renewPattern", workflow)
        self.assertIn("isRenewal", workflow)
        self.assertIn("ai-language-partner:issue-claim-guidance", workflow)
        self.assertIn("ai-language-partner:claim-lease", workflow)
        self.assertIn("claimantMarker", workflow)
        self.assertIn("(?:'d| would) like to (?:work on|take) this", workflow)
        self.assertIn("could you assign", workflow)
        self.assertIn("github.rest.issues.addAssignees", workflow)
        self.assertIn("existingAssignees.length === 0", workflow)
        self.assertIn("already had the `claimed` label or an assignee", workflow)
        self.assertIn("nearby unclaimed issue", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", workflow)
        self.assertIn("STARTER_ISSUE_INDEX.html", workflow)
        self.assertIn("discussions/53", workflow)
        self.assertNotIn("CODESPACES_FIRST_PR.html", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("github.rest.issues.addLabels", workflow)
        self.assertIn("github.rest.issues.removeLabel", workflow)
        self.assertIn("claimed", workflow)
        self.assertIn("leaseHours = 72", workflow)
        self.assertIn("up-for-grabs", workflow)
        self.assertIn("issue-claim-${{ github.repository }}-${{ github.event.issue.number }}", workflow)
        self.assertIn("queue: max", workflow)
        self.assertIn("github.rest.issues.get", workflow)
        self.assertIn("currentIssue.labels", workflow)
        self.assertIn("currentIssue.assignees", workflow)
        self.assertIn("claimLabelAdded &&", workflow)
        self.assertIn("alreadyClaimed &&", workflow)
        self.assertIn("comments.find(", workflow)
        self.assertIn("github.paginate(github.rest.issues.listComments", workflow)
        self.assertIn("ai-language-partner:issue-claim-event", workflow)
        self.assertIn("This issue claim event was already handled", workflow)
        self.assertIn('existing.user?.login === "github-actions[bot]"', workflow)
        self.assertIn("github.rest.issues.updateComment", workflow)
        self.assertIn("renewalAllowed", workflow)
        self.assertIn("currentLeaseOwner", workflow)
        self.assertIn('trustedBotLogin = "github-actions[bot]"', workflow)
        self.assertIn("right.expiresAt.getTime() - left.expiresAt.getTime()", workflow)
        self.assertIn("Your reservation for #${issue.number} is renewed", workflow)
        self.assertIn("Reservation check-in", workflow)
        self.assertIn("Maintainers review stale claims before releasing them", workflow)
        self.assertIn("issue.pull_request", workflow)

    def test_issue_claim_guidance_behavior(self) -> None:
        result = subprocess.run(
            ["node", "scripts/test_issue_claim_guidance.mjs"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("claim guidance behavior OK", result.stdout)

    def test_contributor_funnel_monitor_uses_trusted_base_checkout(self) -> None:
        workflow = Path(".github/workflows/contributor-funnel-monitor.yml").read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("issue_comment:", workflow)
        self.assertIn("Checkout trusted base branch", workflow)
        self.assertIn("ref: main", workflow)
        self.assertIn("snapshot_contributor_funnel.py", workflow)
        self.assertIn("--comment", workflow)

    def test_pr_welcome_workflow_is_single_comment_and_links_demo(self) -> None:
        workflow = Path(".github/workflows/pr-welcome.yml").read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("ai-language-partner:pr-welcome", workflow)
        self.assertIn("issues.listComments", workflow)
        self.assertIn("PR welcome comment already exists", workflow)
        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", workflow)
        self.assertIn("DIRECTORY_FIRST_PR.html", workflow)
        self.assertIn("Closes #123", workflow)
        self.assertIn("CODESPACES_FIRST_PR.html", workflow)
        self.assertIn("labels external PRs for maintainer review", workflow)

    def test_pr_triage_labels_workflow_marks_external_prs_without_counting_claim(self) -> None:
        workflow = Path(".github/workflows/pr-triage-labels.yml").read_text(encoding="utf-8")
        labels_doc = Path("docs/community/LABELS.md").read_text(encoding="utf-8")
        label_script = Path("scripts/create_github_labels.py").read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("external-pr", workflow)
        self.assertIn("needs-maintainer-review", workflow)
        self.assertIn("OWNER", workflow)
        self.assertIn("MEMBER", workflow)
        self.assertIn("COLLABORATOR", workflow)
        self.assertIn("issues.addLabels", workflow)
        self.assertIn("issues.removeLabel", workflow)
        self.assertNotIn("counted", workflow.lower())
        self.assertIn("external-pr", labels_doc)
        self.assertIn("needs-maintainer-review", labels_doc)
        self.assertIn("\"external-pr\"", label_script)
        self.assertIn("\"needs-maintainer-review\"", label_script)

    def test_pr_merge_followup_marks_candidates_without_final_counting_claim(self) -> None:
        workflow = Path(".github/workflows/pr-merge-followup.yml").read_text(encoding="utf-8")
        labels_doc = Path("docs/community/LABELS.md").read_text(encoding="utf-8")
        label_script = Path("scripts/create_github_labels.py").read_text(encoding="utf-8")
        runbook = Path("docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md").read_text(encoding="utf-8")
        policy = Path("docs/community/PR_REVIEW_AND_COUNTING_POLICY.md").read_text(encoding="utf-8")
        snippets = Path("docs/community/MAINTAINER_RESPONSE_SNIPPETS.md").read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("types: [closed]", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("pr.merged", workflow)
        self.assertIn("merged-external-pr-candidate", workflow)
        self.assertIn("not a final Claude for OSS counting decision", workflow)
        self.assertIn("issues.addLabels", workflow)
        self.assertIn("issues.removeLabel", workflow)
        self.assertIn("issues.createComment", workflow)
        self.assertIn("OWNER", workflow)
        self.assertIn("MEMBER", workflow)
        self.assertIn("COLLABORATOR", workflow)
        self.assertIn("merged-external-pr-candidate", labels_doc)
        self.assertIn("\"merged-external-pr-candidate\"", label_script)
        self.assertIn("merged-external-pr-candidate", runbook)
        self.assertIn("evidence-review queue only", runbook)
        self.assertIn("evidence-review cue", policy)
        self.assertIn("MAINTAINER_RESPONSE_SNIPPETS.md", runbook)
        self.assertIn("MAINTAINER_RESPONSE_SNIPPETS.md", policy)
        self.assertIn("First Response To A New PR", snippets)
        self.assertIn("Missing Issue Link", snippets)
        self.assertIn("Not Counted But Appreciated", snippets)
        self.assertIn("Final Counting Checklist", snippets)

    def test_pull_request_template_collects_countable_pr_signals(self) -> None:
        template = Path(".github/PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")

        self.assertIn("Closes #ISSUE_NUMBER", template)
        self.assertIn("Docs/content review only", template)
        self.assertIn("python3 scripts/check_public_tree.py", template)
        self.assertIn("cd apps/api && .venv/bin/python -m pytest", template)
        self.assertIn("DIRECTORY_FIRST_PR.html", template)
        self.assertIn("CODESPACES_FIRST_PR.html", template)
        self.assertIn("First PR help desk", template)

    def test_issue_templates_preserve_fast_lane_fields(self) -> None:
        good_first = Path(".github/ISSUE_TEMPLATE/good_first_issue.yml").read_text(encoding="utf-8")
        content_review = Path(".github/ISSUE_TEMPLATE/content_review.yml").read_text(encoding="utf-8")

        self.assertIn("DIRECTORY_FIRST_PR.html", good_first)
        self.assertIn("NO_INSTALL_FIRST_PRS.html", good_first)
        self.assertIn("FIRST_ISSUE_MATCHER.html", good_first)
        self.assertIn("Direct edit:", good_first)
        self.assertIn("First PR route", good_first)
        self.assertIn("Browser-only docs/content edit", good_first)
        self.assertIn("DIRECTORY_FIRST_PR.html", content_review)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", content_review)

    def test_issue_and_interest_workflows_link_hosted_demo(self) -> None:
        issue_workflow = Path(".github/workflows/issue-welcome.yml").read_text(encoding="utf-8")
        interest_workflow = Path(".github/workflows/contributor-interest-triage.yml").read_text(encoding="utf-8")

        for workflow in (issue_workflow, interest_workflow):
            self.assertIn("author_association", workflow)
            self.assertIn("OWNER", workflow)
            self.assertIn("MEMBER", workflow)
            self.assertIn("COLLABORATOR", workflow)
            self.assertIn('issue.user.type === "Bot"', workflow)

        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", issue_workflow)
        self.assertIn("DIRECTORY_FIRST_PR.html", issue_workflow)
        self.assertIn("FIRST_ISSUE_MATCHER.html", issue_workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", issue_workflow)
        self.assertIn("NO_INSTALL_FIRST_PRS.html", issue_workflow)
        self.assertIn("CODESPACES_FIRST_PR.html", issue_workflow)
        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", interest_workflow)
        self.assertIn("DIRECTORY_FIRST_PR.html", interest_workflow)

    def test_elusoc_application_packet_keeps_personal_data_and_program_claims_honest(self) -> None:
        packet = Path("docs/community/ELUSOC_PROJECT_ADMIN_APPLICATION.md").read_text(encoding="utf-8")
        growth_plan = Path("docs/community/CONTRIBUTOR_GROWTH_PLAN.md").read_text(encoding="utf-8")

        self.assertIn("Applicant enters directly", packet)
        self.assertIn("Password / login secret", packet)
        self.assertIn("Student` or `Professional", packet)
        self.assertIn("WhatsApp number", packet)
        self.assertIn("Telegram username", packet)
        self.assertIn("under the form's 200-word limit", packet)
        self.assertIn("TypeScript, React Native, Expo, Python, FastAPI", packet)
        self.assertIn("do not complete or submit", packet)
        self.assertIn("2 verified unique external merged-PR contributors", packet)
        self.assertIn("rechecked on 2026-07-11", packet)
        self.assertIn("do not apply `elusoc`", packet)
        self.assertIn("official platform confirms", packet)
        self.assertIn("ELUSOC_PROJECT_ADMIN_APPLICATION.md", growth_plan)

    def test_osl_internship_draft_matches_template_without_claiming_submission(self) -> None:
        draft = Path("docs/community/OPEN_SCIENCE_LABS_INTERNSHIP_IDEA_DRAFT.md").read_text(
            encoding="utf-8"
        )
        affiliation = Path("docs/community/OPEN_SCIENCE_LABS_AFFILIATION_PROPOSAL.md").read_text(
            encoding="utf-8"
        )
        normalized_draft = " ".join(draft.split())

        self.assertIn("has not been submitted", normalized_draft)
        self.assertIn("Expected Time: 350 hours", draft)
        self.assertIn("mentor availability", draft)
        self.assertIn("Compensation", draft)
        self.assertIn("Submission Gate", draft)
        self.assertIn("OPEN_SCIENCE_LABS_INTERNSHIP_IDEA_DRAFT.md", affiliation)


class ContributorSprintStatusTest(unittest.TestCase):
    def test_render_status_links_fastest_first_pr_and_counting_rules(self) -> None:
        issues = [
            sprint_status.SpotlightIssue(
                number=1,
                title="docs: add Korean quick-start",
                url="https://example.test/issues/1",
                labels=("good first issue", "docs", "first-timers-only"),
            )
        ]

        markdown = sprint_status.render_status("duct-tape2/ai-language-partner", "2025-07-08", "2026-07-08", 3, issues)

        self.assertIn(sprint_status.MARKER, markdown)
        self.assertIn("Unique external merged PR contributors: `3/20`", markdown)
        self.assertIn("Hosted web demo", markdown)
        self.assertIn("FIRST_ISSUE_MATCHER.html", markdown)
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", markdown)
        self.assertIn("CODESPACES_FIRST_PR.html", markdown)
        self.assertIn("FIVE_MINUTE_FIRST_PR_KO.html", markdown)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", markdown)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", markdown)
        self.assertIn("SHARE_KIT.html", markdown)
        self.assertIn("not Claude", markdown)
        self.assertIn("[#1: docs: add Korean quick-start]", markdown)
        self.assertIn("Maintainer-authored PRs, bots", markdown)


class ContributorFunnelStatusTest(unittest.TestCase):
    def test_claim_pattern_recognizes_natural_language_requests(self) -> None:
        self.assertIsNotNone(contributor_funnel.CLAIM_RE.search("I'd like to work on this"))
        self.assertIsNotNone(contributor_funnel.CLAIM_RE.search("Im working it"))
        self.assertIsNotNone(
            contributor_funnel.CLAIM_RE.search(
                "I'd like to take this as my first contribution. Could you assign it to me?"
            )
        )

    def test_contributor_interest_issues_exclude_maintainer_and_bots(self) -> None:
        fixtures = [
            contributor_funnel.IssueItem(52, "community: sprint", "https://example.test/52", "github-actions[bot]", "", "", ()),
            contributor_funnel.IssueItem(53, "community: maintainer note", "https://example.test/53", "duct-tape2", "", "", ()),
            contributor_funnel.IssueItem(54, "community: contributor interest", "https://example.test/54", "new-helper", "", "", ()),
        ]
        calls: list[str] = []

        def fake_search(repo: str, query: str, token: str | None, limit: int) -> list[contributor_funnel.IssueItem]:
            calls.append(query)
            return fixtures

        with patch.object(contributor_funnel, "search_issues", side_effect=fake_search):
            issues = contributor_funnel.contributor_interest_issues("duct-tape2/ai-language-partner", token=None)

        self.assertEqual([issue.number for issue in issues], [54])
        self.assertIn('is:issue is:open "Contribution lane"', calls)
        self.assertIn('is:issue is:open "기여 분야"', calls)
        self.assertIn('is:issue is:open "貢献分野"', calls)

    def test_render_funnel_status_tracks_open_prs_claims_and_entry_points(self) -> None:
        pr = contributor_funnel.IssueItem(
            number=88,
            title="docs: improve setup",
            url="https://example.test/pull/88",
            login="new-helper",
            created_at="2026-07-09T00:00:00Z",
            updated_at="2026-07-09T01:00:00Z",
            labels=("docs",),
        )
        interest = contributor_funnel.IssueItem(
            number=89,
            title="community: contributor interest",
            url="https://example.test/issues/89",
            login="reviewer",
            created_at="2026-07-09T00:00:00Z",
            updated_at="2026-07-09T02:00:00Z",
            labels=("community",),
        )
        claim = contributor_funnel.ClaimSignal(
            issue_number=1,
            issue_title="docs: add Korean quick-start",
            issue_url="https://example.test/issues/1",
            login="new-helper",
            comment_url="https://example.test/issues/1#comment",
            created_at="2026-07-09T03:00:00Z",
        )

        with patch.object(contributor_funnel, "collect_evidence", return_value=[object(), object()]), patch.object(
            contributor_funnel, "open_external_prs", return_value=[pr]
        ), patch.object(contributor_funnel, "issue_claim_signals", return_value=[claim]), patch.object(
            contributor_funnel, "contributor_interest_issues", return_value=[interest]
        ), patch.object(contributor_funnel, "open_starter_issues", return_value=[]), patch.object(
            contributor_funnel, "count_open_issues", side_effect=[34, 24, 3]
        ), patch.object(
            contributor_funnel, "no_install_task_count", return_value=27
        ):
            markdown = contributor_funnel.build_markdown("duct-tape2/ai-language-partner", "2025-07-09", "2026-07-10", token=None)

        self.assertIn(contributor_funnel.MARKER, markdown)
        self.assertIn("Unique external merged PR contributors: `2/20`", markdown)
        self.assertIn("Open external PRs needing maintainer attention: `1`", markdown)
        self.assertIn("Active claim signals on open issues: `1`", markdown)
        self.assertIn("Claim signals awaiting maintainer response: `1`", markdown)
        self.assertIn("Open contributor interest issues: `1`", markdown)
        self.assertIn("Maintainer response SLA target: `24h`", markdown)
        self.assertIn("Open external PRs over SLA: `1`", markdown)
        self.assertIn("Active claim signals over SLA: `1`", markdown)
        self.assertIn("Contributor interest issues over SLA: `1`", markdown)
        self.assertIn("Open `claimed` issues: `3`", markdown)
        self.assertIn("Hosted web demo", markdown)
        self.assertIn("Call for contributors discussion", markdown)
        self.assertIn("FIRST_ISSUE_MATCHER.html", markdown)
        self.assertIn("CODESPACES_FIRST_PR.html", markdown)
        self.assertIn("FIVE_MINUTE_FIRST_PR_KO.html", markdown)
        self.assertIn("contributor_interest_ko.yml", markdown)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", markdown)
        self.assertIn("contributor_interest_ja.yml", markdown)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", markdown)
        self.assertIn("SHARE_KIT.html", markdown)
        self.assertIn("[#88: docs: improve setup]", markdown)
        self.assertIn("[#1: docs: add Korean quick-start]", markdown)
        self.assertIn("| PR | Author | Updated | SLA |", markdown)
        self.assertIn("| Issue | Contributor | Claim comment | SLA |", markdown)
        self.assertIn("`overdue (", markdown)
        self.assertIn("within 24 hours", markdown)

    def test_claim_rows_mark_maintainer_response(self) -> None:
        claim = contributor_funnel.ClaimSignal(
            issue_number=22,
            issue_title="backend: cover traversal rejection",
            issue_url="https://example.test/issues/22",
            login="new-helper",
            comment_url="https://example.test/issues/22#comment",
            created_at="2026-07-08T00:00:00Z",
            responded_at="2026-07-10T00:00:00Z",
        )

        rows = contributor_funnel.render_claim_rows([claim], "2026-07-10")

        self.assertIn("`responded`", rows[0])
        self.assertNotIn("overdue", rows[0])


class AccountEligibilityAuditTest(unittest.TestCase):
    def test_merged_external_prs_excludes_maintainers_and_bots(self) -> None:
        pulls = [
            {
                "merged_at": "2026-07-01T00:00:00Z",
                "html_url": "https://example.test/pull/1",
                "user": {"login": "duct-tape2", "type": "User"},
            },
            {
                "merged_at": "2026-07-02T00:00:00Z",
                "html_url": "https://example.test/pull/2",
                "user": {"login": "dependabot[bot]", "type": "Bot"},
            },
            {
                "merged_at": "2026-07-03T00:00:00Z",
                "html_url": "https://example.test/pull/3",
                "user": {"login": "hana-reviewer", "type": "User"},
            },
            {
                "merged_at": "2024-07-03T00:00:00Z",
                "html_url": "https://example.test/pull/4",
                "user": {"login": "old-helper", "type": "User"},
            },
        ]

        authors, merged_count, samples = account_audit.merged_external_prs_from_payloads(
            pulls, "2025-07-09", {"duct-tape2", "sinmb79"}
        )

        self.assertEqual(authors, ("hana-reviewer",))
        self.assertEqual(merged_count, 1)
        self.assertEqual(samples, ("https://example.test/pull/3",))

    def test_account_audit_renders_not_ready_counts(self) -> None:
        repo = account_audit.RepoSummary(
            full_name="duct-tape2/ai-language-partner",
            url="https://github.com/duct-tape2/ai-language-partner",
            fork=False,
            archived=False,
            pushed_at="2026-07-09T00:00:00Z",
        )
        audit = account_audit.AccountAudit(
            owner="duct-tape2",
            login="duct-tape2",
            since="2025-07-09",
            generated_on="2026-07-09",
            maintained_repos=(repo,),
            community_repos=(account_audit.ExternalContributorSummary(repo, (), 0, ()),),
            active_contributor=account_audit.ActiveContributorSummary(
                "duct-tape2",
                2,
                ("https://github.com/up-for-grabs/up-for-grabs.net/pull/5916",),
            ),
        )

        markdown = account_audit.render_markdown(audit)

        self.assertIn("Overall verified status from GitHub API: `NOT READY`", markdown)
        self.assertIn("`duct-tape2/ai-language-partner`", markdown)
        self.assertIn("2/100", markdown)
        self.assertIn("0/20", markdown)

    def test_account_audit_prefers_target_repo_when_counts_tie(self) -> None:
        profile = account_audit.RepoSummary(
            full_name="duct-tape2/duct-tape2",
            url="https://github.com/duct-tape2/duct-tape2",
            fork=False,
            archived=False,
            pushed_at="2026-07-09T00:00:00Z",
        )
        target = account_audit.RepoSummary(
            full_name="duct-tape2/ai-language-partner",
            url="https://github.com/duct-tape2/ai-language-partner",
            fork=False,
            archived=False,
            pushed_at="2026-07-09T00:00:00Z",
        )
        audit = account_audit.AccountAudit(
            owner="duct-tape2",
            login="duct-tape2",
            since="2025-07-09",
            generated_on="2026-07-09",
            maintained_repos=(profile, target),
            community_repos=(
                account_audit.ExternalContributorSummary(profile, (), 0, ()),
                account_audit.ExternalContributorSummary(target, (), 0, ()),
            ),
            active_contributor=account_audit.ActiveContributorSummary("duct-tape2", 0, ()),
        )

        self.assertEqual(audit.best_community_repo.repo.full_name, "duct-tape2/ai-language-partner")


class ApplicationEvidenceUpdateTest(unittest.TestCase):
    def test_replace_section_updates_only_contributor_evidence_block(self) -> None:
        text = "\n".join(
            [
                "# App",
                "",
                "## Contributor Evidence",
                "",
                "old evidence",
                "",
                "## Verification Links",
                "",
                "links",
            ]
        )
        section = "## Contributor Evidence\n\nnew evidence"

        updated = evidence_update.replace_section(text, section)

        self.assertIn("new evidence", updated)
        self.assertNotIn("old evidence", updated)
        self.assertIn("## Verification Links", updated)


class ContributorCallPageTest(unittest.TestCase):
    def test_contributor_call_page_is_shareable_and_honest(self) -> None:
        page = Path("docs/community/CALL_FOR_CONTRIBUTORS.md").read_text(encoding="utf-8")

        self.assertIn("layout: page", page)
        self.assertIn("https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html", page)
        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", page)
        self.assertIn("DIRECTORY_FIRST_PR.html", page)
        self.assertIn("FIRST_ISSUE_MATCHER.html", page)
        self.assertIn("CALL_FOR_CONTRIBUTORS_JA.html", page)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", page)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", page)
        self.assertIn("contributor_interest_ja.yml", page)
        self.assertIn("No-install first PR board", page)
        self.assertIn("20+ unique external contributors", page)
        self.assertIn("Maintainer PRs", page)
        self.assertIn("metric-only changes are excluded", page)

    def test_outreach_messages_link_contributor_call(self) -> None:
        messages = Path("docs/community/OUTREACH_MESSAGES.md").read_text(encoding="utf-8")

        self.assertIn("CALL_FOR_CONTRIBUTORS.html", messages)
        self.assertIn("Contributor call", messages)
        self.assertIn("FIRST_ISSUE_MATCHER.html", messages)
        self.assertIn("CODESPACES_FIRST_PR.html", messages)
        self.assertIn("- Status: `closed`", messages)
        self.assertIn("- Posted URL: `n/a (closed)`", messages)

    def test_contributor_share_kit_is_publicly_linked_and_counting_safe(self) -> None:
        share_kit = Path("docs/community/SHARE_KIT.md").read_text(encoding="utf-8")
        readme = Path("README.md").read_text(encoding="utf-8")
        index = Path("docs/index.md").read_text(encoding="utf-8")
        landing = Path("docs/community/CONTRIBUTOR_LANDING.md").read_text(encoding="utf-8")
        playbook = Path("docs/community/OUTREACH_PLAYBOOK.md").read_text(encoding="utf-8")

        self.assertIn("layout: page", share_kit)
        self.assertIn("30-Second Posts", share_kit)
        self.assertIn("Do not mass-post identical messages", share_kit)
        self.assertIn("Only useful merged PRs", share_kit)
        self.assertIn("external contributors count", share_kit)
        self.assertIn("DIRECTORY_FIRST_PR.html", share_kit)
        self.assertIn("FIRST_ISSUE_MATCHER.html", share_kit)
        self.assertIn("NO_INSTALL_FIRST_PRS.html", share_kit)
        self.assertIn("OUTREACH_QUEUE.json", share_kit)
        self.assertIn("verify_outreach_queue.py", share_kit)
        self.assertIn("post_outreach_batch_status.py", share_kit)
        self.assertIn("SHARE_KIT.md", readme)
        self.assertIn("SHARE_KIT.html", index)
        self.assertIn("SHARE_KIT.html", landing)
        self.assertIn("SHARE_KIT.md", playbook)

    def test_directory_first_pr_fast_lane_is_publicly_linked_and_counting_safe(self) -> None:
        guide = Path("docs/community/DIRECTORY_FIRST_PR.md").read_text(encoding="utf-8")
        readme = Path("README.md").read_text(encoding="utf-8")
        index = Path("docs/index.md").read_text(encoding="utf-8")
        landing = Path("docs/community/CONTRIBUTOR_LANDING.md").read_text(encoding="utf-8")

        self.assertIn("layout: page", guide)
        self.assertIn("Start In 60 Seconds", guide)
        self.assertIn("For Good First Issue", guide)
        self.assertIn("Closes #ISSUE_NUMBER", guide)
        self.assertIn("Only useful merged external PRs count", guide)
        self.assertIn("STARTER_ISSUE_INDEX.html", guide)
        self.assertIn("excludes claimed and assigned tasks", guide)
        self.assertNotIn("issues/49", guide)
        self.assertIn("DIRECTORY_FIRST_PR.md", readme)
        self.assertIn("DIRECTORY_FIRST_PR.html", index)
        self.assertIn("DIRECTORY_FIRST_PR.html", landing)

    def test_outreach_batch_status_selects_actionable_items_and_stays_honest(self) -> None:
        items = [
            {
                "id": "outreach_01",
                "audience": "Korean Japanese-learning study group",
                "lane": "Korean docs",
                "issue_query": "https://github.com/duct-tape2/ai-language-partner/issues/1",
                "status": "draft",
                "notes": "Ask for setup review.",
            },
            {
                "id": "outreach_02",
                "audience": "Japanese reviewers",
                "lane": "Japanese review",
                "issue_query": "https://github.com/duct-tape2/ai-language-partner/issues/8",
                "status": "responded",
                "notes": "Follow up with first PR guide.",
            },
            {
                "id": "outreach_03",
                "audience": "Already counted",
                "lane": "Done",
                "issue_query": "https://github.com/duct-tape2/ai-language-partner/issues/9",
                "status": "merged-counted",
                "notes": "Done.",
            },
        ]

        selected = outreach_batch.next_batch(items, limit=2)
        markdown = outreach_batch.build_markdown(
            "duct-tape2/ai-language-partner",
            "2026-07-09",
            limit=2,
        )

        self.assertEqual([item["id"] for item in selected], ["outreach_02", "outreach_01"])
        self.assertIn(outreach_batch.MARKER, markdown)
        self.assertIn("not Claude for OSS evidence", markdown)
        self.assertIn("only useful merged PRs", markdown)
        self.assertIn("Contributor share kit", markdown)
        self.assertIn("OUTREACH_MESSAGES.html", markdown)
        self.assertIn("Next Outreach Batch", markdown)

    def test_outreach_batch_workflow_posts_to_kickoff_issue(self) -> None:
        workflow = Path(".github/workflows/outreach-batch-status.yml").read_text(encoding="utf-8")

        self.assertIn("post_outreach_batch_status.py", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("--comment", workflow)
        self.assertIn("Checkout trusted base branch", workflow)

    def test_outreach_queue_tracks_public_discussion_post(self) -> None:
        payload = json.loads(Path("docs/community/OUTREACH_QUEUE.json").read_text(encoding="utf-8"))
        items = payload["items"]
        posted = [item for item in items if item["posted_url"]]

        self.assertGreaterEqual(len(items), 22)
        self.assertTrue(any(item["posted_url"] == "https://github.com/duct-tape2/ai-language-partner/discussions/55" for item in posted))
        reddit = next(item for item in items if item["id"] == "outreach_22")
        self.assertEqual(reddit["status"], "closed")
        self.assertEqual(reddit["posted_url"], "")
        self.assertIn("deleted", reddit["notes"])
        self.assertTrue(any(item["id"] == "outreach_00" and item["status"] == "posted" for item in items))
        self.assertTrue(any(item["id"] == "outreach_23" and item["status"] == "draft" for item in items))
        self.assertTrue(any(item["issue_query"].endswith("/issues/63") for item in items))
        beginner_docs = next(item for item in items if item["id"] == "outreach_27")
        self.assertEqual(beginner_docs["status"], "posted")
        self.assertEqual(beginner_docs["issue_query"], "https://github.com/duct-tape2/ai-language-partner/issues/16")
        self.assertEqual(
            beginner_docs["posted_url"],
            "https://github.com/orgs/community/discussions/200218#discussioncomment-17599687",
        )
        self.assertIn("browser-only", beginner_docs["notes"])
        openapi_docs = next(item for item in items if item["id"] == "outreach_10")
        security_tests = next(item for item in items if item["id"] == "outreach_12")
        tooling_docs = next(item for item in items if item["id"] == "outreach_20")
        self.assertTrue(openapi_docs["issue_query"].endswith("/issues/24"))
        self.assertTrue(security_tests["issue_query"].endswith("/issues/49"))
        self.assertTrue(tooling_docs["issue_query"].endswith("/issues/26"))
        security_student = next(item for item in items if item["id"] == "outreach_28")
        self.assertEqual(security_student["status"], "posted")
        self.assertEqual(security_student["issue_query"], "https://github.com/duct-tape2/ai-language-partner/issues/49")
        self.assertEqual(
            security_student["posted_url"],
            "https://github.com/orgs/community/discussions/197632#discussioncomment-17599912",
        )
        self.assertIn("rather than a security toolkit", security_student["notes"])
        docs_first_timer = next(item for item in items if item["id"] == "outreach_29")
        self.assertEqual(docs_first_timer["status"], "posted")
        self.assertEqual(docs_first_timer["issue_query"], "https://github.com/duct-tape2/ai-language-partner/issues/44")
        self.assertEqual(
            docs_first_timer["posted_url"],
            "https://github.com/orgs/community/discussions/198822#discussioncomment-17600005",
        )
        self.assertIn("documentation fixes are taken seriously", docs_first_timer["notes"])

    def test_contributor_call_update_renders_live_discussion_comment(self) -> None:
        comment = contributor_call_update.render_comment(
            "duct-tape2/ai-language-partner",
            "2025-07-09",
            "2026-07-09",
            contributor_count=3,
            no_install_count=27,
        )

        self.assertIn(contributor_call_update.MARKER, comment)
        self.assertIn("Unique external merged PR contributors: `3/20`", comment)
        self.assertIn("Remaining contributors needed: `17`", comment)
        self.assertIn("FIRST_ISSUE_MATCHER.html", comment)
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", comment)
        self.assertIn("CODESPACES_FIRST_PR.html", comment)
        self.assertIn("FIVE_MINUTE_FIRST_PR_KO.html", comment)
        self.assertIn("CALL_FOR_CONTRIBUTORS_KO.html", comment)
        self.assertIn("contributor_interest_ko.yml", comment)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", comment)
        self.assertIn("CALL_FOR_CONTRIBUTORS_JA.html", comment)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", comment)
        self.assertIn("SHARE_KIT.html", comment)
        self.assertIn("contributor_interest_ja.yml", comment)
        self.assertIn("awesome-local-first/pull/46", comment)
        self.assertIn("not Claude for OSS evidence by", comment)

    def test_contributor_call_update_workflow_renders_without_discussion_write(self) -> None:
        workflow = Path(".github/workflows/contributor-call-update.yml").read_text(encoding="utf-8")

        self.assertIn("post_contributor_call_update.py", workflow)
        self.assertNotIn("discussions: write", workflow)
        self.assertNotIn("--comment", workflow)
        self.assertIn("Checkout trusted base branch", workflow)

    def test_contributor_call_update_discussion_lookup_uses_marker_comment(self) -> None:
        source = Path("scripts/post_contributor_call_update.py").read_text(encoding="utf-8")

        self.assertIn("addDiscussionComment", source)
        self.assertIn("updateDiscussionComment", source)
        self.assertIn("ai-language-partner:contributor-call-update", source)
        self.assertIn("viewer { login }", source)
        self.assertIn("preferred_author", source)

    def test_contributor_call_update_normalizes_bot_login_variants(self) -> None:
        self.assertEqual(
            contributor_call_update.normalized_login("github-actions[bot]"),
            "github-actions",
        )
        self.assertEqual(
            contributor_call_update.normalized_login("github-actions"),
            "github-actions",
        )

    @patch.object(contributor_call_update, "graphql")
    def test_contributor_call_update_finds_viewer_login(self, graphql_mock) -> None:
        graphql_mock.return_value = {"data": {"viewer": {"login": "duct-tape2"}}}

        self.assertEqual(contributor_call_update.viewer_login("token"), "duct-tape2")

    @patch.object(contributor_call_update, "graphql")
    def test_contributor_call_update_reuses_matching_author_comment(self, graphql_mock) -> None:
        graphql_mock.return_value = {
            "data": {
                "repository": {
                    "discussion": {
                        "id": "discussion-id",
                        "comments": {
                            "nodes": [
                                {
                                    "id": "comment-id",
                                    "body": f"{contributor_call_update.MARKER}\nstatus",
                                    "url": "https://example.test/discussioncomment/1",
                                    "author": {"login": "duct-tape2"},
                                }
                            ]
                        },
                    }
                }
            }
        }

        result = contributor_call_update.discussion_and_marker_comment(
            "duct-tape2/ai-language-partner",
            55,
            "token",
            preferred_author="duct-tape2",
        )

        self.assertEqual(
            result,
            (
                "discussion-id",
                "comment-id",
                "https://example.test/discussioncomment/1",
            ),
        )

    @patch.object(contributor_call_update, "graphql")
    def test_contributor_call_update_does_not_edit_another_author(self, graphql_mock) -> None:
        graphql_mock.return_value = {
            "data": {
                "repository": {
                    "discussion": {
                        "id": "discussion-id",
                        "comments": {
                            "nodes": [
                                {
                                    "id": "comment-id",
                                    "body": f"{contributor_call_update.MARKER}\nstatus",
                                    "url": "https://example.test/discussioncomment/2",
                                    "author": {"login": "unexpected-app-name"},
                                }
                            ]
                        },
                    }
                }
            }
        }

        result = contributor_call_update.discussion_and_marker_comment(
            "duct-tape2/ai-language-partner",
            55,
            "token",
            preferred_author="duct-tape2",
        )

        self.assertEqual(result, ("discussion-id", None, None))

    @patch.object(contributor_call_update, "build_comment", return_value="rendered status")
    def test_contributor_call_update_cli_render_mode_needs_no_token(self, build_comment_mock) -> None:
        output = StringIO()
        with patch.dict(contributor_call_update.os.environ, {}, clear=True), redirect_stdout(output):
            result = contributor_call_update.main(["post_contributor_call_update.py"])

        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue().strip(), "rendered status")
        build_comment_mock.assert_called_once()

    def test_korean_first_pr_route_is_publicly_linked(self) -> None:
        guide = Path("docs/community/FIVE_MINUTE_FIRST_PR_KO.md").read_text(encoding="utf-8")
        call = Path("docs/community/CALL_FOR_CONTRIBUTORS_KO.md").read_text(encoding="utf-8")
        template = Path(".github/ISSUE_TEMPLATE/contributor_interest.yml").read_text(encoding="utf-8")
        ko_template = Path(".github/ISSUE_TEMPLATE/contributor_interest_ko.yml").read_text(encoding="utf-8")
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("한국어 5분 첫 PR", call)
        self.assertIn("DIRECTORY_FIRST_PR.html", template)
        self.assertIn("DIRECTORY_FIRST_PR.html", ko_template)
        self.assertIn("FIVE_MINUTE_FIRST_PR_KO.html", template)
        self.assertIn("FIVE_MINUTE_FIRST_PR_KO.html", ko_template)
        self.assertIn("CALL_FOR_CONTRIBUTORS_KO.html", ko_template)
        self.assertIn("기여 분야", ko_template)
        self.assertIn("contributor_interest_ko.yml", guide)
        self.assertIn("contributor_interest_ko.yml", call)
        self.assertIn("contributor_interest_ko.yml", readme)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.md", guide)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", call)
        self.assertIn("Closes #ISSUE_NUMBER", guide)
        self.assertIn("STARTER_ISSUE_INDEX.html", guide)
        self.assertIn("예약되었거나 담당자가 있는 이슈를 제외", guide)
        self.assertIn("CI가 schema, ID, reference, safety를 자동 검증", guide)
        self.assertIn("숫자를 채우기 위한", guide)

    def test_readme_and_pages_link_github_contribute_route(self) -> None:
        readme = Path("README.md").read_text(encoding="utf-8")
        index = Path("docs/index.md").read_text(encoding="utf-8")

        self.assertIn("first--timers--only-friendly", readme)
        self.assertIn("https://github.com/duct-tape2/ai-language-partner/contribute", readme)
        self.assertIn("https://github.com/duct-tape2/ai-language-partner/contribute", index)
        self.assertIn("New here from GitHub topics", readme)
        self.assertIn("Pick a first PR in 30 seconds", readme)
        self.assertIn("27 no-install issue slots", readme)
        self.assertIn("arrived from GitHub topics", index)
        self.assertIn("Current available starter issues", index)
        self.assertIn("claimed or assigned tasks are excluded", index)
        self.assertIn("Browse current unclaimed tasks", index)

    def test_codespaces_first_pr_route_is_publicly_linked(self) -> None:
        devcontainer = json.loads(Path(".devcontainer/devcontainer.json").read_text(encoding="utf-8"))
        guide = Path("docs/community/CODESPACES_FIRST_PR.md").read_text(encoding="utf-8")
        readme = Path("README.md").read_text(encoding="utf-8")
        index = Path("docs/index.md").read_text(encoding="utf-8")
        landing = Path("docs/community/CONTRIBUTOR_LANDING.md").read_text(encoding="utf-8")
        contributing = Path("CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertIn("postCreateCommand", devcontainer)
        self.assertIn("apps/api/requirements.txt", devcontainer["postCreateCommand"])
        self.assertIn("npm ci", devcontainer["postCreateCommand"])
        self.assertIn("1293331196", guide)
        self.assertIn("CODESPACES_FIRST_PR.md", readme)
        self.assertIn("CODESPACES_FIRST_PR.html", index)
        self.assertIn("CODESPACES_FIRST_PR.html", landing)
        self.assertIn("CODESPACES_FIRST_PR.md", contributing)

    def test_japanese_first_pr_route_is_publicly_linked(self) -> None:
        guide = Path("docs/community/FIVE_MINUTE_FIRST_PR_JA.md").read_text(encoding="utf-8")
        call = Path("docs/community/CALL_FOR_CONTRIBUTORS_JA.md").read_text(encoding="utf-8")
        template = Path(".github/ISSUE_TEMPLATE/contributor_interest.yml").read_text(encoding="utf-8")
        ja_template = Path(".github/ISSUE_TEMPLATE/contributor_interest_ja.yml").read_text(encoding="utf-8")
        readme = Path("README.md").read_text(encoding="utf-8")
        ja_index = Path("docs/ja/index.md").read_text(encoding="utf-8")

        self.assertIn("日本語 5分 first PR", call)
        self.assertIn("DIRECTORY_FIRST_PR.html", template)
        self.assertIn("DIRECTORY_FIRST_PR.html", ja_template)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", template)
        self.assertIn("FIVE_MINUTE_FIRST_PR_JA.html", ja_template)
        self.assertIn("CALL_FOR_CONTRIBUTORS_JA.html", ja_template)
        self.assertIn("貢献分野", ja_template)
        self.assertIn("contributor_interest_ja.yml", guide)
        self.assertIn("contributor_interest_ja.yml", call)
        self.assertIn("contributor_interest_ja.yml", readme)
        self.assertIn("contributor_interest_ja.yml", ja_index)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.md", guide)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", call)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", ja_index)
        self.assertIn("Closes #ISSUE_NUMBER", guide)
        self.assertIn("STARTER_ISSUE_INDEX.html", guide)
        self.assertIn("予約済み・担当済みの issue を除く", guide)
        self.assertIn("CI が schema、ID、reference、safety を自動検証", guide)
        self.assertIn("数字を増やすため", guide)

    def test_readiness_required_files_include_korean_contributor_routes(self) -> None:
        self.assertIn(".github/ISSUE_TEMPLATE/contributor_interest_ko.yml", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/CALL_FOR_CONTRIBUTORS_KO.md", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/FIVE_MINUTE_FIRST_PR_KO.md", readiness.REQUIRED_FILES)
        self.assertIn(".github/ISSUE_TEMPLATE/contributor_interest_ja.yml", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/CALL_FOR_CONTRIBUTORS_JA.md", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/DIRECTORY_FIRST_PR.md", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/FIVE_MINUTE_FIRST_PR_JA.md", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/MAINTAINER_RESPONSE_SNIPPETS.md", readiness.REQUIRED_FILES)
        self.assertIn(".github/workflows/pr-triage-labels.yml", readiness.REQUIRED_FILES)
        self.assertIn(".github/workflows/pr-merge-followup.yml", readiness.REQUIRED_FILES)
        self.assertIn("docs/community/SHARE_KIT.md", readiness.REQUIRED_FILES)
        self.assertIn(".github/workflows/outreach-batch-status.yml", readiness.REQUIRED_FILES)
        self.assertIn("scripts/post_outreach_batch_status.py", readiness.REQUIRED_FILES)
        self.assertIn("scripts/push_current_branch_from_clipboard_token.sh", readiness.REQUIRED_FILES)
        self.assertIn("scripts/create_pr_from_clipboard_token.py", readiness.REQUIRED_FILES)
        self.assertIn("scripts/publish_pending_claude_oss_work_from_clipboard_token.sh", readiness.REQUIRED_FILES)

    def test_clipboard_branch_push_helper_avoids_storing_tokens(self) -> None:
        helper = Path("scripts/push_current_branch_from_clipboard_token.sh").read_text(encoding="utf-8")
        checklist = Path("docs/community/PUBLISHING_AND_APPLICATION_CHECKLIST.md").read_text(encoding="utf-8")

        self.assertIn("pbpaste", helper)
        self.assertIn("pbcopy", helper)
        self.assertIn("GIT_TERMINAL_PROMPT=0", helper)
        self.assertIn("credential.helper=", helper)
        self.assertIn("username=x-access-token", helper)
        self.assertNotIn("github.com/${TOKEN}", helper)
        self.assertIn("push_current_branch_from_clipboard_token.sh", checklist)
        self.assertIn("add-ai-language-partner", checklist)

    def test_clipboard_pr_helper_creates_existing_or_new_pr_without_gh(self) -> None:
        helper = Path("scripts/create_pr_from_clipboard_token.py").read_text(encoding="utf-8")
        checklist = Path("docs/community/PUBLISHING_AND_APPLICATION_CHECKLIST.md").read_text(encoding="utf-8")

        self.assertIn("pbpaste", helper)
        self.assertIn("pbcopy", helper)
        self.assertIn("TOKEN_PREFIXES", helper)
        self.assertIn("--token-source", helper)
        self.assertIn("env_token", helper)
        self.assertIn("existing_open_pr", helper)
        self.assertIn("https://api.github.com/repos/{repo}/pulls", helper)
        self.assertIn("maintainer_can_modify", helper)
        self.assertIn("create_pr_from_clipboard_token.py", checklist)
        self.assertIn("github/forgoodfirstissue", checklist)
        self.assertIn("duct-tape2:add-ai-language-partner", checklist)

    def test_one_shot_publish_helper_pushes_internal_and_listing_prs(self) -> None:
        helper = Path("scripts/publish_pending_claude_oss_work_from_clipboard_token.sh").read_text(encoding="utf-8")
        checklist = Path("docs/community/PUBLISHING_AND_APPLICATION_CHECKLIST.md").read_text(encoding="utf-8")

        self.assertIn("pbpaste", helper)
        self.assertIn("pbcopy", helper)
        self.assertIn("codex/directory-first-pr-fast-lane", helper)
        self.assertIn("/private/tmp/forgoodfirstissue", helper)
        self.assertIn("github/forgoodfirstissue", helper)
        self.assertIn("--token-source env", helper)
        self.assertIn("credential.helper=", helper)
        self.assertIn("refusing to publish from dirty worktree", helper)
        self.assertIn("publish_pending_claude_oss_work_from_clipboard_token.sh", checklist)
        self.assertIn("reads the copied token", checklist)
        self.assertIn("clears the clipboard", checklist)

    def test_language_review_first_pr_kit_is_reviewable_and_counting_safe(self) -> None:
        kit = Path("docs/community/LANGUAGE_REVIEW_FIRST_PR_KIT.md").read_text(encoding="utf-8")
        content_template = Path(".github/ISSUE_TEMPLATE/content_review.yml").read_text(encoding="utf-8")

        self.assertIn("layout: page", kit)
        self.assertIn("#8", kit)
        self.assertIn("#47", kit)
        self.assertIn("packs/yui/v1/story.json", kit)
        self.assertIn("apps/mobile/src/culture/cultureNotes.ts", kit)
        self.assertIn("Do not change `schemaVersion`", kit)
        self.assertIn("Closes #ISSUE_NUMBER", kit)
        self.assertIn("contributor_interest_ja.yml", kit)
        self.assertIn("contributor_interest_ko.yml", kit)
        self.assertIn("LANGUAGE_REVIEW_FIRST_PR_KIT.html", content_template)


class NoInstallFirstPrBoardTest(unittest.TestCase):
    def test_first_issue_matcher_has_direct_routes_and_counting_guardrails(self) -> None:
        matcher = Path("docs/community/FIRST_ISSUE_MATCHER.md").read_text(encoding="utf-8")

        self.assertIn("Thirty-Second Match", matcher)
        self.assertIn("https://github.com/duct-tape2/ai-language-partner/edit/main/", matcher)
        self.assertIn("Closes #ISSUE_NUMBER", matcher)
        self.assertIn("20+ unique external contributors", matcher)
        self.assertIn("metric-only changes do not count", matcher)
        self.assertIn("issues/49", matcher)
        self.assertNotIn("issues/22", matcher)

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
        self.assertIn("Open the direct edit page", comment)
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", comment)
        self.assertIn("CODESPACES_FIRST_PR.html", comment)
        self.assertIn("discussions/53", comment)
        self.assertNotIn("FIRST_ISSUE_MATCHER.html", comment)
        self.assertEqual(comment.count("https://"), 4)
        self.assertLess(len(comment), 1_600)
        self.assertIn("Closes #44", comment)
        self.assertIn("Do not split trivial", comment)

    def test_no_install_verification_matches_source_type(self) -> None:
        base = dict(
            number=1,
            title="task",
            issue_url="https://example.test/1",
            good_pr_shape="Make one change",
            edit_url="https://example.test/edit",
        )

        docs = no_install_guides.NoInstallTask(source_file="docs/index.md", **base)
        mobile = no_install_guides.NoInstallTask(source_file="apps/mobile/src/i18n.ts", **base)
        openapi = no_install_guides.NoInstallTask(source_file="contracts/openapi_v0.yaml", **base)
        dialogue = no_install_guides.NoInstallTask(source_file="packs/yui/v1/story.json", **base)

        self.assertIn("no CLI check is required", no_install_guides.verification(docs))
        self.assertIn("npm run verify", no_install_guides.verification(mobile))
        self.assertIn("pytest", no_install_guides.verification(openapi))
        self.assertIn("verify_dialogue_pack_sources.py", no_install_guides.verification(dialogue))

    def test_no_install_existing_comment_is_owned_paginated_and_duplicate_safe(self) -> None:
        foreign = {
            "id": 1,
            "user": {"login": "other-app[bot]"},
            "body": no_install_guides.MARKER,
        }
        page_one = [foreign] + [
            {"id": index + 2, "user": {"login": "someone"}, "body": "plain"}
            for index in range(99)
        ]
        first_owned = {
            "id": 200,
            "user": {"login": no_install_guides.TRUSTED_COMMENT_LOGIN},
            "body": no_install_guides.MARKER,
        }
        duplicate = {**first_owned, "id": 201}

        with patch.object(
            no_install_guides,
            "github_json",
            side_effect=[page_one, [first_owned, duplicate]],
        ) as github_json:
            result = no_install_guides.existing_guide_comment(
                "duct-tape2/ai-language-partner", 44, "token"
            )

        self.assertEqual(result, first_owned)
        self.assertEqual(github_json.call_count, 2)
        self.assertIn("page=2", github_json.call_args_list[1].args[0])

    def test_no_install_upsert_skips_unchanged_owned_comment(self) -> None:
        task = no_install_guides.NoInstallTask(
            number=44,
            title="first PR walkthrough",
            issue_url="https://example.test/44",
            good_pr_shape="Improve the walkthrough",
            source_file="docs/community/FIRST_PR_WALKTHROUGH.md",
            edit_url="https://example.test/edit",
        )
        body = no_install_guides.render_comment("duct-tape2/ai-language-partner", task)
        existing = {
            "url": "https://api.github.test/comments/1",
            "html_url": "https://github.test/issues/44#issuecomment-1",
            "body": body,
        }

        with patch.object(
            no_install_guides, "existing_guide_comment", return_value=existing
        ), patch.object(no_install_guides, "github_json") as github_json:
            action, url = no_install_guides.upsert_comment(
                "duct-tape2/ai-language-partner", task, "token"
            )

        self.assertEqual(action, "unchanged")
        self.assertEqual(url, existing["html_url"])
        github_json.assert_not_called()

    def test_no_install_workflow_posts_only_outside_pull_requests(self) -> None:
        workflow = Path(".github/workflows/no-install-first-pr-guides.yml").read_text(encoding="utf-8")

        self.assertIn("post_no_install_first_pr_guides.py", workflow)
        self.assertIn("github.event_name != 'pull_request'", workflow)

    def test_generated_no_install_comments_cover_board_tasks(self) -> None:
        comments = Path("docs/community/NO_INSTALL_FIRST_PR_COMMENTS.md").read_text(encoding="utf-8")

        self.assertIn("Issues covered: `27`", comments)
        self.assertIn(no_install_guides.MARKER, comments)
        self.assertIn("Open the direct edit page", comments)
        self.assertIn("FIVE_MINUTE_FIRST_PR.html", comments)
        self.assertIn("CODESPACES_FIRST_PR.html", comments)
        self.assertIn("discussions/53", comments)
        self.assertNotIn("DIRECTORY_FIRST_PR.html", comments)
        self.assertIn("Closes #1", comments)
        self.assertIn("Closes #24", comments)
        self.assertIn("Closes #44", comments)
        self.assertIn("Closes #50", comments)


class DiscoveryLabelsTest(unittest.TestCase):
    def test_first_timers_subset_is_not_empty_and_excludes_harder_issue(self) -> None:
        self.assertIn(1, discovery_labels.FIRST_TIMERS_ISSUES)
        self.assertIn(44, discovery_labels.FIRST_TIMERS_ISSUES)
        self.assertIn(50, discovery_labels.FIRST_TIMERS_ISSUES)
        self.assertNotIn(22, discovery_labels.FIRST_TIMERS_ISSUES)
        self.assertIn(24, discovery_labels.UP_FOR_GRABS_ISSUES)
        self.assertIn("up-for-grabs", discovery_labels.DISCOVERY_LABELS)
        self.assertIn("first-timers-only", discovery_labels.DISCOVERY_LABELS)


class DiscoveryListingSnapshotTest(unittest.TestCase):
    def test_listing_prs_track_current_external_channels(self) -> None:
        names = {listing.name for listing in discovery_snapshot.LISTING_PRS}

        self.assertIn("First Contributions Project Discovery", names)
        self.assertIn("For Good First Issue", names)
        self.assertIn("Up For Grabs", names)
        self.assertIn("Awesome for Beginners", names)
        self.assertIn("Awesome for Non-Programmers", names)
        self.assertIn("Awesome Language Learning", names)
        self.assertIn("Awesome Japanese Learning Resources", names)
        self.assertIn("Awesome Japanese Study Materials", names)
        self.assertIn("Awesome Japanese Resources", names)
        self.assertIn("Awesome Local-First", names)
        self.assertIn("Awesome Language Learning Japanese Page", names)
        self.assertIn("Awesome Open Source School", names)
        self.assertIn("Awesomo", names)
        self.assertIn("React Native Apps", names)
        self.assertIn("Awesome Open Source AI", names)
        issue_names = {listing.name for listing in discovery_snapshot.LISTING_ISSUES}
        self.assertIn("Awesome Japanese", issue_names)
        self.assertIn("Meaningful Code", issue_names)

    def test_meaningful_code_tracks_public_submission_issue(self) -> None:
        listing = next(
            issue
            for issue in discovery_snapshot.LISTING_ISSUES
            if issue.name == "Meaningful Code"
        )

        self.assertEqual(listing.repo, "Meaningful-Code/meaningfulcode-frontend")
        self.assertEqual(listing.number, 147)
        self.assertIn("impactful-project review", listing.open_next_step)
        self.assertIn("education criteria", listing.check_note)

    def test_new_active_listing_prs_have_exact_public_targets(self) -> None:
        listings = {listing.name: listing for listing in discovery_snapshot.LISTING_PRS}

        self.assertEqual(listings["Awesomo"].repo, "lk-geimfari/awesomo")
        self.assertEqual(listings["Awesomo"].number, 479)
        self.assertEqual(
            listings["React Native Apps"].repo,
            "ReactNativeNews/React-Native-Apps",
        )
        self.assertEqual(listings["React Native Apps"].number, 259)
        self.assertEqual(
            listings["Awesome Open Source AI"].repo,
            "alvinreal/awesome-opensource-ai",
        )
        self.assertEqual(listings["Awesome Open Source AI"].number, 582)

    def test_for_good_first_issue_tracks_public_pr(self) -> None:
        for_good_first_issue = next(
            listing
            for listing in discovery_snapshot.LISTING_PRS
            if listing.name == "For Good First Issue"
        )
        self.assertEqual(for_good_first_issue.repo, "github/forgoodfirstissue")
        self.assertEqual(for_good_first_issue.number, 494)
        self.assertIn("DIRECTORY_FIRST_PR.html", for_good_first_issue.contributor_link)

    def test_good_first_issue_directory_is_locked_until_ten_contributors(self) -> None:
        with patch.object(discovery_snapshot, "collect_evidence", return_value=[object(), object()]):
            rows = discovery_snapshot.directory_rows("duct-tape2/ai-language-partner", token=None)

        self.assertIn("Good First Issue", rows[0])
        self.assertIn("locked", rows[0])
        self.assertIn("current 2/10", rows[0])
        self.assertIn("FIRST_ISSUE_MATCHER.html", rows[0])
        self.assertIn("CodeTriage", rows[1])
        self.assertIn("active", rows[1])
        self.assertIn("https://www.codetriage.com/duct-tape2/ai-language-partner", rows[1])
        self.assertIn("public profile and issue sync active", rows[1])
        self.assertIn("Good First Issue.org", rows[2])
        self.assertIn("awaiting response", rows[2])
        self.assertIn("https://github.com/orgs/goodfirstissueorg/discussions/1", rows[2])
        self.assertIn("OAuth authorization is disabled", rows[2])
        self.assertIn("24 Pull Requests", rows[3])
        self.assertIn("active", rows[3])
        self.assertIn("projects?page=9", rows[3])
        self.assertIn("public project #3564", rows[3])
        self.assertIn("contribulator score 39", rows[3])
        self.assertIn("Help Wanted", rows[4])
        self.assertIn("active", rows[4])
        self.assertIn("37 indexed help-wanted issues", rows[4])
        self.assertIn("helpwanted.dev/projects/duct-tape2/ai-language-partner", rows[4])
        self.assertIn("LibHunt", rows[5])
        self.assertIn("active", rows[5])
        self.assertIn("libhunt.com/r/ai-language-partner", rows[5])
        self.assertIn("no contributor-count claim", rows[5])
        self.assertIn("Ovio", rows[6])
        self.assertIn("blocked", rows[6])
        self.assertIn("api: null", rows[6])
        self.assertIn("fallback email sent", rows[6])

    def test_build_markdown_keeps_listings_separate_from_contributor_evidence(self) -> None:
        listing_status = {
            "name": "Example Listing",
            "url": "https://example.test/pull/1",
            "kind": "PR",
            "state": "open",
            "merged": False,
            "mergeable": True,
            "draft": False,
            "checks": ["Project Changes: completed success"],
            "contributor_link": "https://example.test/labels/first-timers-only",
            "followup_url": "https://example.test/pull/1#comment",
        }
        issue_status = {
            "name": "Example Issue",
            "url": "https://example.test/issues/2",
            "kind": "Issue",
            "state": "open",
            "merged": "n/a",
            "mergeable": "awaiting maintainer acknowledgement",
            "draft": False,
            "checks": ["issue submitted before PR per contribution guidelines"],
            "contributor_link": "https://example.test/first-pr",
            "followup_url": "",
        }

        release_status = {
            "status": "active",
            "url": "https://example.test/releases/demo",
            "asset": "https://example.test/releases/demo.zip",
        }

        with patch.object(discovery_snapshot, "count_open_issues", side_effect=[18, 16]), patch.object(
            discovery_snapshot, "fetch_demo_release", return_value=release_status
        ), patch.object(discovery_snapshot, "fetch_listing_pr", return_value=listing_status), patch.object(
            discovery_snapshot, "fetch_listing_issue", return_value=issue_status
        ), patch.object(
            discovery_snapshot, "fetch_repo_topics", return_value=["good-first-issue", "language-learning"]
        ), patch.object(
            discovery_snapshot, "directory_rows", return_value=["| Good First Issue | Directory | locked | n/a | requires 10 contributors; current 0/10 | [link](https://example.test/gfi) | [issues](https://example.test/first) | - | README criteria |"]
        ):
            markdown = discovery_snapshot.build_markdown("duct-tape2/ai-language-partner", token=None)

        self.assertIn(discovery_snapshot.MARKER, markdown)
        self.assertIn("Open `up-for-grabs` issues: `18`", markdown)
        self.assertIn("Open `first-timers-only` issues: `16`", markdown)
        self.assertIn("do not", markdown)
        self.assertIn("count as Claude for OSS contributor evidence", markdown)
        self.assertIn("Hosted web demo: https://duct-tape2.github.io/ai-language-partner/demo/", markdown)
        self.assertIn("GitHub topics: `good-first-issue`, `language-learning`", markdown)
        self.assertIn("Web demo prerelease: `active`", markdown)
        self.assertIn("https://example.test/releases/demo.zip", markdown)
        self.assertIn("[link](https://example.test/pull/1)", markdown)
        self.assertIn("[update](https://example.test/pull/1#comment)", markdown)
        self.assertIn("For Good First Issue", markdown)
        self.assertIn("Good First Issue", markdown)
        self.assertIn("LibHunt", markdown)
        self.assertIn("libhunt.com/r/ai-language-partner", markdown)
        self.assertIn("awaiting maintainer acknowledgement", markdown)

    def test_closed_listing_issue_is_not_reported_as_waiting(self) -> None:
        issue = discovery_snapshot.ListingIssue(
            name="Example Issue",
            repo="example/repo",
            number=2,
            contributor_link="https://example.test/first-pr",
        )
        payload = {
            "html_url": "https://example.test/issues/2",
            "state": "closed",
            "state_reason": "completed",
        }

        with patch.object(discovery_snapshot, "github_json", return_value=payload):
            status = discovery_snapshot.fetch_listing_issue(issue, token=None)

        self.assertEqual(status["state"], "closed")
        self.assertIn("closed (completed)", status["mergeable"])
        self.assertNotIn("awaiting maintainer acknowledgement", status["mergeable"])


class PagesDemoTest(unittest.TestCase):
    def test_pages_demo_uses_project_page_safe_paths(self) -> None:
        demo = Path("docs/demo")
        index = demo / "index.html"
        self.assertTrue(index.is_file())
        self.assertFalse((demo / "_expo").exists())
        self.assertTrue((demo / "expo-static").is_dir())

        html = index.read_text(encoding="utf-8")
        self.assertIn('href="favicon.ico"', html)
        self.assertIn('src="expo-static/static/js/web/', html)
        self.assertNotIn('href="/favicon.ico"', html)
        self.assertNotIn('src="/_expo/', html)

        js_files = list((demo / "expo-static" / "static" / "js" / "web").glob("*.js"))
        self.assertTrue(js_files)
        for js_file in js_files:
            with self.subTest(js_file=js_file.name):
                text = js_file.read_text(encoding="utf-8")
                self.assertNotIn('uri:"/assets/', text)


class SecurityAutomationTest(unittest.TestCase):
    def test_codeql_scans_python_and_typescript_with_minimal_permissions(self) -> None:
        workflow = Path(".github/workflows/codeql.yml").read_text(encoding="utf-8")

        self.assertIn("javascript-typescript", workflow)
        self.assertIn("- python", workflow)
        self.assertIn("security-events: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn(
            "github/codeql-action/init@99df26d4f13ea111d4ec1a7dddef6063f76b97e9 # v4",
            workflow,
        )
        self.assertIn(
            "github/codeql-action/analyze@99df26d4f13ea111d4ec1a7dddef6063f76b97e9 # v4",
            workflow,
        )

    def test_dependency_review_blocks_new_high_severity_findings(self) -> None:
        workflow = Path(".github/workflows/dependency-review.yml").read_text(encoding="utf-8")

        self.assertIn(
            "actions/dependency-review-action@2031cfc080254a8a887f58cffee85186f0e49e48 # v4.9.0",
            workflow,
        )
        self.assertIn("fail-on-severity: high", workflow)
        self.assertIn('branches: ["main"]', workflow)

    def test_dialogue_pack_sources_are_checked_in_ci(self) -> None:
        workflow = Path(".github/workflows/dialogue-pack-sources.yml").read_text(encoding="utf-8")
        contributing = Path("CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertIn('"packs/**"', workflow)
        self.assertIn("verify_dialogue_pack_sources.py", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5", workflow)
        self.assertIn("Definition of done is task-specific", contributing)
        self.assertIn("Dialogue Pack Sources", contributing)

    def test_workflow_actions_are_pinned_by_full_commit_sha(self) -> None:
        pattern = re.compile(r"^[^@]+@[0-9a-f]{40}(?:\s+#.*)?$")
        for workflow_path in sorted(Path(".github/workflows").glob("*.yml")):
            for line_number, line in enumerate(workflow_path.read_text(encoding="utf-8").splitlines(), 1):
                if "uses:" not in line:
                    continue
                with self.subTest(workflow=workflow_path.name, line=line_number):
                    action = line.split("uses:", 1)[1].strip()
                    self.assertRegex(action, pattern)

    def test_dependabot_limits_and_groups_update_noise(self) -> None:
        config = Path(".github/dependabot.yml").read_text(encoding="utf-8")

        self.assertIn("package-ecosystem: npm", config)
        self.assertIn("package-ecosystem: pip", config)
        self.assertIn("package-ecosystem: github-actions", config)
        self.assertEqual(config.count("open-pull-requests-limit: 3"), 3)
        self.assertEqual(config.count("interval: weekly"), 3)


if __name__ == "__main__":
    unittest.main()
