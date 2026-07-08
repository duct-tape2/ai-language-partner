from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[1]

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.providers import STRUCTURED_TURN_SCHEMA_VERSION, _mock_wav_base64, _post_audio_transcription


def _enabled(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_bool(env: Mapping[str, str], key: str) -> bool:
    return bool((env.get(key) or "").strip())


def _redacted_env(env: Mapping[str, str], key: str) -> dict[str, Any]:
    return {"name": key, "present": _env_bool(env, key), "valueReturned": False}


def _provider_env_key(provider: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in provider.upper())
    return cleaned.strip("_") or "OIDC"


def _json_request(url: str, payload: Optional[dict[str, Any]], headers: dict[str, str], timeout: int, method: str = "GET") -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _bytes_request(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> tuple[bytes, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), response.headers.get("content-type", "")


def _skip(check_id: str, reason: str, configured: bool = False, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    result = {"id": check_id, "status": "skipped", "configured": configured, "reason": reason}
    if extra:
        result.update(extra)
    return result


def _fail(check_id: str, reason: str, configured: bool = True) -> dict[str, Any]:
    return {"id": check_id, "status": "failed", "configured": configured, "reason": reason}


def _pass(check_id: str, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    result = {"id": check_id, "status": "passed", "configured": True}
    if extra:
        result.update(extra)
    return result


def _safe_call(check_id: str, fn) -> dict[str, Any]:
    try:
        return fn()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return _fail(check_id, f"{exc.__class__.__name__}")
    except Exception as exc:
        return _fail(check_id, f"{exc.__class__.__name__}")


def _oidc_providers(env: Mapping[str, str]) -> list[str]:
    configured = env.get("AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS", "")
    return [item.strip().lower() for item in configured.split(",") if item.strip()]


def _oidc_issuer(env: Mapping[str, str], provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    return env.get(f"AI_LANGUAGE_PARTNER_OIDC_{key}_ISSUER") or env.get("AI_LANGUAGE_PARTNER_OIDC_ISSUER")


def verify_oidc_discovery(env: Mapping[str, str], real_calls: bool, timeout: int) -> dict[str, Any]:
    providers = _oidc_providers(env)
    configured = []
    for provider in providers:
        issuer = (_oidc_issuer(env, provider) or "").rstrip("/")
        if issuer and not issuer.startswith("https://local-oidc.example"):
            configured.append({"provider": provider, "issuer": issuer})
    if not configured:
        return _skip("oidc_discovery", "no_real_oidc_issuer_configured", configured=False)
    if not real_calls:
        return _skip("oidc_discovery", "real_calls_disabled", configured=True, extra={"configuredProviders": [item["provider"] for item in configured]})

    def run() -> dict[str, Any]:
        details = []
        for item in configured:
            url = item["issuer"] + "/.well-known/openid-configuration"
            discovery = _json_request(url, None, {"Accept": "application/json"}, timeout)
            jwks_uri = discovery.get("jwks_uri")
            issuer_matches = discovery.get("issuer") == item["issuer"]
            if not jwks_uri or not issuer_matches:
                return _fail("oidc_discovery", "issuer_or_jwks_uri_mismatch")
            jwks = _json_request(str(jwks_uri), None, {"Accept": "application/json"}, timeout)
            keys = jwks.get("keys") if isinstance(jwks, dict) else None
            details.append({"provider": item["provider"], "issuerMatches": issuer_matches, "jwksKeyCount": len(keys or [])})
        return _pass("oidc_discovery", {"providers": details})

    return _safe_call("oidc_discovery", run)


def verify_llm_strict_json_schema(env: Mapping[str, str], real_calls: bool, timeout: int) -> dict[str, Any]:
    provider = (env.get("AI_LANGUAGE_PARTNER_LLM_PROVIDER") or "mock").strip().lower()
    api_key = env.get("AI_LANGUAGE_PARTNER_LLM_API_KEY") or env.get("OPENAI_API_KEY")
    configured = provider in {"openai", "openai_compatible"} and bool(api_key)
    if not configured:
        return _skip("llm_strict_json_schema", "openai_compatible_llm_not_configured", configured=False)
    if not real_calls:
        return _skip("llm_strict_json_schema", "real_calls_disabled", configured=True)

    def run() -> dict[str, Any]:
        base_url = (env.get("AI_LANGUAGE_PARTNER_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        model = env.get("AI_LANGUAGE_PARTNER_LLM_MODEL") or "gpt-4o-mini"
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["schemaVersion", "ok"],
            "properties": {
                "schemaVersion": {"type": "string", "const": STRUCTURED_TURN_SCHEMA_VERSION},
                "ok": {"type": "boolean"},
            },
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON matching the schema."},
                {"role": "user", "content": "Return ok true."},
            ],
            "temperature": 0,
            "response_format": {"type": "json_schema", "json_schema": {"name": "external_smoke", "strict": True, "schema": schema}},
        }
        response = _json_request(
            base_url + "/chat/completions",
            payload,
            {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            timeout,
            method="POST",
        )
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        ok = parsed.get("schemaVersion") == STRUCTURED_TURN_SCHEMA_VERSION and parsed.get("ok") is True
        return _pass("llm_strict_json_schema", {"model": model, "schemaVersionMatched": ok}) if ok else _fail("llm_strict_json_schema", "schema_mismatch")

    return _safe_call("llm_strict_json_schema", run)


def verify_tts_media(env: Mapping[str, str], real_calls: bool, timeout: int) -> dict[str, Any]:
    provider = (env.get("AI_LANGUAGE_PARTNER_TTS_PROVIDER") or "mock").strip().lower()
    openai_key = env.get("AI_LANGUAGE_PARTNER_TTS_API_KEY") or env.get("OPENAI_API_KEY")
    eleven_key = env.get("ELEVENLABS_API_KEY")
    configured = (provider == "openai" and bool(openai_key)) or (provider == "elevenlabs" and bool(eleven_key))
    if not configured:
        return _skip("tts_media_compatibility", "tts_provider_not_configured", configured=False)
    if not real_calls:
        return _skip("tts_media_compatibility", "real_calls_disabled", configured=True, extra={"provider": provider})

    def run_openai() -> dict[str, Any]:
        base_url = (env.get("AI_LANGUAGE_PARTNER_TTS_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": env.get("AI_LANGUAGE_PARTNER_TTS_MODEL") or "gpt-4o-mini-tts",
            "voice": env.get("AI_LANGUAGE_PARTNER_TTS_VOICE") or "alloy",
            "input": "External provider smoke test.",
            "response_format": "mp3",
        }
        audio, content_type = _bytes_request(
            base_url + "/audio/speech",
            payload,
            {"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}", "Accept": "audio/mpeg"},
            timeout,
        )
        return _pass("tts_media_compatibility", {"provider": "openai", "contentType": content_type, "audioBytes": len(audio)}) if len(audio) > 100 else _fail("tts_media_compatibility", "empty_audio")

    def run_elevenlabs() -> dict[str, Any]:
        base_url = (env.get("ELEVENLABS_BASE_URL") or "https://api.elevenlabs.io").rstrip("/")
        voice_id = env.get("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"
        payload = {"text": "External provider smoke test.", "model_id": env.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2"}
        audio, content_type = _bytes_request(
            f"{base_url}/v1/text-to-speech/{urllib.parse.quote(voice_id)}",
            payload,
            {"Content-Type": "application/json", "xi-api-key": str(eleven_key), "Accept": "audio/mpeg"},
            timeout,
        )
        return _pass("tts_media_compatibility", {"provider": "elevenlabs", "contentType": content_type, "audioBytes": len(audio)}) if len(audio) > 100 else _fail("tts_media_compatibility", "empty_audio")

    return _safe_call("tts_media_compatibility", run_openai if provider == "openai" else run_elevenlabs)


def verify_stt_media(env: Mapping[str, str], real_calls: bool, timeout: int) -> dict[str, Any]:
    provider = (env.get("AI_LANGUAGE_PARTNER_STT_PROVIDER") or "mock").strip().lower()
    api_key = env.get("AI_LANGUAGE_PARTNER_STT_API_KEY") or env.get("OPENAI_API_KEY")
    configured = provider == "openai" and bool(api_key)
    if not configured:
        return _skip("stt_media_compatibility", "openai_stt_not_configured", configured=False)
    if not real_calls:
        return _skip("stt_media_compatibility", "real_calls_disabled", configured=True)

    def run() -> dict[str, Any]:
        base_url = (env.get("AI_LANGUAGE_PARTNER_STT_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        audio = base64.b64decode(_mock_wav_base64(duration_ms=900), validate=False)
        text = _post_audio_transcription(
            base_url + "/audio/transcriptions",
            str(api_key),
            env.get("AI_LANGUAGE_PARTNER_STT_MODEL") or "whisper-1",
            audio,
            content_type="audio/wav",
            timeout=timeout,
        )
        return _pass("stt_media_compatibility", {"provider": "openai", "transcriptPresent": bool(text), "audioBytes": len(audio)}) if text else _fail("stt_media_compatibility", "empty_transcript")

    return _safe_call("stt_media_compatibility", run)


def verify_pronunciation_provider(env: Mapping[str, str]) -> dict[str, Any]:
    provider = (env.get("AI_LANGUAGE_PARTNER_PRONUNCIATION_PROVIDER") or "acoustic_feature_mock").strip().lower()
    if provider in {"mock", "text_mock", "acoustic_feature_mock"}:
        return _skip("production_pronunciation_provider", "production_pronunciation_provider_not_configured", configured=False, extra={"activeProvider": provider})
    return _pass("production_pronunciation_provider", {"activeProvider": provider, "note": "custom provider selected; run app-level pronunciation scoring smoke separately"})


def verify_external_provider_readiness(env: Optional[Mapping[str, str]] = None) -> dict[str, Any]:
    values = env or os.environ
    real_calls = _enabled(values.get("AI_LANGUAGE_PARTNER_EXTERNAL_SMOKE_REAL_CALLS"))
    timeout = max(2, min(60, int(values.get("AI_LANGUAGE_PARTNER_EXTERNAL_SMOKE_TIMEOUT_SECONDS", "15"))))
    checks = [
        verify_oidc_discovery(values, real_calls, timeout),
        verify_llm_strict_json_schema(values, real_calls, timeout),
        verify_tts_media(values, real_calls, timeout),
        verify_stt_media(values, real_calls, timeout),
        verify_pronunciation_provider(values),
    ]
    failed = [item for item in checks if item["status"] == "failed"]
    passed = [item for item in checks if item["status"] == "passed"]
    skipped = [item for item in checks if item["status"] == "skipped"]
    return {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "projectId": "ai-language-partner-mobile-shared-20260629-v1",
        "realCallsEnabled": real_calls,
        "timeoutSeconds": timeout,
        "passed": not failed,
        "realProviderEvidenceComplete": real_calls and not failed and len(passed) >= 4,
        "summary": {
            "passed": len(passed),
            "skipped": len(skipped),
            "failed": len(failed),
        },
        "secretsReturned": False,
        "env": [
            _redacted_env(values, "OPENAI_API_KEY"),
            _redacted_env(values, "AI_LANGUAGE_PARTNER_LLM_API_KEY"),
            _redacted_env(values, "AI_LANGUAGE_PARTNER_TTS_API_KEY"),
            _redacted_env(values, "AI_LANGUAGE_PARTNER_STT_API_KEY"),
            _redacted_env(values, "ELEVENLABS_API_KEY"),
            _redacted_env(values, "AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS"),
        ],
        "checks": {item["id"]: item for item in checks},
    }


def main() -> int:
    result = verify_external_provider_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
