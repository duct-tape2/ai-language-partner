from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.reputation_model import artifact_json, reputation_profiles_to_examples, train_evaluate_reputation_model
from app.store import ApiStore, default_db_path, normalize_learner_id


def evaluate(db_path: Optional[Union[Path, str]] = None, learner_id: Optional[str] = None, include_fixture: bool = True) -> dict:
    store = ApiStore(db_path or default_db_path())
    learners = set()
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT learner_id FROM xp_events
            UNION
            SELECT learner_id FROM xp_abuse_flags
            UNION
            SELECT blocked_learner_id AS learner_id FROM social_blocks
            UNION
            SELECT blocker_learner_id AS learner_id FROM social_blocks
            """
        ).fetchall()
    learners.update(row["learner_id"] for row in rows if row["learner_id"])
    if learner_id:
        learners.add(normalize_learner_id(learner_id))
    profiles = [store.learner_reputation_profile(learner_id=item) for item in sorted(learners)]
    db_examples = reputation_profiles_to_examples(profiles, source="reputation_profiles")
    result = train_evaluate_reputation_model(db_examples=db_examples, include_fixture=include_fixture)
    result.update(
        {
            "learnerId": normalize_learner_id(learner_id) if learner_id else None,
            "profileCount": len(profiles),
            "reviewableDbExampleCount": len(db_examples),
            "dbPath": str(db_path or default_db_path()),
            "fixtureIncluded": bool(include_fixture),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Train/evaluate the offline anti-cheat reputation model.")
    parser.add_argument("--db-path", default=None, help="SQLite database path. Defaults to AI_LANGUAGE_PARTNER_DB_PATH or app data path.")
    parser.add_argument("--learner-id", default=None, help="Optional learner id to force into the evaluation cohort.")
    parser.add_argument("--no-fixture", action="store_true", help="Disable deterministic fixture examples.")
    parser.add_argument("--output", default=None, help="Optional output JSON path.")
    args = parser.parse_args()

    result = evaluate(
        db_path=Path(args.db_path) if args.db_path else None,
        learner_id=args.learner_id,
        include_fixture=not args.no_fixture,
    )
    payload = artifact_json(result)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result.get("status") == "evaluated" else 1


if __name__ == "__main__":
    raise SystemExit(main())
