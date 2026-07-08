from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "apps" / "api" / "data" / "language_partner.sqlite3"
REPORT_DIR = PROJECT_ROOT / "authoring" / "weekly_reports"


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "").lower()
    return "".join(ch for ch in value if ch.isalnum() or "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" or "\uac00" <= ch <= "\ud7a3")


def read_unmatched(db_path: Path) -> list[dict]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT persona_id, pack_version, node_id, utterance, stt_confidence, created_at
            FROM dialogue_unmatched
            WHERE status = 'new'
            ORDER BY created_at DESC
            LIMIT 1000
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
    return [dict(row) for row in rows]


def build_report(rows: list[dict]) -> dict:
    buckets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        key = (row["persona_id"], row["node_id"], normalize(row["utterance"])[:40])
        buckets[key].append(row)
    clusters = []
    for (persona_id, node_id, norm), items in buckets.items():
        utterances = Counter(item["utterance"] for item in items)
        clusters.append(
            {
                "personaId": persona_id,
                "nodeId": node_id,
                "normalized": norm,
                "count": len(items),
                "examples": [item for item, _count in utterances.most_common(5)],
                "recommendedAction": "add_variant" if len(items) >= 2 else "review",
                "approved": False,
                "targetLineId": "",
            }
        )
    clusters.sort(key=lambda item: item["count"], reverse=True)
    return {"ok": True, "unmatchedRows": len(rows), "clusterCount": len(clusters), "clusters": clusters}


def write_report(report: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / "weekly_expand_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = REPORT_DIR / "weekly_expand_report.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["personaId", "nodeId", "normalized", "count", "examples", "recommendedAction", "approved", "targetLineId"])
        writer.writeheader()
        for cluster in report["clusters"]:
            writer.writerow({**cluster, "examples": " | ".join(cluster["examples"])})
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster unmatched dialogue logs for weekly bank expansion.")
    parser.add_argument("--db", default=os.environ.get("AI_LANGUAGE_PARTNER_DB_PATH", str(DEFAULT_DB)))
    parser.add_argument("--seed-fake", type=int, default=0)
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.seed_fake:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dialogue_unmatched (
              id TEXT PRIMARY KEY,
              learner_id TEXT DEFAULT 'local-dev',
              persona_id TEXT NOT NULL,
              pack_version TEXT NOT NULL,
              node_id TEXT NOT NULL,
              utterance TEXT NOT NULL,
              stt_confidence REAL,
              status TEXT NOT NULL DEFAULT 'new',
              created_at TEXT NOT NULL
            )
            """
        )
        for index in range(args.seed_fake):
            conn.execute(
                "INSERT OR REPLACE INTO dialogue_unmatched VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (f"fake_{index}", "local-dev", "yui", "v1", "yui_today_n5_node_01", "今日はちょっと疲れた", 0.8, "new"),
            )
        conn.commit()
        conn.close()

    rows = read_unmatched(db_path)
    report = build_report(rows)
    path = write_report(report)
    print(json.dumps({"ok": True, "report": str(path), **report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
