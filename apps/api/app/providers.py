from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from . import safety

STRUCTURED_TURN_SCHEMA_VERSION = "turn_payload_v1"
APP_DIR = Path(__file__).resolve().parent


def estimate_tokens(text: Optional[str]) -> int:
    if not text:
        return 0
    return max(1, len(text) // 2)


def tts_cache_key(text: str, persona_id: str, language: str, speed: Optional[float], emotion: Optional[str], provider: str = "mock") -> str:
    raw = f"{provider}\n{persona_id}\n{language}\n{speed or 1.0}\n{emotion or ''}\n{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_json_asset(name: str, fallback: Any) -> Any:
    path = APP_DIR / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def load_voice_catalog() -> list[Dict[str, Any]]:
    catalog = _load_json_asset("voice_catalog.json", [])
    return catalog if isinstance(catalog, list) else []


def load_persona_voice_map() -> Dict[str, Any]:
    mapping = _load_json_asset("persona_voices.json", {})
    return mapping if isinstance(mapping, dict) else {}


def voice_for_request(request: Dict[str, Any]) -> Dict[str, Any]:
    persona_id = str(request.get("personaId") or "yui")
    emotion = str(request.get("emotion") or "default")
    voice_map = load_persona_voice_map()
    persona_voice = voice_map.get(persona_id) or voice_map.get("yui") or {}
    emotion_map = persona_voice.get("emotions") or {}
    voice_id = (
        emotion_map.get(emotion)
        or emotion_map.get("default")
        or persona_voice.get("defaultVoiceId")
        or f"mock_{persona_id}_{emotion}"
    )
    catalog = {str(item.get("voiceId")): item for item in load_voice_catalog()}
    selected = dict(catalog.get(str(voice_id)) or {})
    selected.setdefault("voiceId", str(voice_id))
    selected.setdefault("engine", "mock")
    selected.setdefault("personaId", persona_id)
    selected.setdefault("characterName", persona_voice.get("displayName") or persona_id)
    selected.setdefault("styleName", emotion)
    selected.setdefault("creditText", "Local mock voice")
    return selected


def _mock_wav_base64(duration_ms: int = 680, sample_rate: int = 16000, frequency: float = 440.0) -> str:
    frames = int(sample_rate * duration_ms / 1000)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        samples = bytearray()
        for index in range(frames):
            envelope = min(1.0, index / 1200) * min(1.0, (frames - index) / 1800)
            tone = math.sin(2 * math.pi * frequency * index / sample_rate)
            overtone = 0.35 * math.sin(2 * math.pi * (frequency * 1.5) * index / sample_rate)
            value = int(14000 * envelope * (tone + overtone) / 1.35)
            samples.extend(value.to_bytes(2, "little", signed=True))
        wav.writeframes(bytes(samples))
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class MockTTSProvider:
    provider = "mock"
    external_configured = False
    replaceable = True

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "externalConfigured": self.external_configured,
            "replaceable": self.replaceable,
            "personaVoices": sorted(load_persona_voice_map().keys()),
            "voiceCatalogSize": len(load_voice_catalog()),
        }

    def voice_used_for(self, request: Dict[str, Any]) -> str:
        return str(voice_for_request(request).get("voiceId") or "mock")

    def synthesize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        text = request["text"]
        voice = voice_for_request(request)
        voice_hash = int(hashlib.sha256(str(voice.get("voiceId")).encode("utf-8")).hexdigest()[:8], 16)
        speed = float(request.get("speed") or 1.0)
        frequency = 330.0 + (voice_hash % 260)
        duration_ms = max(700, min(6200, int(len(text) * 140 / max(0.5, min(speed, 1.8)))))
        audio_base64 = _mock_wav_base64(duration_ms=duration_ms, frequency=frequency)
        return {
            "audioUrl": "data:audio/wav;base64," + audio_base64,
            "audioBase64": audio_base64,
            "provider": self.provider,
            "cacheHit": False,
            "spokenText": text,
            "durationMs": duration_ms,
            "latencyMs": int((time.perf_counter() - started) * 1000),
            "voiceUsed": str(voice.get("voiceId")),
            "voice": voice,
        }


class MockSTTProvider:
    provider = "mock"
    external_configured = False
    replaceable = True

    def describe(self) -> Dict[str, Any]:
        return {"active": self.provider, "externalConfigured": self.external_configured, "replaceable": self.replaceable}

    def transcribe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        transcript = request.get("mockText") or request.get("text") or "今日めっちゃ疲れた"
        return {
            "text": transcript,
            "provider": self.provider,
            "confidence": 0.92,
            "sttSeconds": float(request.get("durationSeconds") or 2.0),
            "latencyMs": int((time.perf_counter() - started) * 1000),
        }


class MockPronunciationScorer:
    provider = "mock"
    external_configured = False
    replaceable = True

    def describe(self) -> Dict[str, Any]:
        return {"active": self.provider, "externalConfigured": self.external_configured, "replaceable": self.replaceable}

    def score(self, expected_text: str, actual_text: str, audio_base64: Optional[str] = None) -> Dict[str, Any]:
        expected_units = _speech_units(expected_text)
        actual_units = _speech_units(actual_text)
        expected_set = set(expected_units)
        actual_set = set(actual_units)
        matched = [unit for unit in expected_units if unit in actual_set]
        missing = [unit for unit in expected_units if unit not in actual_set]
        extra = [unit for unit in actual_units if unit not in expected_set]
        coverage = len(matched) / max(1, len(expected_units))
        penalty = min(0.25, len(extra) / max(8, len(expected_units)) * 0.1)
        score = max(0, min(100, round((coverage - penalty) * 100)))
        rating = "excellent" if score >= 90 else "good" if score >= 75 else "needs_practice" if score >= 55 else "retry"
        feedback = "좋아. 리듬은 거의 맞고, 빠진 소리만 짧게 다시 잡으면 돼."
        if rating == "excellent":
            feedback = "아주 좋아. 실제 대화에서 바로 써도 될 정도로 자연스러워."
        elif rating == "retry":
            feedback = "문장 전체보다 짧은 단위로 다시 따라 해보자. 먼저 めっちゃ疲れた 부분만 잡으면 좋아."
        elif missing:
            feedback = f"{'、'.join(missing[:3])} 소리가 빠졌어. 그 부분만 한 번 더 또렷하게 말해봐."
        return {
            "provider": self.provider,
            "expectedText": expected_text,
            "actualText": actual_text,
            "score": score,
            "rating": rating,
            "scoringMode": "text_overlap_mock",
            "acousticEvidencePresent": False,
            "matchedUnits": matched,
            "missingUnits": missing,
            "extraUnits": extra,
            "feedbackKo": feedback,
        }


class AcousticFeaturePronunciationScorer(MockPronunciationScorer):
    provider = "acoustic_feature_mock"

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "externalConfigured": False,
            "replaceable": True,
            "acousticFeatures": ["durationMs", "sampleRate", "rms", "zeroCrossingRate", "voicedRatio"],
            "fallback": "text_overlap_mock",
        }

    def score(self, expected_text: str, actual_text: str, audio_base64: Optional[str] = None) -> Dict[str, Any]:
        base = super().score(expected_text, actual_text)
        if not audio_base64:
            base["provider"] = self.provider
            base["scoringMode"] = "text_overlap_fallback_no_audio"
            base["acousticEvidencePresent"] = False
            return base

        features = _wav_features(audio_base64)
        if not features["ok"]:
            base["provider"] = self.provider
            base["scoringMode"] = "text_overlap_fallback_invalid_audio"
            base["acousticEvidencePresent"] = False
            base["acousticError"] = features["error"]
            return base

        expected_duration_ms = max(650, min(7000, len(_speech_units(expected_text)) * 180))
        duration_ratio = min(features["durationMs"], expected_duration_ms) / max(features["durationMs"], expected_duration_ms)
        energy_score = 1.0 if features["rms"] >= 0.04 else max(0.35, features["rms"] / 0.04)
        voicing_score = min(1.0, features["voicedRatio"] / 0.55) if features["voicedRatio"] else 0.35
        acoustic_score = round((duration_ratio * 0.45 + energy_score * 0.30 + voicing_score * 0.25) * 100)
        combined = round(base["score"] * 0.65 + acoustic_score * 0.35)
        rating = "excellent" if combined >= 90 else "good" if combined >= 75 else "needs_practice" if combined >= 55 else "retry"
        feedback = base["feedbackKo"]
        if features["durationMs"] < expected_duration_ms * 0.55:
            feedback = "문장이 너무 짧게 끊겼어. 마지막까지 소리를 이어서 다시 말해봐."
        elif features["rms"] < 0.035:
            feedback = "소리가 너무 작아. 같은 문장을 조금 더 또렷하게 말해봐."
        elif rating == "excellent":
            feedback = "텍스트 일치와 음성 길이/에너지 모두 좋아. 실제 대화 연습용으로 충분히 자연스러워."
        return {
            **base,
            "provider": self.provider,
            "score": max(0, min(100, combined)),
            "rating": rating,
            "feedbackKo": feedback,
            "scoringMode": "text_plus_acoustic_features",
            "acousticEvidencePresent": True,
            "acousticScore": acoustic_score,
            "acousticFeatures": features,
        }


class MockLLMProvider:
    provider = "mock"
    external_configured = False
    replaceable = True

    def describe(self) -> Dict[str, Any]:
        return {"active": self.provider, "externalConfigured": self.external_configured, "replaceable": self.replaceable}

    def generate_turn(self, persona: Dict[str, Any], room: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        started = time.perf_counter()
        guardrail = safety.assess_text(user_text)
        if guardrail["action"] == "block":
            assistant_text = str(guardrail["message"])
            return {
                "blocked": True,
                "safety": guardrail,
                "assistantText": assistant_text,
                "spokenText": room.get("primaryPhraseJa", "今日めっちゃ疲れた") + "。",
                "suggestedUserReply": room.get("primaryPhraseJa", "今日めっちゃ疲れた") + "。",
                "corrections": [],
                "reviewCards": [],
                "usage": self._usage(started, user_text, assistant_text),
            }

        normalized_text = str(guardrail.get("transformedText") or user_text)
        corrections = self._corrections_for(normalized_text, room)
        if guardrail["action"] == "transform":
            corrections.append(
                {
                    "category": "cultural_nuance",
                    "original": user_text,
                    "corrected": normalized_text,
                    "explanationKo": str(guardrail["message"]),
                    "severity": "important",
                    "isKoreanLiteral": False,
                }
            )

        primary_ja = room.get("primaryPhraseJa", "今日めっちゃ疲れた")
        spoken_text = primary_ja if primary_ja.endswith("。") else primary_ja + "。"
        alternatives = room.get("alternativePhrasesJa") or ["今日はすごく疲れた", "今日ちょっとしんどい"]
        assistant_text = (
            f"{persona.get('displayName', '유이')}가 자연스럽게 잡아줄게. "
            f"친구한테는 「{primary_ja}」라고 하면 좋아. "
            f"조금 더 무난하게는 「{alternatives[0]}」도 괜찮아. "
            "먼저 내가 말해볼게. 잘 듣고 그대로 따라 해봐."
        )
        if corrections:
            first = corrections[0]
            assistant_text += f" 교정 포인트는 {first['original']} -> {first['corrected']}야."

        card = {
            "front": room.get("primaryPhraseKo", "오늘 너무 피곤했어"),
            "back": spoken_text,
            "example": f"A: 今日どうだった？ B: {spoken_text}",
            "tags": room.get("tags", ["감정표현", "친구말투", "일상"]),
        }
        return {
            "blocked": False,
            "safety": guardrail,
            "assistantText": assistant_text,
            "spokenText": spoken_text,
            "suggestedUserReply": spoken_text,
            "corrections": corrections,
            "reviewCards": [card],
            "usage": self._usage(started, user_text, assistant_text),
        }

    def _corrections_for(self, text: str, room: Dict[str, Any]) -> list[Dict[str, Any]]:
        if "疲れるだった" in text or "今日は疲れる" in text:
            return [
                {
                    "category": "verb_tense",
                    "original": "今日は疲れるだった" if "疲れるだった" in text else text,
                    "corrected": "今日は疲れた",
                    "explanationKo": "疲れる는 현재/미래 느낌이라 오늘 이미 피곤했다는 말에는 과거형 疲れた가 자연스러워요.",
                    "severity": "important",
                    "isKoreanLiteral": True,
                }
            ]

        primary_ko = room.get("primaryPhraseKo", "")
        primary_ja = room.get("primaryPhraseJa", "今日めっちゃ疲れた")
        spoken = primary_ja if primary_ja.endswith("。") else primary_ja + "。"
        if "피곤" in text or primary_ko in text:
            return [
                {
                    "category": "naturalness",
                    "original": text,
                    "corrected": spoken,
                    "explanationKo": "한국어를 단어 그대로 옮기기보다 친구 사이에서 바로 쓰는 짧은 일본어 표현으로 잡는 게 자연스러워요.",
                    "severity": "minor",
                    "isKoreanLiteral": False,
                }
            ]

        if "お前" in text:
            return [
                {
                    "category": "register",
                    "original": "お前",
                    "corrected": "君 / あなた / 이름",
                    "explanationKo": "お前는 현실 대화에서 거칠게 들릴 수 있어요. 친한 사이라도 이름이나 더 부드러운 표현이 안전합니다.",
                    "severity": "important",
                    "isKoreanLiteral": False,
                }
            ]

        return []

    def _usage(self, started: float, input_text: str, output_text: str) -> Dict[str, Any]:
        return {
            "llmInputTokens": estimate_tokens(input_text),
            "llmOutputTokens": estimate_tokens(output_text),
            "latencyMs": int((time.perf_counter() - started) * 1000),
        }


def _speech_units(text: str) -> list[str]:
    normalized = "".join(ch for ch in (text or "") if ch.isalnum() or "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff")
    if not normalized:
        return []
    if any("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in normalized):
        return list(normalized)
    return normalized.lower().split()


def _wav_features(audio_base64: str) -> Dict[str, Any]:
    try:
        audio, _content_type = decode_audio_payload(audio_base64)
        with wave.open(io.BytesIO(audio), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            frame_count = wav.getnframes()
            frames = wav.readframes(frame_count)
        if sample_width != 2:
            return {"ok": False, "error": f"unsupported_sample_width_{sample_width}"}
        samples = []
        step = max(1, channels)
        for index in range(0, len(frames), sample_width * channels):
            value = int.from_bytes(frames[index : index + sample_width], "little", signed=True)
            samples.append(value / 32768.0)
        if not samples:
            return {"ok": False, "error": "empty_audio"}
        rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
        crossings = sum(1 for prev, cur in zip(samples, samples[1:]) if (prev < 0 <= cur) or (prev >= 0 > cur))
        voiced = sum(1 for sample in samples if abs(sample) > 0.015)
        return {
            "ok": True,
            "durationMs": round(frame_count / max(1, sample_rate) * 1000),
            "sampleRate": sample_rate,
            "channels": channels,
            "rms": round(rms, 5),
            "zeroCrossingRate": round(crossings / max(1, len(samples) - 1), 5),
            "voicedRatio": round(voiced / len(samples), 5),
        }
    except Exception as exc:
        return {"ok": False, "error": exc.__class__.__name__}


def decode_audio_payload(audio_base64: str, default_content_type: str = "audio/wav") -> Tuple[bytes, str]:
    if not audio_base64:
        return b"", default_content_type
    value = audio_base64.strip()
    if value.startswith("data:"):
        header, payload = value.split(",", 1)
        content_type = header[5:].split(";", 1)[0] or default_content_type
        return base64.b64decode(payload, validate=False), content_type
    return base64.b64decode(value, validate=False), default_content_type


def _audio_extension(content_type: str) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    mapping = {
        "audio/wav": "wav",
        "audio/wave": "wav",
        "audio/x-wav": "wav",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/mp4": "m4a",
        "audio/m4a": "m4a",
        "audio/x-m4a": "m4a",
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "video/mp4": "mp4",
    }
    return mapping.get(normalized, "audio")


def _which(name: str) -> Optional[str]:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        path = os.path.join(directory, name)
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    return None


def _initial_prompt_from_hints(request: Dict[str, Any]) -> str:
    hints = request.get("hintLineIds") or request.get("hints") or []
    if isinstance(hints, str):
        hints = [part.strip() for part in hints.split(",") if part.strip()]
    if not isinstance(hints, list):
        return ""
    return "。".join(str(item) for item in hints[:12] if item)


class OpenAICompatibleLLMProvider(MockLLMProvider):
    provider = "openai_compatible"
    external_configured = True

    def __init__(self, api_key: str, base_url: str, model: str, repair_attempts: int = 2, response_format_mode: str = "json_object"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.repair_attempts = min(3, max(0, int(repair_attempts)))
        self.response_format_mode = response_format_mode
        self._fallback = MockLLMProvider()

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "externalConfigured": bool(self.api_key),
            "replaceable": True,
            "baseUrl": self.base_url,
            "model": self.model,
            "structuredOutputSchemaVersion": STRUCTURED_TURN_SCHEMA_VERSION,
            "structuredOutputRepairAttempts": self.repair_attempts,
            "responseFormatMode": self.response_format_mode,
            "secretsReturned": False,
        }

    def generate_turn(self, persona: Dict[str, Any], room: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        fallback = self._fallback.generate_turn(persona, room, user_text)
        response_schema = _structured_turn_json_schema()
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Korean-first Japanese conversation coach. "
                        "Return concise Korean guidance and natural Japanese. "
                        "Never impersonate real people or copyrighted characters. "
                        f"Return schemaVersion={STRUCTURED_TURN_SCHEMA_VERSION}. "
                        "Return a JSON object with schemaVersion, assistantTextKo, spokenTextJa, "
                        "suggestedUserReplyJa, corrections, and reviewCards."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "persona": persona,
                            "practiceRoom": room,
                            "learnerText": user_text,
                            "expectedOutputSchemaVersion": STRUCTURED_TURN_SCHEMA_VERSION,
                            "expectedOutputJsonSchema": response_schema,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "temperature": 0.4,
            "response_format": _llm_response_format(self.response_format_mode, response_schema),
        }
        parsed: Any = None
        try:
            data = _post_json(f"{self.base_url}/chat/completions", payload, self.api_key, timeout=20)
            parsed = _parse_json_object(data["choices"][0]["message"]["content"])
        except Exception as exc:
            fallback["providerWarning"] = f"{self.provider}_fallback:{exc.__class__.__name__}"
            return fallback

        normalized, validation_error = _normalize_structured_turn_payload(parsed)
        repaired = False
        for _attempt in range(self.repair_attempts):
            if normalized:
                break
            try:
                repair_payload = _repair_payload(payload, parsed, validation_error)
                data = _post_json(f"{self.base_url}/chat/completions", repair_payload, self.api_key, timeout=20)
                parsed = _parse_json_object(data["choices"][0]["message"]["content"])
                normalized, validation_error = _normalize_structured_turn_payload(parsed)
                repaired = bool(normalized)
            except Exception as exc:
                validation_error = f"repair_failed:{exc.__class__.__name__}"
                break
        if not normalized:
            fallback["providerWarning"] = f"{self.provider}_fallback:{validation_error}"
            return fallback

        assistant_text = normalized["assistantTextKo"]
        spoken_text = normalized["spokenTextJa"]
        suggested_reply = normalized["suggestedUserReplyJa"]
        if assistant_text:
            fallback["assistantText"] = assistant_text
        if spoken_text:
            fallback["spokenText"] = spoken_text if spoken_text.endswith("。") else spoken_text + "。"
        if suggested_reply:
            fallback["suggestedUserReply"] = suggested_reply if suggested_reply.endswith("。") else suggested_reply + "。"
        fallback["corrections"] = normalized["corrections"]
        if normalized["reviewCards"]:
            fallback["reviewCards"] = normalized["reviewCards"]
        fallback["usage"]["llmProvider"] = self.provider
        fallback["usage"]["externalModel"] = self.model
        if repaired:
            fallback["providerWarning"] = f"{self.provider}_repaired_structured_output"
        return fallback


def _llm_response_format(mode: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    normalized = (mode or "json_object").strip().lower()
    if normalized in {"json_schema", "strict_json_schema"}:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ai_language_partner_turn_payload_v1",
                "strict": True,
                "schema": schema,
            },
        }
    return {"type": "json_object"}


def _structured_turn_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schemaVersion", "assistantTextKo", "spokenTextJa", "suggestedUserReplyJa", "corrections", "reviewCards"],
        "properties": {
            "schemaVersion": {"type": "string", "const": STRUCTURED_TURN_SCHEMA_VERSION},
            "assistantTextKo": {"type": "string", "minLength": 1, "maxLength": 1200},
            "spokenTextJa": {"type": "string", "minLength": 1, "maxLength": 1200},
            "suggestedUserReplyJa": {"type": "string", "minLength": 1, "maxLength": 1200},
            "corrections": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["category", "original", "corrected", "explanationKo"],
                    "properties": {
                        "category": {"type": "string", "minLength": 1, "maxLength": 80},
                        "original": {"type": "string", "maxLength": 500},
                        "corrected": {"type": "string", "maxLength": 500},
                        "explanationKo": {"type": "string", "maxLength": 800},
                        "severity": {"type": "string", "enum": ["minor", "medium", "important"]},
                        "isKoreanLiteral": {"type": "boolean"},
                    },
                },
            },
            "reviewCards": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["front", "back"],
                    "properties": {
                        "front": {"type": "string", "minLength": 1, "maxLength": 500},
                        "back": {"type": "string", "minLength": 1, "maxLength": 500},
                        "example": {"type": ["string", "null"], "maxLength": 800},
                        "tags": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 80}},
                    },
                },
            },
        },
    }


def _parse_json_object(content: str) -> Dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("non_object_json")
    return parsed


def _normalize_structured_turn_payload(payload: Any) -> tuple[Optional[Dict[str, Any]], str]:
    if not isinstance(payload, dict):
        return None, "non_object_json"
    if payload.get("schemaVersion") != STRUCTURED_TURN_SCHEMA_VERSION:
        return None, "unsupported_schemaVersion"
    normalized: Dict[str, Any] = {}
    normalized["schemaVersion"] = STRUCTURED_TURN_SCHEMA_VERSION
    for key in ["assistantTextKo", "spokenTextJa", "suggestedUserReplyJa"]:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            return None, f"missing_{key}"
        normalized[key] = payload[key].strip()[:1200]
    corrections = payload.get("corrections", [])
    if corrections is not None:
        if not isinstance(corrections, list):
            return None, "invalid_corrections"
        required = {"category", "original", "corrected", "explanationKo"}
        normalized_corrections = []
        for item in corrections[:5]:
            if not isinstance(item, dict) or any(not isinstance(item.get(key), str) for key in required):
                return None, "invalid_correction_item"
            severity = item.get("severity") if item.get("severity") in {"minor", "medium", "important"} else "minor"
            normalized_corrections.append(
                {
                    "category": item["category"].strip()[:80],
                    "original": item["original"].strip()[:500],
                    "corrected": item["corrected"].strip()[:500],
                    "explanationKo": item["explanationKo"].strip()[:800],
                    "severity": severity,
                    "isKoreanLiteral": bool(item.get("isKoreanLiteral", False)),
                }
            )
    else:
        normalized_corrections = []
    review_cards = payload.get("reviewCards", [])
    if review_cards is not None:
        if not isinstance(review_cards, list):
            return None, "invalid_review_cards"
        normalized_cards = []
        for item in review_cards[:3]:
            if not isinstance(item, dict) or not isinstance(item.get("front"), str) or not isinstance(item.get("back"), str):
                return None, "invalid_review_card_item"
            tags = item.get("tags") if isinstance(item.get("tags"), list) else []
            normalized_cards.append(
                {
                    "front": item["front"].strip()[:500],
                    "back": item["back"].strip()[:500],
                    "example": item["example"].strip()[:800] if isinstance(item.get("example"), str) else None,
                    "tags": [str(tag).strip()[:80] for tag in tags[:8] if str(tag).strip()],
                }
            )
    else:
        normalized_cards = []
    normalized["corrections"] = normalized_corrections
    normalized["reviewCards"] = normalized_cards
    return normalized, ""


def _repair_payload(original_payload: Dict[str, Any], broken_payload: Any, validation_error: str) -> Dict[str, Any]:
    payload = dict(original_payload)
    messages = list(payload.get("messages") or [])
    messages.append(
        {
            "role": "user",
            "content": json.dumps(
                {
                    "repairInstruction": "Return only a valid JSON object matching the required schema. No prose, no markdown.",
                    "validationError": validation_error,
                    "brokenPayload": broken_payload,
                    "schemaVersion": STRUCTURED_TURN_SCHEMA_VERSION,
                    "requiredKeys": ["schemaVersion", "assistantTextKo", "spokenTextJa", "suggestedUserReplyJa", "corrections", "reviewCards"],
                    "correctionItemRequiredKeys": ["category", "original", "corrected", "explanationKo"],
                    "reviewCardRequiredKeys": ["front", "back"],
                },
                ensure_ascii=False,
            ),
        }
    )
    payload["messages"] = messages
    payload["temperature"] = 0.1
    return payload


class OpenAITTSProvider(MockTTSProvider):
    provider = "openai_tts"
    external_configured = True

    def __init__(self, api_key: str, base_url: str, model: str, voice: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.voice = voice
        self._fallback = MockTTSProvider()

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "externalConfigured": bool(self.api_key),
            "replaceable": True,
            "baseUrl": self.base_url,
            "model": self.model,
            "voice": self.voice,
            "secretsReturned": False,
        }

    def synthesize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "voice": self.voice,
            "input": request["text"],
            "response_format": "mp3",
            "speed": float(request.get("speed") or 1.0),
        }
        try:
            audio_bytes = _post_bytes(f"{self.base_url}/audio/speech", payload, self.api_key, timeout=30)
            audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
            duration_ms = max(800, min(12000, int(len(request["text"]) * 130)))
            return {
                "audioUrl": "data:audio/mpeg;base64," + audio_base64,
                "audioBase64": audio_base64,
                "provider": self.provider,
                "cacheHit": False,
                "spokenText": request["text"],
                "durationMs": duration_ms,
                "latencyMs": 0,
                "voiceUsed": self.voice,
            }
        except Exception:
            result = self._fallback.synthesize(request)
            result["provider"] = self.provider + "_fallback_mock"
            return result


class EdgeTTSProvider(MockTTSProvider):
    provider = "edge_tts"
    external_configured = True

    def __init__(self, voice: str):
        self.voice = voice
        self._fallback = MockTTSProvider()

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "externalConfigured": True,
            "replaceable": True,
            "voice": self.voice,
            "secretsReturned": False,
        }

    def voice_used_for(self, request: Dict[str, Any]) -> str:
        voice = voice_for_request(request)
        return str(voice.get("edgeVoice") or self.voice)

    def synthesize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        out_path = None
        voice_used = self.voice_used_for(request)
        rate = int(round((float(request.get("speed") or 1.0) - 1.0) * 100))
        rate_arg = f"{rate:+d}%"
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                out_path = tmp.name
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "edge_tts",
                    "--voice",
                    voice_used,
                    "--rate",
                    rate_arg,
                    "--text",
                    request["text"],
                    "--write-media",
                    out_path,
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
            with open(out_path, "rb") as handle:
                audio_bytes = handle.read()
            if not audio_bytes:
                raise RuntimeError("edge-tts produced empty audio")
            audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
            duration_ms = max(800, min(12000, int(len(request["text"]) * 130)))
            return {
                "audioUrl": "data:audio/mpeg;base64," + audio_base64,
                "audioBase64": audio_base64,
                "provider": self.provider,
                "cacheHit": False,
                "spokenText": request["text"],
                "durationMs": duration_ms,
                "latencyMs": int((time.perf_counter() - started) * 1000),
                "voiceUsed": voice_used,
            }
        except Exception:
            result = self._fallback.synthesize(request)
            result["provider"] = self.provider + "_fallback_mock"
            result["voiceUsed"] = voice_used
            return result
        finally:
            if out_path and os.path.exists(out_path):
                os.unlink(out_path)


class VoicevoxCompatTTSProvider(MockTTSProvider):
    provider = "voicevox_compat"
    external_configured = True

    def __init__(self, engine: str, base_url: str, fallback: Optional[MockTTSProvider] = None):
        self.engine = engine
        self.base_url = base_url.rstrip("/")
        self._fallback = fallback or EdgeTTSProvider("ja-JP-NanamiNeural")
        self._speakers_cache: Optional[list[Dict[str, Any]]] = None

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "engine": self.engine,
            "externalConfigured": True,
            "replaceable": True,
            "baseUrl": self.base_url,
            "voiceCatalogSize": len(load_voice_catalog()),
            "personaVoices": sorted(load_persona_voice_map().keys()),
            "fallback": self._fallback.provider,
            "secretsReturned": False,
        }

    def voice_used_for(self, request: Dict[str, Any]) -> str:
        return str(voice_for_request(request).get("voiceId"))

    def synthesize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        voice = voice_for_request(request)
        try:
            speaker_id = self._resolve_speaker_id(voice)
            query_url = f"{self.base_url}/audio_query?text={urllib.parse.quote(str(request['text']))}&speaker={speaker_id}"
            query_req = urllib.request.Request(query_url, data=b"", method="POST")
            with urllib.request.urlopen(query_req, timeout=20) as response:
                query = json.loads(response.read().decode("utf-8"))
            request_speed = float(request.get("speed") or 1.0)
            query["speedScale"] = float(voice.get("speedScale") or query.get("speedScale") or 1.0) * request_speed
            query["pitchScale"] = float(voice.get("pitchScale") if voice.get("pitchScale") is not None else query.get("pitchScale") or 0.0)
            query["intonationScale"] = float(
                voice.get("intonationScale") if voice.get("intonationScale") is not None else query.get("intonationScale") or 1.0
            )
            query["volumeScale"] = float(voice.get("volumeScale") if voice.get("volumeScale") is not None else query.get("volumeScale") or 1.0)
            body = json.dumps(query, ensure_ascii=False).encode("utf-8")
            synthesis_req = urllib.request.Request(
                f"{self.base_url}/synthesis?speaker={speaker_id}",
                data=body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(synthesis_req, timeout=60) as response:
                audio_bytes = response.read()
            if not audio_bytes:
                raise RuntimeError("voice engine returned empty audio")
            audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
            duration_ms = max(700, min(12000, int(len(request["text"]) * 130 / max(0.5, float(request.get("speed") or 1.0)))))
            return {
                "audioUrl": "data:audio/wav;base64," + audio_base64,
                "audioBase64": audio_base64,
                "provider": self.provider,
                "cacheHit": False,
                "spokenText": request["text"],
                "durationMs": duration_ms,
                "latencyMs": int((time.perf_counter() - started) * 1000),
                "voiceUsed": str(voice.get("voiceId")),
                "engineSpeakerId": speaker_id,
                "voice": voice,
            }
        except Exception:
            result = self._fallback.synthesize(request)
            result["provider"] = self.provider + "_fallback_" + result["provider"]
            result["voiceUsed"] = str(voice.get("voiceId"))
            result["voiceEngineError"] = "unavailable_or_unmatched_speaker"
            return result

    def _speakers(self) -> list[Dict[str, Any]]:
        if self._speakers_cache is None:
            with urllib.request.urlopen(f"{self.base_url}/speakers", timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
            self._speakers_cache = data if isinstance(data, list) else []
        return self._speakers_cache

    def _resolve_speaker_id(self, voice: Dict[str, Any]) -> int:
        style_id = voice.get("engineStyleId")
        if isinstance(style_id, int):
            return style_id
        character = str(voice.get("characterName") or "")
        style = str(voice.get("styleName") or "")
        for speaker in self._speakers():
            if str(speaker.get("name")) != character:
                continue
            for speaker_style in speaker.get("styles") or []:
                if str(speaker_style.get("name")) == style and isinstance(speaker_style.get("id"), int):
                    return int(speaker_style["id"])
        raise RuntimeError(f"speaker style not found: {character}/{style}")


class ElevenLabsTTSProvider(OpenAITTSProvider):
    provider = "elevenlabs_tts"

    def __init__(self, api_key: str, base_url: str, voice_id: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.voice = voice_id
        self.model = model
        self._fallback = MockTTSProvider()

    def synthesize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"text": request["text"], "model_id": self.model, "voice_settings": {"stability": 0.45, "similarity_boost": 0.75}}
        try:
            url = f"{self.base_url}/v1/text-to-speech/{self.voice}"
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={"Content-Type": "application/json", "xi-api-key": self.api_key, "Accept": "audio/mpeg"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                audio_bytes = response.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
            duration_ms = max(800, min(12000, int(len(request["text"]) * 130)))
            return {
                "audioUrl": "data:audio/mpeg;base64," + audio_base64,
                "audioBase64": audio_base64,
                "provider": self.provider,
                "cacheHit": False,
                "spokenText": request["text"],
                "durationMs": duration_ms,
                "latencyMs": 0,
                "voiceUsed": self.voice,
            }
        except Exception:
            result = self._fallback.synthesize(request)
            result["provider"] = self.provider + "_fallback_mock"
            return result


class OpenAISTTProvider(MockSTTProvider):
    provider = "openai_stt"
    external_configured = True

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._fallback = MockSTTProvider()

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "externalConfigured": bool(self.api_key),
            "replaceable": True,
            "baseUrl": self.base_url,
            "model": self.model,
            "secretsReturned": False,
        }

    def transcribe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        audio_base64 = request.get("audioBase64")
        if not audio_base64:
            result = self._fallback.transcribe(request)
            result["provider"] = self.provider + "_fallback_mock"
            return result
        try:
            audio_bytes, content_type = decode_audio_payload(audio_base64)
            text = _post_audio_transcription(
                f"{self.base_url}/audio/transcriptions",
                self.api_key,
                self.model,
                audio_bytes,
                content_type=content_type,
                timeout=30,
            )
            return {"text": text, "provider": self.provider, "confidence": 0.9, "sttSeconds": 2.0, "latencyMs": 0}
        except Exception:
            result = self._fallback.transcribe(request)
            result["provider"] = self.provider + "_fallback_mock"
            return result


class WhisperCppSTTProvider(MockSTTProvider):
    provider = "whisper_cpp"
    external_configured = True

    def __init__(self, binary: str, model_path: str, fallback: Optional[MockSTTProvider] = None):
        self.binary = binary
        self.model_path = model_path
        self._fallback = fallback or MockSTTProvider()

    def describe(self) -> Dict[str, Any]:
        return {
            "active": self.provider,
            "externalConfigured": True,
            "replaceable": True,
            "binary": self.binary,
            "modelPathConfigured": bool(self.model_path),
            "modelPresent": bool(self.model_path and os.path.exists(os.path.expanduser(self.model_path))),
            "ffmpegPresent": bool(_which("ffmpeg")),
            "secretsReturned": False,
        }

    def transcribe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        audio_base64 = request.get("audioBase64")
        if not audio_base64:
            result = self._fallback.transcribe(request)
            result["provider"] = self.provider + "_fallback_mock"
            return result
        input_path = None
        wav_path = None
        transcript_path = None
        try:
            audio_bytes, content_type = decode_audio_payload(audio_base64)
            if not audio_bytes:
                raise RuntimeError("empty audio")
            suffix = "." + _audio_extension(content_type)
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                input_path = tmp.name
                tmp.write(audio_bytes)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            ffmpeg = _which("ffmpeg")
            if not ffmpeg:
                raise RuntimeError("ffmpeg not found")
            subprocess.run(
                [ffmpeg, "-y", "-i", input_path, "-ac", "1", "-ar", "16000", wav_path],
                check=True,
                capture_output=True,
                timeout=30,
            )
            binary = os.path.expanduser(self.binary)
            model_path = os.path.expanduser(self.model_path)
            if not os.path.exists(binary) or not os.path.exists(model_path):
                raise RuntimeError("whisper.cpp binary or model missing")
            cmd = [binary, "-m", model_path, "-f", wav_path, "-l", str(request.get("language") or "ja"), "-otxt"]
            prompt = _initial_prompt_from_hints(request)
            if prompt:
                cmd.extend(["--prompt", prompt])
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            transcript_path = wav_path + ".txt"
            with open(transcript_path, "r", encoding="utf-8") as handle:
                text = handle.read().strip()
            if not text:
                raise RuntimeError("empty transcription")
            return {
                "text": text,
                "provider": self.provider,
                "confidence": 0.88,
                "sttSeconds": float(request.get("durationSeconds") or 2.0),
                "latencyMs": int((time.perf_counter() - started) * 1000),
            }
        except Exception:
            result = self._fallback.transcribe(request)
            result["provider"] = self.provider + "_fallback_mock"
            return result
        finally:
            for path in [input_path, wav_path, transcript_path]:
                if path and os.path.exists(path):
                    os.unlink(path)


def build_provider_stack(env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    values = env or os.environ
    llm = _build_llm(values)
    tts = _build_tts(values)
    stt = _build_stt(values)
    pronunciation = _build_pronunciation(values)
    return {"llm": llm, "tts": tts, "stt": stt, "pronunciation": pronunciation}


def _build_llm(env: Dict[str, str]) -> MockLLMProvider:
    provider = env.get("AI_LANGUAGE_PARTNER_LLM_PROVIDER", "mock").lower()
    key = env.get("AI_LANGUAGE_PARTNER_LLM_API_KEY") or env.get("OPENAI_API_KEY")
    if provider in {"openai", "openai_compatible"} and key:
        return OpenAICompatibleLLMProvider(
            api_key=key,
            base_url=env.get("AI_LANGUAGE_PARTNER_LLM_BASE_URL", "https://api.openai.com/v1"),
            model=env.get("AI_LANGUAGE_PARTNER_LLM_MODEL", "gpt-4o-mini"),
            repair_attempts=int(env.get("AI_LANGUAGE_PARTNER_LLM_REPAIR_ATTEMPTS", "2")),
            response_format_mode=env.get("AI_LANGUAGE_PARTNER_LLM_RESPONSE_FORMAT", "json_object"),
        )
    return MockLLMProvider()


def _build_tts(env: Dict[str, str]) -> MockTTSProvider:
    provider = env.get("AI_LANGUAGE_PARTNER_TTS_PROVIDER", "mock").lower()
    openai_key = env.get("AI_LANGUAGE_PARTNER_TTS_API_KEY") or env.get("OPENAI_API_KEY")
    eleven_key = env.get("ELEVENLABS_API_KEY")
    if provider == "openai" and openai_key:
        return OpenAITTSProvider(
            api_key=openai_key,
            base_url=env.get("AI_LANGUAGE_PARTNER_TTS_BASE_URL", "https://api.openai.com/v1"),
            model=env.get("AI_LANGUAGE_PARTNER_TTS_MODEL", "gpt-4o-mini-tts"),
            voice=env.get("AI_LANGUAGE_PARTNER_TTS_VOICE", "alloy"),
        )
    if provider == "elevenlabs" and eleven_key:
        return ElevenLabsTTSProvider(
            api_key=eleven_key,
            base_url=env.get("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io"),
            voice_id=env.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
            model=env.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
        )
    if provider == "edge":
        return EdgeTTSProvider(voice=env.get("AI_LANGUAGE_PARTNER_TTS_VOICE", "ja-JP-NanamiNeural"))
    if provider in {"voicevox", "aivis", "voicevox_compat"}:
        engine = "aivis" if provider == "aivis" else "voicevox"
        return VoicevoxCompatTTSProvider(
            engine=engine,
            base_url=env.get("AI_LANGUAGE_PARTNER_VOICE_ENGINE_URL", env.get("VOICEVOX_BASE_URL", "http://127.0.0.1:10101")),
        )
    return MockTTSProvider()


def _build_stt(env: Dict[str, str]) -> MockSTTProvider:
    provider = env.get("AI_LANGUAGE_PARTNER_STT_PROVIDER", "mock").lower()
    key = env.get("AI_LANGUAGE_PARTNER_STT_API_KEY") or env.get("OPENAI_API_KEY")
    if provider == "openai" and key:
        return OpenAISTTProvider(
            api_key=key,
            base_url=env.get("AI_LANGUAGE_PARTNER_STT_BASE_URL", "https://api.openai.com/v1"),
            model=env.get("AI_LANGUAGE_PARTNER_STT_MODEL", "whisper-1"),
        )
    if provider in {"whisper", "whisper_cpp"}:
        return WhisperCppSTTProvider(
            binary=env.get("AI_LANGUAGE_PARTNER_WHISPER_CPP_BIN", "/opt/homebrew/bin/whisper-cli"),
            model_path=env.get("AI_LANGUAGE_PARTNER_WHISPER_CPP_MODEL", "~/whisper-models/ggml-medium.bin"),
        )
    return MockSTTProvider()


def _build_pronunciation(env: Dict[str, str]) -> MockPronunciationScorer:
    provider = env.get("AI_LANGUAGE_PARTNER_PRONUNCIATION_PROVIDER", "acoustic_feature_mock").lower()
    if provider in {"mock", "text_mock"}:
        return MockPronunciationScorer()
    return AcousticFeaturePronunciationScorer()


def _post_json(url: str, payload: Dict[str, Any], api_key: str, timeout: int) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_bytes(url: str, payload: Dict[str, Any], api_key: str, timeout: int) -> bytes:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def _post_audio_transcription(
    url: str,
    api_key: str,
    model: str,
    audio_bytes: bytes,
    timeout: int,
    content_type: str = "audio/wav",
) -> str:
    boundary = "----ai-language-partner-boundary"
    extension = _audio_extension(content_type)
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{model}\r\n".encode("utf-8"),
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"audio.{extension}\"\r\n"
            f"Content-Type: {content_type or 'application/octet-stream'}\r\n\r\n"
        ).encode("utf-8"),
        audio_bytes,
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    req = urllib.request.Request(
        url,
        data=b"".join(parts),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("text") or "")
