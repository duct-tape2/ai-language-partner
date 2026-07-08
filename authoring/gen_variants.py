from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

from generate_seed_bank import AUTHORING_ROOT, build, expand_variants


def run_ollama(prompt: str, model: str) -> list[str]:
    completed = subprocess.run(
        ["ollama", "run", model, prompt],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return []
    lines = [line.strip(" -\t") for line in completed.stdout.splitlines() if line.strip()]
    return [line for line in lines if 1 <= len(line) <= 80][:15]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reviewed dialogue-bank utterance variants.")
    parser.add_argument("--use-ollama", action="store_true", help="Use local Ollama only for offline authoring drafts.")
    parser.add_argument("--model", default="qwen3.6-27b-uncensored")
    parser.add_argument("--output", default=str(AUTHORING_ROOT / "variants.csv"))
    args = parser.parse_args()

    summary = build()
    if not args.use_ollama:
        print(json.dumps({"ok": True, "mode": "deterministic", "summary": summary}, ensure_ascii=False, indent=2))
        return

    path = Path(args.output)
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    grouped: dict[str, dict] = {}
    for row in rows:
        grouped.setdefault(row["lineId"], row)

    expanded = []
    for line_id, row in grouped.items():
        prompt = (
            "日本語学習者の発話バリエーションを安全に作る。"
            "下品な内容や個人情報は禁止。各行に一つだけ。\n"
            f"基本文: {row['text']}\n韓国語意味: {row['ko']}\n"
            "韓国人学習者の助詞抜け、丁寧体/普通体混同、短縮を含めて10個。"
        )
        variants = run_ollama(prompt, args.model) or expand_variants(row["text"], row["ko"])
        for variant in variants[:15]:
            expanded.append({**row, "text": variant})

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["personaId", "packVersion", "scenarioId", "nodeId", "lineId", "text", "ko", "intent"])
        writer.writeheader()
        writer.writerows(expanded)
    print(json.dumps({"ok": True, "mode": "ollama_offline_draft", "rows": len(expanded)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
