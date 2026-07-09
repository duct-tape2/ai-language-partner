#!/usr/bin/env python3
"""Unit tests for Claude for OSS evidence counting.

These tests use fixture GitHub search results so the contributor-counting rules
can be checked in CI without live API access.
"""

from __future__ import annotations

import json
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

    def test_governance_script_checks_pinned_sprint_issue(self) -> None:
        source = Path("scripts/verify_github_governance.py").read_text(encoding="utf-8")

        self.assertIn("pinnedIssues", source)
        self.assertIn("20 contributor sprint kickoff pinned", source)
        self.assertIn("issue.get(\"number\") == 52", source)

    def test_governance_script_checks_discovery_topics(self) -> None:
        source = Path("scripts/verify_github_governance.py").read_text(encoding="utf-8")

        self.assertIn("DISCOVERY_TOPICS", source)
        self.assertIn("help-wanted", source)
        self.assertIn("contributor discovery topics", source)


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
    def test_claude_oss_evidence_refresh_opens_pr_not_direct_main_push(self) -> None:
        workflow = Path(".github/workflows/claude-oss-evidence-refresh.yml").read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("github.event.pull_request.merged == true", workflow)
        self.assertIn("--allow-not-ready", workflow)
        self.assertIn("automation/claude-oss-evidence", workflow)
        self.assertIn("github.rest.pulls.create", workflow)
        self.assertIn("ref: main", workflow)

    def test_contributor_interest_triage_workflow_has_lane_links(self) -> None:
        workflow = Path(".github/workflows/contributor-interest-triage.yml").read_text(encoding="utf-8")

        self.assertIn("ai-language-partner:contributor-interest-triage", workflow)
        self.assertIn("FIRST_ISSUE_MATCHER.md", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR.md", workflow)
        self.assertIn("Korean docs or learner notes", workflow)
        self.assertIn("Japanese naturalness review", workflow)
        self.assertIn("FIRST_PR_RECIPES.md", workflow)
        self.assertIn("github.rest.issues.createComment", workflow)

    def test_contributor_sprint_status_workflow_posts_single_status_comment(self) -> None:
        workflow = Path(".github/workflows/contributor-sprint-status.yml").read_text(encoding="utf-8")

        self.assertIn("post_contributor_sprint_status.py", workflow)
        self.assertIn("--comment", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR.md", workflow)

    def test_issue_claim_guidance_workflow_handles_claim_comments(self) -> None:
        workflow = Path(".github/workflows/issue-claim-guidance.yml").read_text(encoding="utf-8")

        self.assertIn("issue_comment:", workflow)
        self.assertIn("/claim", workflow)
        self.assertIn("ai-language-partner:issue-claim-guidance", workflow)
        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", workflow)
        self.assertIn("FIVE_MINUTE_FIRST_PR.md", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("issue.pull_request", workflow)

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
        self.assertIn("ai-language-partner:pr-welcome", workflow)
        self.assertIn("issues.listComments", workflow)
        self.assertIn("PR welcome comment already exists", workflow)
        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", workflow)

    def test_issue_and_interest_workflows_link_hosted_demo(self) -> None:
        issue_workflow = Path(".github/workflows/issue-welcome.yml").read_text(encoding="utf-8")
        interest_workflow = Path(".github/workflows/contributor-interest-triage.yml").read_text(encoding="utf-8")

        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", issue_workflow)
        self.assertIn("https://duct-tape2.github.io/ai-language-partner/demo/", interest_workflow)


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
        self.assertIn("FIRST_ISSUE_MATCHER.md", markdown)
        self.assertIn("FIVE_MINUTE_FIRST_PR.md", markdown)
        self.assertIn("not Claude", markdown)
        self.assertIn("[#1: docs: add Korean quick-start]", markdown)
        self.assertIn("Maintainer-authored PRs, bots", markdown)


class ContributorFunnelStatusTest(unittest.TestCase):
    def test_contributor_interest_issues_exclude_maintainer_and_bots(self) -> None:
        fixtures = [
            contributor_funnel.IssueItem(52, "community: sprint", "https://example.test/52", "github-actions[bot]", "", "", ()),
            contributor_funnel.IssueItem(53, "community: maintainer note", "https://example.test/53", "duct-tape2", "", "", ()),
            contributor_funnel.IssueItem(54, "community: contributor interest", "https://example.test/54", "new-helper", "", "", ()),
        ]

        with patch.object(contributor_funnel, "search_issues", return_value=fixtures):
            issues = contributor_funnel.contributor_interest_issues("duct-tape2/ai-language-partner", token=None)

        self.assertEqual([issue.number for issue in issues], [54])

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
            contributor_funnel, "count_open_issues", side_effect=[34, 24]
        ), patch.object(
            contributor_funnel, "no_install_task_count", return_value=27
        ):
            markdown = contributor_funnel.build_markdown("duct-tape2/ai-language-partner", "2025-07-09", "2026-07-09", token=None)

        self.assertIn(contributor_funnel.MARKER, markdown)
        self.assertIn("Unique external merged PR contributors: `2/20`", markdown)
        self.assertIn("Open external PRs needing maintainer attention: `1`", markdown)
        self.assertIn("Active claim signals on open issues: `1`", markdown)
        self.assertIn("Open contributor interest issues: `1`", markdown)
        self.assertIn("Hosted web demo", markdown)
        self.assertIn("Call for contributors discussion", markdown)
        self.assertIn("FIRST_ISSUE_MATCHER.md", markdown)
        self.assertIn("[#88: docs: improve setup]", markdown)
        self.assertIn("[#1: docs: add Korean quick-start]", markdown)
        self.assertIn("within 24 hours", markdown)


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
        self.assertIn("FIRST_ISSUE_MATCHER.md", page)
        self.assertIn("No-install first PR board", page)
        self.assertIn("20+ unique external contributors", page)
        self.assertIn("Maintainer PRs", page)
        self.assertIn("metric-only changes are excluded", page)

    def test_outreach_messages_link_contributor_call(self) -> None:
        messages = Path("docs/community/OUTREACH_MESSAGES.md").read_text(encoding="utf-8")

        self.assertIn("CALL_FOR_CONTRIBUTORS.html", messages)
        self.assertIn("Contributor call", messages)
        self.assertIn("FIRST_ISSUE_MATCHER.md", messages)

    def test_outreach_queue_tracks_public_discussion_post(self) -> None:
        payload = json.loads(Path("docs/community/OUTREACH_QUEUE.json").read_text(encoding="utf-8"))
        items = payload["items"]
        posted = [item for item in items if item["posted_url"]]

        self.assertGreaterEqual(len(items), 22)
        self.assertTrue(any(item["posted_url"] == "https://github.com/duct-tape2/ai-language-partner/discussions/55" for item in posted))
        self.assertTrue(any(item["id"] == "outreach_00" and item["status"] == "posted" for item in items))


class NoInstallFirstPrBoardTest(unittest.TestCase):
    def test_first_issue_matcher_has_direct_routes_and_counting_guardrails(self) -> None:
        matcher = Path("docs/community/FIRST_ISSUE_MATCHER.md").read_text(encoding="utf-8")

        self.assertIn("Thirty-Second Match", matcher)
        self.assertIn("https://github.com/duct-tape2/ai-language-partner/edit/main/", matcher)
        self.assertIn("Closes #ISSUE_NUMBER", matcher)
        self.assertIn("20+ unique external contributors", matcher)
        self.assertIn("metric-only changes do not count", matcher)

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

        self.assertIn("Issues covered: `27`", comments)
        self.assertIn(no_install_guides.MARKER, comments)
        self.assertIn("Hosted web demo", comments)
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

        self.assertIn("Up For Grabs", names)
        self.assertIn("Awesome for Beginners", names)
        self.assertIn("Awesome for Non-Programmers", names)
        self.assertIn("Awesome Language Learning", names)
        self.assertIn("Awesome Japanese Learning Resources", names)
        self.assertIn("Awesome Japanese Study Materials", names)
        self.assertIn("Awesome Japanese", {listing.name for listing in discovery_snapshot.LISTING_ISSUES})

    def test_good_first_issue_directory_is_locked_until_ten_contributors(self) -> None:
        with patch.object(discovery_snapshot, "collect_evidence", return_value=[object(), object()]):
            rows = discovery_snapshot.directory_rows("duct-tape2/ai-language-partner", token=None)

        self.assertIn("Good First Issue", rows[0])
        self.assertIn("locked", rows[0])
        self.assertIn("current 2/10", rows[0])
        self.assertIn("FIRST_ISSUE_MATCHER.md", rows[0])

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
            discovery_snapshot, "directory_rows", return_value=["| Good First Issue | Directory | locked | n/a | requires 10 contributors; current 0/10 | [link](https://example.test/gfi) | [issues](https://example.test/first) | - | README criteria |"]
        ):
            markdown = discovery_snapshot.build_markdown("duct-tape2/ai-language-partner", token=None)

        self.assertIn(discovery_snapshot.MARKER, markdown)
        self.assertIn("Open `up-for-grabs` issues: `18`", markdown)
        self.assertIn("Open `first-timers-only` issues: `16`", markdown)
        self.assertIn("do not", markdown)
        self.assertIn("count as Claude for OSS contributor evidence", markdown)
        self.assertIn("Hosted web demo: https://duct-tape2.github.io/ai-language-partner/demo/", markdown)
        self.assertIn("Web demo prerelease: `active`", markdown)
        self.assertIn("https://example.test/releases/demo.zip", markdown)
        self.assertIn("[link](https://example.test/pull/1)", markdown)
        self.assertIn("[update](https://example.test/pull/1#comment)", markdown)
        self.assertIn("Good First Issue", markdown)
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


if __name__ == "__main__":
    unittest.main()
