from __future__ import annotations

import csv
import json
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTHORING_ROOT = PROJECT_ROOT / "authoring"
SCENARIO_ROOT = AUTHORING_ROOT / "scenarios"
PACKS_ROOT = PROJECT_ROOT / "packs"
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))

from app import safety  # noqa: E402


LINE_RE = re.compile(r"#line:([A-Za-z0-9_\-]+)")
KO_RE = re.compile(r"#ko:([^#]+)")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate() -> dict:
    pack_version = os.getenv("AI_LANGUAGE_PARTNER_DIALOGUE_PACK_VERSION", "v2")
    require_generated_assets = os.getenv("AI_LANGUAGE_PARTNER_VALIDATE_GENERATED_ASSETS", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    errors: list[str] = []
    line_ids: list[str] = []
    user_line_ids: set[str] = set()
    safety_checks = {"scenarioLines": 0, "variantRows": 0, "blocked": 0}
    scenario_files = sorted(SCENARIO_ROOT.glob("*/*.ink"))
    if len(scenario_files) != 30:
        fail(errors, f"expected 30 scenario .ink files, found {len(scenario_files)}")

    for path in scenario_files:
        text = path.read_text(encoding="utf-8")
        if "-> END" not in text:
            fail(errors, f"{path}: missing END")
        for lineno, line in enumerate(text.splitlines(), start=1):
            line_match = LINE_RE.search(line)
            if not line_match:
                continue
            line_id = line_match.group(1)
            line_ids.append(line_id)
            if "_u" in line_id:
                user_line_ids.add(line_id)
            ko_match = KO_RE.search(line)
            if not ko_match or not ko_match.group(1).strip():
                fail(errors, f"{path}:{lineno}: line {line_id} missing #ko")
            safety_checks["scenarioLines"] += 1
            guardrail = safety.assess_text(line)
            if guardrail.get("action") == "block":
                safety_checks["blocked"] += 1
                fail(errors, f"{path}:{lineno}: safety block for {line_id}")

    duplicates = sorted(line_id for line_id, count in Counter(line_ids).items() if count > 1)
    if duplicates:
        fail(errors, "duplicate lineIds: " + ", ".join(duplicates[:20]))

    variants_path = AUTHORING_ROOT / "variants.csv"
    if not variants_path.exists():
        fail(errors, "missing authoring/variants.csv")
        rows = []
    else:
        with variants_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    variants_by_line: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        variants_by_line[row.get("lineId", "")].append(row)
        safety_checks["variantRows"] += 1
        if safety.assess_text(row.get("text", "")).get("action") == "block":
            safety_checks["blocked"] += 1
            fail(errors, f"variant safety block: {row.get('lineId')}")

    missing_variant_lines = sorted(line_id for line_id in user_line_ids if len(variants_by_line.get(line_id, [])) < 8)
    if missing_variant_lines:
        fail(errors, "user lineIds with fewer than 8 variants: " + ", ".join(missing_variant_lines[:20]))

    pack_summaries = []
    for manifest_path in sorted(PACKS_ROOT.glob(f"*/{pack_version}/manifest.json")):
        pack_root = manifest_path.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("packVersion") != pack_version:
            fail(errors, f"{manifest_path}: packVersion mismatch")
        provider = str(manifest.get("ttsProvider") or "")
        if pack_version != "v1" and any(marker in provider.lower() for marker in ["mock", "fallback"]):
            fail(errors, f"{manifest_path}: non-live ttsProvider {provider}")
        for key in ["filler", "confirm", "fallback"]:
            if len(manifest.get(key) or []) != 5:
                fail(errors, f"{manifest_path}: expected 5 {key} lines")
        audio = manifest.get("audio") or []
        if manifest.get("audioCount") != len(audio):
            fail(errors, f"{manifest_path}: audioCount mismatch")
        for required in ["story.json", "variants.csv"]:
            if not (pack_root / required).exists():
                fail(errors, f"{pack_root}: missing {required}")
        if require_generated_assets:
            for item in audio:
                audio_path = pack_root / item["path"]
                if not audio_path.exists() or audio_path.stat().st_size == 0:
                    fail(errors, f"missing audio: {audio_path}")
            for required in ["embeddings.npy", "pack.zip"]:
                if not (pack_root / required).exists():
                    fail(errors, f"{pack_root}: missing {required}")
            zip_path = pack_root / "pack.zip"
            if zip_path.exists():
                with zipfile.ZipFile(zip_path) as archive:
                    names = set(archive.namelist())
                for required in ["story.json", "manifest.json", "variants.csv", "embeddings.npy"]:
                    if required not in names:
                        fail(errors, f"{zip_path}: missing {required} inside zip")
        pack_summaries.append(
            {
                "personaId": manifest.get("personaId"),
                "packVersion": manifest.get("packVersion"),
                "ttsProvider": manifest.get("ttsProvider"),
                "scenarioCount": manifest.get("scenarioCount"),
                "variantCount": manifest.get("variantCount"),
                "audioCount": manifest.get("audioCount"),
            }
        )

    if len(pack_summaries) != 3:
        fail(errors, f"expected 3 persona packs, found {len(pack_summaries)}")
    if sum(int(item.get("scenarioCount") or 0) for item in pack_summaries) != 30:
        fail(errors, "pack scenario total is not 30")

    report = {
        "ok": not errors,
        "errors": errors,
        "packVersion": pack_version,
        "generatedAssetChecks": "required" if require_generated_assets else "skipped",
        "scenarioFiles": len(scenario_files),
        "lineIds": len(line_ids),
        "userLineIds": len(user_line_ids),
        "variants": len(rows),
        "safetyGate": {
            "gate": "app.safety.assess_text",
            "checkedScenarioLines": safety_checks["scenarioLines"],
            "checkedVariantRows": safety_checks["variantRows"],
            "blockedTexts": safety_checks["blocked"],
            "status": "passed" if safety_checks["blocked"] == 0 else "blocked",
        },
        "packs": pack_summaries,
    }
    return report


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)
