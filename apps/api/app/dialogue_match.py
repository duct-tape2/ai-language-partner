from __future__ import annotations

import csv
import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .paths import resolve_project_root

PROJECT_ROOT = resolve_project_root(Path(__file__))
PACKS_ROOT = PROJECT_ROOT / "packs"
MATCH_THRESHOLD = float(os.environ.get("AI_LANGUAGE_PARTNER_DIALOGUE_MATCH_THRESHOLD", "0.75"))
CONFIRM_THRESHOLD = float(os.environ.get("AI_LANGUAGE_PARTNER_DIALOGUE_CONFIRM_THRESHOLD", "0.55"))

_JOSA = {"は", "が", "を", "に", "で", "と", "も", "へ", "の", "ね", "よ", "か", "요", "은", "는", "이", "가", "을", "를"}
_GLOBAL_PATTERNS = {
    "repeat": [r"もう\s*一回", r"もう\s*いっかい", r"もう\s*一度", r"もう一回", r"다시", r"한\s*번\s*더"],
    "hint": [r"ヒント", r"힌트", r"도와", r"모르겠"],
    "quit": [r"やめる", r"終わり", r"그만", r"끝낼"],
    "slow": [r"ゆっくり", r"천천히", r"slow"],
}


@dataclass
class Variant:
    persona_id: str
    pack_version: str
    scenario_id: str
    node_id: str
    line_id: str
    text: str
    ko: str
    intent: str


def pack_root(persona_id: str, pack_version: str) -> Path:
    return PACKS_ROOT / persona_id / pack_version


def normalize_utterance(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "").lower()
    normalized = re.sub(r"https?://\S+", " ", normalized)
    normalized = re.sub(r"[\s、。！？!?.,;:・…~〜「」『』（）()\[\]{}\"']", "", normalized)
    normalized = normalized.replace("私", "わたし").replace("僕", "ぼく").replace("俺", "おれ")
    normalized = normalized.replace("です", "").replace("ます", "")
    return normalized.strip()


def _char_ngrams(text: str, n: int = 2) -> set[str]:
    if not text:
        return set()
    if len(text) <= n:
        return {text}
    return {text[index : index + n] for index in range(len(text) - n + 1)}


def _tokens(text: str) -> set[str]:
    normalized = normalize_utterance(text)
    tokens = {token for token in re.split(r"[\s/|]+", normalized) if token and token not in _JOSA}
    tokens.update(_char_ngrams(normalized, 2))
    return tokens


def _similarity(left: str, right: str) -> float:
    left_norm = normalize_utterance(left)
    right_norm = normalize_utterance(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    if left_norm in right_norm or right_norm in left_norm:
        return 0.88
    seq = SequenceMatcher(a=left_norm, b=right_norm).ratio()
    left_tokens = _tokens(left_norm)
    right_tokens = _tokens(right_norm)
    overlap = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    return round(max(seq * 0.92, overlap), 4)


def detect_global_intent(utterance: str) -> Optional[str]:
    normalized = normalize_utterance(utterance)
    for intent, patterns in _GLOBAL_PATTERNS.items():
        if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
            return intent
    return None


class DialogueMatcher:
    def __init__(self, packs_root: Path = PACKS_ROOT):
        self.packs_root = packs_root
        self._variant_cache: Dict[tuple[str, str], list[Variant]] = {}

    def describe(self) -> Dict[str, Any]:
        return {
            "engine": "bank",
            "matcherModel": "lexical_ngram_fallback",
            "embeddingModelConfigured": bool(os.environ.get("AI_LANGUAGE_PARTNER_DIALOGUE_EMBEDDING_MODEL")),
            "packsRoot": str(self.packs_root),
            "packVersions": list_dialogue_packs(self.packs_root),
            "runtimeLlmCalls": False,
            "thresholds": {"match": MATCH_THRESHOLD, "confirm": CONFIRM_THRESHOLD},
        }

    def match(
        self,
        persona_id: str,
        pack_version: str,
        utterance: str,
        candidate_line_ids: Iterable[str],
        global_intents: bool = True,
    ) -> Dict[str, Any]:
        started = time.perf_counter()
        global_intent = detect_global_intent(utterance) if global_intents else None
        if global_intent:
            return {
                "tier": "match",
                "matchedLineId": None,
                "score": 1.0,
                "confirmLineId": None,
                "globalIntent": global_intent,
                "latencyMs": int((time.perf_counter() - started) * 1000),
            }

        candidates = {line_id for line_id in candidate_line_ids if line_id}
        variants = self._variants(persona_id, pack_version)
        if candidates:
            variants = [variant for variant in variants if variant.line_id in candidates]

        best_variant: Optional[Variant] = None
        best_score = 0.0
        for variant in variants:
            score = max(_similarity(utterance, variant.text), _similarity(utterance, variant.ko))
            if score > best_score:
                best_score = score
                best_variant = variant

        if best_score >= MATCH_THRESHOLD and best_variant:
            tier = "match"
            matched_line_id = best_variant.line_id
            confirm_line_id = None
        elif best_score >= CONFIRM_THRESHOLD and best_variant:
            tier = "confirm"
            matched_line_id = best_variant.line_id
            confirm_line_id = f"{persona_id}_confirm_001"
        else:
            tier = "fallback"
            matched_line_id = None
            confirm_line_id = None

        return {
            "tier": tier,
            "matchedLineId": matched_line_id,
            "score": round(best_score, 4),
            "confirmLineId": confirm_line_id,
            "globalIntent": None,
            "latencyMs": int((time.perf_counter() - started) * 1000),
        }

    def _variants(self, persona_id: str, pack_version: str) -> list[Variant]:
        key = (persona_id, pack_version)
        if key in self._variant_cache:
            return self._variant_cache[key]
        path = pack_root(persona_id, pack_version) / "variants.csv"
        variants: list[Variant] = []
        if path.exists():
            with path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    variants.append(
                        Variant(
                            persona_id=str(row.get("personaId") or persona_id),
                            pack_version=str(row.get("packVersion") or pack_version),
                            scenario_id=str(row.get("scenarioId") or ""),
                            node_id=str(row.get("nodeId") or ""),
                            line_id=str(row.get("lineId") or ""),
                            text=str(row.get("text") or ""),
                            ko=str(row.get("ko") or ""),
                            intent=str(row.get("intent") or ""),
                        )
                    )
        self._variant_cache[key] = variants
        return variants


def list_dialogue_packs(packs_root: Path = PACKS_ROOT) -> list[Dict[str, Any]]:
    packs: list[Dict[str, Any]] = []
    if not packs_root.exists():
        return packs
    for persona_dir in sorted(path for path in packs_root.iterdir() if path.is_dir()):
        for version_dir in sorted(path for path in persona_dir.iterdir() if path.is_dir()):
            manifest_path = version_dir / "manifest.json"
            manifest: Dict[str, Any] = {}
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    manifest = {}
            size_bytes = sum(path.stat().st_size for path in version_dir.rglob("*") if path.is_file())
            packs.append(
                {
                    "personaId": persona_dir.name,
                    "packVersion": version_dir.name,
                    "sizeBytes": size_bytes,
                    "topics": manifest.get("topics") or [],
                    "levels": manifest.get("levels") or [],
                    "scenarioCount": manifest.get("scenarioCount") or 0,
                    "lineCount": manifest.get("lineCount") or 0,
                    "audioCount": manifest.get("audioCount") or 0,
                }
            )
    return packs
