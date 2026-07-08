#!/usr/bin/env python3
"""Validate the contributor outreach queue.

The queue is an execution aid for finding real external contributors. It is not
evidence by itself; only useful merged external PRs count for Claude for OSS.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "docs" / "community" / "OUTREACH_QUEUE.json"
REQUIRED_ITEM_FIELDS = {
    "id",
    "audience",
    "lane",
    "issue_query",
    "message_template",
    "status",
    "posted_url",
    "notes",
}


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list):
        return fail("items must be a list")

    allowed_statuses = set(payload.get("status_values") or [])
    if not allowed_statuses:
        return fail("status_values must not be empty")

    seen_ids: set[str] = set()
    lanes: set[str] = set()
    posted = 0
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return fail(f"item {index} must be an object")
        missing = sorted(REQUIRED_ITEM_FIELDS - set(item))
        if missing:
            return fail(f"{item.get('id', index)} missing fields: {', '.join(missing)}")
        item_id = str(item["id"])
        if item_id in seen_ids:
            return fail(f"duplicate id: {item_id}")
        seen_ids.add(item_id)
        status = str(item["status"])
        if status not in allowed_statuses:
            return fail(f"{item_id} has invalid status: {status}")
        issue_query = str(item["issue_query"])
        if not issue_query.startswith("https://github.com/duct-tape2/ai-language-partner/"):
            return fail(f"{item_id} issue_query must point at this repository")
        posted_url = str(item["posted_url"])
        if posted_url:
            posted += 1
            if not posted_url.startswith("https://"):
                return fail(f"{item_id} posted_url must be an https URL when set")
        lanes.add(str(item["lane"]))

    if len(items) < 20:
        return fail(f"expected at least 20 outreach items, got {len(items)}")
    if len(lanes) < 6:
        return fail(f"expected at least 6 contribution lanes, got {len(lanes)}")

    print(f"PASS: outreach queue has {len(items)} item(s), {len(lanes)} lane(s), {posted} posted URL(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
