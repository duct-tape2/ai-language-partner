from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKS_ROOT = PROJECT_ROOT / "packs"
APP_DIR = PROJECT_ROOT / "apps" / "api" / "app"
DEFAULT_ENGINE_URL = "http://127.0.0.1:10101"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def line_texts_from_story(story: dict) -> dict[str, str]:
    texts: dict[str, str] = {}
    for scenario in story.get("scenarios") or []:
        scenario["packVersion"] = story.get("packVersion", scenario.get("packVersion"))
        for node in scenario.get("nodes") or []:
            if node.get("assistantLineId") and node.get("assistantText"):
                texts[node["assistantLineId"]] = node["assistantText"]
    return texts


def voice_catalog() -> dict[str, dict]:
    return {voice["voiceId"]: voice for voice in load_json(APP_DIR / "voice_catalog.json")}


def persona_voice_map() -> dict[str, dict]:
    return load_json(APP_DIR / "persona_voices.json")


def synthesize(engine_url: str, text: str, voice: dict, out_path: Path) -> dict:
    started = time.perf_counter()
    style_id = int(voice["engineStyleId"])
    query_url = f"{engine_url.rstrip('/')}/audio_query?text={urllib.parse.quote(text)}&speaker={style_id}"
    query_req = urllib.request.Request(query_url, data=b"", method="POST")
    with urllib.request.urlopen(query_req, timeout=30) as response:
        query = json.loads(response.read().decode("utf-8"))
    query["speedScale"] = float(voice.get("speedScale") or query.get("speedScale") or 1.0)
    query["pitchScale"] = float(voice.get("pitchScale") if voice.get("pitchScale") is not None else query.get("pitchScale") or 0.0)
    query["intonationScale"] = float(voice.get("intonationScale") if voice.get("intonationScale") is not None else query.get("intonationScale") or 1.0)
    query["volumeScale"] = float(voice.get("volumeScale") if voice.get("volumeScale") is not None else query.get("volumeScale") or 1.0)
    body = json.dumps(query, ensure_ascii=False).encode("utf-8")
    synth_req = urllib.request.Request(
        f"{engine_url.rstrip('/')}/synthesis?speaker={style_id}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(synth_req, timeout=90) as response:
        raw_wav = response.read()
    if not raw_wav:
        raise RuntimeError(f"empty synthesis for {voice['voiceId']}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(raw_wav)
    try:
        ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        subprocess.run(
            [ffmpeg, "-y", "-i", str(tmp_path), "-af", "loudnorm=I=-18:LRA=11:TP=-1.5", str(out_path)],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except Exception:
        out_path.write_bytes(raw_wav)
    finally:
        tmp_path.unlink(missing_ok=True)
    return {
        "voiceUsed": voice["voiceId"],
        "engineStyleId": voice["engineStyleId"],
        "characterName": voice["characterName"],
        "styleName": voice["styleName"],
        "bytes": out_path.stat().st_size,
        "latencyMs": int((time.perf_counter() - started) * 1000),
    }


def update_variants(source: Path, dest: Path, pack_version: str) -> int:
    rows = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            row["packVersion"] = pack_version
            rows.append(row)
    with dest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["personaId", "packVersion", "scenarioId", "nodeId", "lineId", "text", "ko", "intent"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_pack(persona_id: str, source_version: str, pack_version: str, engine_url: str, dry_run: bool) -> dict:
    source_root = PACKS_ROOT / persona_id / source_version
    dest_root = PACKS_ROOT / persona_id / pack_version
    if not source_root.exists():
        raise FileNotFoundError(source_root)
    if dest_root.exists() and not dry_run:
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    catalog = voice_catalog()
    persona_voices = persona_voice_map()
    persona_map = persona_voices[persona_id]
    story = load_json(source_root / "story.json")
    story["packVersion"] = pack_version
    for scenario in story.get("scenarios") or []:
        scenario["packVersion"] = pack_version
    text_by_line = line_texts_from_story(story)
    source_manifest = load_json(source_root / "manifest.json")
    for key in ["filler", "confirm", "fallback"]:
        for item in source_manifest.get(key) or []:
            if item.get("lineId") and item.get("text"):
                text_by_line[item["lineId"]] = item["text"]

    if not dry_run:
        write_json(dest_root / "story.json", story)
        shutil.copy2(source_root / "embeddings.npy", dest_root / "embeddings.npy")
        variant_count = update_variants(source_root / "variants.csv", dest_root / "variants.csv", pack_version)
    else:
        variant_count = sum(1 for _ in (source_root / "variants.csv").open("r", encoding="utf-8")) - 1

    audio_items = []
    synth_summary = []
    for item in source_manifest.get("audio") or []:
        category = item.get("category") or "dialogue"
        line_id = item["lineId"]
        text = text_by_line.get(line_id)
        if not text:
            raise RuntimeError(f"missing text for {line_id}")
        emotion = "default"
        if category == "confirm":
            emotion = "confirm"
        elif category == "fallback":
            emotion = "fallback"
        elif category == "filler":
            emotion = "gentle"
        voice_id = persona_map.get("emotions", {}).get(emotion) or persona_map["defaultVoiceId"]
        voice = catalog[voice_id]
        rel_path = Path("audio") / f"{line_id}.wav"
        out_path = dest_root / rel_path
        result = {"voiceUsed": voice_id, "engineStyleId": voice["engineStyleId"], "characterName": voice["characterName"], "styleName": voice["styleName"]}
        if not dry_run:
            result = synthesize(engine_url, text, voice, out_path)
        updated = {**item, "path": str(rel_path), "text": text, "voiceUsed": voice_id, "engine": "aivis_speech"}
        audio_items.append(updated)
        synth_summary.append({"lineId": line_id, "category": category, **result})

    manifest = {
        **source_manifest,
        "packVersion": pack_version,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtimeLlmCalls": False,
        "ttsProvider": "aivis_speech_engine",
        "engineBaseUrl": engine_url,
        "sourcePackVersion": source_version,
        "voiceUsed": persona_map["defaultVoiceId"],
        "variantCount": variant_count,
        "audio": audio_items,
        "filler": [item for item in audio_items if item.get("category") == "filler"],
        "confirm": [item for item in audio_items if item.get("category") == "confirm"],
        "fallback": [item for item in audio_items if item.get("category") == "fallback"],
    }
    if not dry_run:
        write_json(dest_root / "manifest.json", manifest)
        with zipfile.ZipFile(dest_root / "pack.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(p for p in dest_root.rglob("*") if p.is_file() and p.name != "pack.zip"):
                archive.write(path, path.relative_to(dest_root))
    return {
        "personaId": persona_id,
        "sourceVersion": source_version,
        "packVersion": pack_version,
        "dryRun": dry_run,
        "audioCount": len(audio_items),
        "variantCount": variant_count,
        "voicesUsed": sorted({item["voiceUsed"] for item in audio_items}),
        "synthesis": synth_summary,
        "packBytes": (dest_root / "pack.zip").stat().st_size if (dest_root / "pack.zip").exists() else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch synthesize dialogue-bank audio with the running Aivis/VOICEVOX-compatible engine.")
    parser.add_argument("--persona", default=None)
    parser.add_argument("--source-version", default="v1")
    parser.add_argument("--pack-version", default="v2")
    parser.add_argument("--engine-url", default=DEFAULT_ENGINE_URL)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    personas = [args.persona] if args.persona else sorted(path.name for path in PACKS_ROOT.iterdir() if (path / args.source_version).exists())
    results = [build_pack(persona, args.source_version, args.pack_version, args.engine_url, args.dry_run) for persona in personas]
    summary = {
        "ok": True,
        "engineUrl": args.engine_url,
        "dryRun": args.dry_run,
        "sourceVersion": args.source_version,
        "packVersion": args.pack_version,
        "personas": personas,
        "totalAudio": sum(item["audioCount"] for item in results),
        "results": results,
    }
    evidence_path = PROJECT_ROOT / "artifacts" / "backend" / f"batch_tts_{args.pack_version}.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    printable = {**summary, "results": [{k: v for k, v in item.items() if k != "synthesis"} for item in results]}
    print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
