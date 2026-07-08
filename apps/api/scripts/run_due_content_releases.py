from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.store import ApiStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply due scheduled/planned content releases.")
    parser.add_argument("--db-path", default=os.environ.get("AI_LANGUAGE_PARTNER_DB_PATH"))
    parser.add_argument("--actor", default=os.environ.get("AI_LANGUAGE_PARTNER_RELEASE_WORKER_ACTOR", "content-release-worker"))
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    store = ApiStore(args.db_path) if args.db_path else ApiStore()
    result = {"ok": True, **store.run_due_content_releases(actor=args.actor, limit=args.limit)}
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
