from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.learner_model import artifact_json, review_cards_to_examples, train_evaluate_memory_model
from app.store import ApiStore, default_db_path, normalize_learner_id


def evaluate(db_path: Optional[Union[Path, str]] = None, learner_id: str = "local-dev", include_fixture: bool = True) -> dict:
    store = ApiStore(db_path or default_db_path())
    learner = normalize_learner_id(learner_id)
    cards = store.list_review_cards(learner_id=learner)
    db_examples = review_cards_to_examples(cards, source="review_cards")
    result = train_evaluate_memory_model(db_examples=db_examples, include_fixture=include_fixture)
    result.update(
        {
            "learnerId": learner,
            "reviewCardCount": len(cards),
            "reviewedDbExampleCount": len(db_examples),
            "dbPath": str(db_path or default_db_path()),
            "fixtureIncluded": bool(include_fixture),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Train/evaluate the offline learner memory model.")
    parser.add_argument("--db-path", default=None, help="SQLite database path. Defaults to AI_LANGUAGE_PARTNER_DB_PATH or app data path.")
    parser.add_argument("--learner-id", default="local-dev")
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
