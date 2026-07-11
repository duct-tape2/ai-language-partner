from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify_dialogue_pack_sources as verifier  # noqa: E402


def write_pack(root: Path, *, story: object | None = None, variants: list[dict[str, str]] | None = None) -> Path:
    pack = root / "yui" / "v1"
    pack.mkdir(parents=True)
    manifest = {
        "schemaVersion": "dialogue_bank_manifest_v1",
        "personaId": "yui",
        "packVersion": "v1",
        "scenarioCount": 1,
    }
    default_story = {
        "schemaVersion": "dialogue_bank_story_v1",
        "personaId": "yui",
        "packVersion": "v1",
        "scenarios": [
            {
                "scenarioId": "greeting",
                "personaId": "yui",
                "packVersion": "v1",
                "nodes": [
                    {
                        "nodeId": "node_01",
                        "assistantLineId": "yui_greeting_a01",
                        "assistantText": "こんにちは。",
                        "assistantKo": "안녕하세요.",
                        "choices": [
                            {
                                "lineId": "yui_greeting_u01",
                                "text": "こんにちは",
                                "ko": "안녕하세요",
                                "nextNodeId": "node_01",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    default_variants = [
        {
            "personaId": "yui",
            "packVersion": "v1",
            "scenarioId": "greeting",
            "nodeId": "node_01",
            "lineId": "yui_greeting_u01",
            "text": "こんにちは",
            "ko": "안녕하세요",
            "intent": "choice",
        }
    ]
    (pack / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    (pack / "story.json").write_text(json.dumps(default_story if story is None else story, ensure_ascii=False), encoding="utf-8")
    with (pack / "variants.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=verifier.REQUIRED_VARIANT_COLUMNS)
        writer.writeheader()
        writer.writerows(default_variants if variants is None else variants)
    return pack


class DialoguePackSourceValidationTest(unittest.TestCase):
    def test_repository_sources_validate(self) -> None:
        report = verifier.validate_packs(Path(__file__).resolve().parents[1] / "packs")

        self.assertTrue(report["ok"], report["errors"][:5])
        self.assertGreater(report["packCount"], 0)

    def test_rejects_invalid_story_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = write_pack(root)
            (pack / "story.json").write_text("{not valid json", encoding="utf-8")

            report = verifier.validate_packs(root)

        self.assertFalse(report["ok"])
        self.assertTrue(any("invalid JSON" in error for error in report["errors"]))

    def test_rejects_missing_story_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = write_pack(root)
            (pack / "story.json").unlink()

            report = verifier.validate_packs(root)

        self.assertFalse(report["ok"])
        self.assertTrue(any("story.json: missing file" in error for error in report["errors"]))

    def test_rejects_variant_line_outside_story(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_pack(
                root,
                variants=[
                    {
                        "personaId": "yui",
                        "packVersion": "v1",
                        "scenarioId": "greeting",
                        "nodeId": "node_01",
                        "lineId": "unknown_line",
                        "text": "こんにちは",
                        "ko": "안녕하세요",
                        "intent": "choice",
                    }
                ],
            )

            report = verifier.validate_packs(root)

        self.assertFalse(report["ok"])
        self.assertTrue(any("is not a story choice" in error for error in report["errors"]))

    def test_rejects_text_blocked_by_dialogue_safety(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = write_pack(root)
            story_path = pack / "story.json"
            story = json.loads(story_path.read_text(encoding="utf-8"))
            story["scenarios"][0]["nodes"][0]["choices"][0]["text"] = "19금 롤플레이"
            story_path.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")

            report = verifier.validate_packs(root)

        self.assertFalse(report["ok"])
        self.assertTrue(any("blocked by dialogue safety policy" in error for error in report["errors"]))
