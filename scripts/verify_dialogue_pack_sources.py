#!/usr/bin/env python3
"""Validate checked-in dialogue-pack JSON and CSV sources.

This intentionally validates source files only. Generated audio, archives, and
local speech engines stay outside the public contribution path.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app import safety  # noqa: E402


REQUIRED_VARIANT_COLUMNS = (
    "personaId",
    "packVersion",
    "scenarioId",
    "nodeId",
    "lineId",
    "text",
    "ko",
    "intent",
)


def is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_object(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path}: missing file")
        return None
    except json.JSONDecodeError as error:
        errors.append(f"{path}: invalid JSON ({error.msg})")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path}: expected a JSON object")
        return None
    return value


def validate_safe_text(value: object, location: str, errors: list[str]) -> None:
    if not is_nonempty_text(value):
        errors.append(f"{location}: expected non-empty text")
        return
    result = safety.assess_text(str(value))
    if result.get("action") == "block":
        errors.append(f"{location}: blocked by dialogue safety policy")


def validate_pack(pack_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    persona_id = pack_dir.parent.name
    pack_version = pack_dir.name
    manifest = load_object(pack_dir / "manifest.json", errors)
    story = load_object(pack_dir / "story.json", errors)

    if manifest is not None:
        if manifest.get("schemaVersion") != "dialogue_bank_manifest_v1":
            errors.append(f"{pack_dir / 'manifest.json'}: unexpected schemaVersion")
        if manifest.get("personaId") != persona_id:
            errors.append(f"{pack_dir / 'manifest.json'}: personaId does not match directory")
        if manifest.get("packVersion") != pack_version:
            errors.append(f"{pack_dir / 'manifest.json'}: packVersion does not match directory")

    scenario_nodes: dict[str, set[str]] = {}
    choice_line_ids: set[str] = set()
    choice_locations: dict[str, tuple[str, str]] = {}
    assistant_line_ids: list[str] = []
    scenario_count = 0
    if story is not None:
        if story.get("schemaVersion") != "dialogue_bank_story_v1":
            errors.append(f"{pack_dir / 'story.json'}: unexpected schemaVersion")
        if story.get("personaId") != persona_id:
            errors.append(f"{pack_dir / 'story.json'}: personaId does not match directory")
        if story.get("packVersion") != pack_version:
            errors.append(f"{pack_dir / 'story.json'}: packVersion does not match directory")
        scenarios = story.get("scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            errors.append(f"{pack_dir / 'story.json'}: expected a non-empty scenarios list")
            scenarios = []
        scenario_ids: set[str] = set()
        for scenario_index, scenario in enumerate(scenarios, 1):
            location = f"{pack_dir / 'story.json'}: scenarios[{scenario_index}]"
            if not isinstance(scenario, dict):
                errors.append(f"{location}: expected an object")
                continue
            scenario_id = scenario.get("scenarioId")
            if not is_nonempty_text(scenario_id):
                errors.append(f"{location}: expected scenarioId")
                continue
            scenario_id = str(scenario_id)
            if scenario_id in scenario_ids:
                errors.append(f"{location}: duplicate scenarioId {scenario_id}")
                continue
            scenario_ids.add(scenario_id)
            scenario_count += 1
            for key, expected in (("personaId", persona_id), ("packVersion", pack_version)):
                if scenario.get(key) != expected:
                    errors.append(f"{location}: {key} does not match directory")
            nodes = scenario.get("nodes")
            if not isinstance(nodes, list) or not nodes:
                errors.append(f"{location}: expected a non-empty nodes list")
                continue
            node_ids: set[str] = set()
            next_nodes: list[tuple[str, str]] = []
            for node_index, node in enumerate(nodes, 1):
                node_location = f"{location}.nodes[{node_index}]"
                if not isinstance(node, dict):
                    errors.append(f"{node_location}: expected an object")
                    continue
                node_id = node.get("nodeId")
                if not is_nonempty_text(node_id):
                    errors.append(f"{node_location}: expected nodeId")
                    continue
                node_id = str(node_id)
                if node_id in node_ids:
                    errors.append(f"{node_location}: duplicate nodeId {node_id}")
                    continue
                node_ids.add(node_id)
                assistant_line_id = node.get("assistantLineId")
                if not is_nonempty_text(assistant_line_id):
                    errors.append(f"{node_location}: expected assistantLineId")
                else:
                    assistant_line_ids.append(str(assistant_line_id))
                validate_safe_text(node.get("assistantText"), f"{node_location}.assistantText", errors)
                validate_safe_text(node.get("assistantKo"), f"{node_location}.assistantKo", errors)
                choices = node.get("choices")
                if not isinstance(choices, list) or not choices:
                    errors.append(f"{node_location}: expected a non-empty choices list")
                    continue
                for choice_index, choice in enumerate(choices, 1):
                    choice_location = f"{node_location}.choices[{choice_index}]"
                    if not isinstance(choice, dict):
                        errors.append(f"{choice_location}: expected an object")
                        continue
                    line_id = choice.get("lineId")
                    if not is_nonempty_text(line_id):
                        errors.append(f"{choice_location}: expected lineId")
                    else:
                        line_id = str(line_id)
                        if line_id in choice_line_ids:
                            errors.append(f"{choice_location}: duplicate choice lineId {line_id}")
                        else:
                            choice_locations[line_id] = (scenario_id, node_id)
                        choice_line_ids.add(line_id)
                    validate_safe_text(choice.get("text"), f"{choice_location}.text", errors)
                    validate_safe_text(choice.get("ko"), f"{choice_location}.ko", errors)
                    next_node_id = choice.get("nextNodeId")
                    if not is_nonempty_text(next_node_id):
                        errors.append(f"{choice_location}: expected nextNodeId")
                    else:
                        next_nodes.append((choice_location, str(next_node_id)))
            for choice_location, next_node_id in next_nodes:
                if next_node_id != "END" and next_node_id not in node_ids:
                    errors.append(f"{choice_location}: nextNodeId {next_node_id} is not in scenario {scenario_id}")
            scenario_nodes[scenario_id] = node_ids

    duplicate_assistant_ids = sorted(line_id for line_id, count in Counter(assistant_line_ids).items() if count > 1)
    if duplicate_assistant_ids:
        errors.append(f"{pack_dir / 'story.json'}: duplicate assistantLineId values: {', '.join(duplicate_assistant_ids[:5])}")

    variants_path = pack_dir / "variants.csv"
    variant_line_ids: set[str] = set()
    variant_rows = 0
    if not variants_path.exists():
        errors.append(f"{variants_path}: missing file")
    else:
        with variants_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = set(reader.fieldnames or [])
            missing_headers = [column for column in REQUIRED_VARIANT_COLUMNS if column not in headers]
            if missing_headers:
                errors.append(f"{variants_path}: missing columns: {', '.join(missing_headers)}")
            for row_number, row in enumerate(reader, 2):
                variant_rows += 1
                location = f"{variants_path}:{row_number}"
                if any(not is_nonempty_text(row.get(column)) for column in REQUIRED_VARIANT_COLUMNS):
                    errors.append(f"{location}: required column is blank")
                    continue
                if row["personaId"] != persona_id or row["packVersion"] != pack_version:
                    errors.append(f"{location}: personaId or packVersion does not match directory")
                if row["scenarioId"] not in scenario_nodes:
                    errors.append(f"{location}: unknown scenarioId {row['scenarioId']}")
                elif row["nodeId"] not in scenario_nodes[row["scenarioId"]]:
                    errors.append(f"{location}: unknown nodeId {row['nodeId']}")
                if row["lineId"] not in choice_line_ids:
                    errors.append(f"{location}: lineId {row['lineId']} is not a story choice")
                elif choice_locations[row["lineId"]] != (row["scenarioId"], row["nodeId"]):
                    errors.append(
                        f"{location}: lineId {row['lineId']} does not match the story scenarioId/nodeId"
                    )
                variant_line_ids.add(row["lineId"])
                validate_safe_text(row["text"], f"{location}.text", errors)
                validate_safe_text(row["ko"], f"{location}.ko", errors)

    missing_variants = sorted(choice_line_ids - variant_line_ids)
    if missing_variants:
        errors.append(f"{variants_path}: choice lineIds without variants: {', '.join(missing_variants[:5])}")
    if manifest is not None and isinstance(manifest.get("scenarioCount"), int) and manifest["scenarioCount"] != scenario_count:
        errors.append(f"{pack_dir / 'manifest.json'}: scenarioCount does not match story")

    return {
        "pack": str(pack_dir.relative_to(ROOT)) if pack_dir.is_relative_to(ROOT) else str(pack_dir),
        "ok": not errors,
        "errors": errors,
        "scenarioCount": scenario_count,
        "choiceLineCount": len(choice_line_ids),
        "variantRowCount": variant_rows,
    }


def validate_packs(packs_root: Path) -> dict[str, Any]:
    if not packs_root.is_dir():
        return {
            "ok": False,
            "packCount": 0,
            "packs": [],
            "errors": [f"{packs_root}: missing packs directory"],
        }
    pack_dirs = sorted(
        version_dir
        for persona_dir in packs_root.iterdir()
        if persona_dir.is_dir()
        for version_dir in persona_dir.iterdir()
        if version_dir.is_dir()
    )
    reports = [validate_pack(pack_dir) for pack_dir in pack_dirs]
    errors = [error for report in reports for error in report["errors"]]
    return {"ok": not errors, "packCount": len(reports), "packs": reports, "errors": errors}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packs-root", type=Path, default=ROOT / "packs")
    args = parser.parse_args(argv[1:])
    report = validate_packs(args.packs_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
