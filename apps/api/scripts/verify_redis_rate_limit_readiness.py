from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rate_limit import build_rate_limiter


def _enabled(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


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


def verify_fallback_does_not_leak_secret() -> dict[str, Any]:
    secret_url = "redis://:redis-secret-should-not-leak@127.0.0.1:6390/0"
    limiter = build_rate_limiter(
        {
            "AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND": "redis",
            "AI_LANGUAGE_PARTNER_REDIS_URL": secret_url,
            "AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE": "2",
        }
    )
    description = limiter.describe()
    serialized = json.dumps(description, ensure_ascii=False, sort_keys=True)
    if "redis-secret-should-not-leak" in serialized:
        return _fail("redis_fallback_secret_redaction", "redis_url_secret_leaked", configured=True)
    if description.get("backend") == "redis":
        return _skip(
            "redis_fallback_secret_redaction",
            "unexpected_local_redis_on_fallback_port",
            configured=True,
            extra={"backend": "redis", "secretsReturned": False},
        )
    fallback_reason = str(description.get("fallbackReason") or "")
    ok = description.get("backend") == "memory" and description.get("requestedBackend") == "redis" and fallback_reason.startswith("redis_unavailable:")
    if not ok:
        return _fail("redis_fallback_secret_redaction", "fallback_description_mismatch", configured=True)
    return _pass(
        "redis_fallback_secret_redaction",
        {
            "backend": description["backend"],
            "requestedBackend": description["requestedBackend"],
            "fallbackReasonClass": fallback_reason.split(":", 1)[-1],
            "secretsReturned": False,
        },
    )


def _redis_client(redis_url: str):
    import redis  # type: ignore

    return redis.Redis.from_url(redis_url)


def verify_live_redis_ping(redis_url: str, timeout_seconds: int) -> dict[str, Any]:
    try:
        client = _redis_client(redis_url)
        if hasattr(client, "connection_pool"):
            client.connection_pool.connection_kwargs["socket_connect_timeout"] = timeout_seconds
            client.connection_pool.connection_kwargs["socket_timeout"] = timeout_seconds
        ping_ok = bool(client.ping())
        return _pass("redis_live_ping", {"ping": ping_ok, "secretsReturned": False}) if ping_ok else _fail("redis_live_ping", "ping_false")
    except Exception as exc:
        return _fail("redis_live_ping", exc.__class__.__name__)


def verify_distributed_counter(redis_url: str) -> dict[str, Any]:
    try:
        first = build_rate_limiter(
            {
                "AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND": "redis",
                "AI_LANGUAGE_PARTNER_REDIS_URL": redis_url,
                "AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE": "2",
            }
        )
        second = build_rate_limiter(
            {
                "AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND": "redis",
                "AI_LANGUAGE_PARTNER_REDIS_URL": redis_url,
                "AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE": "2",
            }
        )
        if first.describe().get("backend") != "redis" or second.describe().get("backend") != "redis":
            return _fail("redis_distributed_counter", "redis_limiter_not_active")
        now = time.time()
        client_id = f"redis-smoke-{int(now * 1000)}"
        path = "/redis-smoke"
        one = first.check(client_id, path, now=now)
        two = second.check(client_id, path, now=now)
        three = first.check(client_id, path, now=now)
        ok = one.allowed and two.allowed and not three.allowed and three.backend == "redis"
        if not ok:
            return _fail("redis_distributed_counter", "shared_counter_limit_not_enforced")
        return _pass(
            "redis_distributed_counter",
            {
                "firstAllowed": one.allowed,
                "secondAllowed": two.allowed,
                "thirdAllowed": three.allowed,
                "thirdRetryAfterSeconds": three.retry_after_seconds,
                "distributed": first.describe().get("distributed") is True,
                "secretsReturned": False,
            },
        )
    except Exception as exc:
        return _fail("redis_distributed_counter", exc.__class__.__name__)


def verify_light_load(redis_url: str, request_count: int) -> dict[str, Any]:
    try:
        limiter = build_rate_limiter(
            {
                "AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND": "redis",
                "AI_LANGUAGE_PARTNER_REDIS_URL": redis_url,
                "AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE": str(max(1, request_count)),
            }
        )
        if limiter.describe().get("backend") != "redis":
            return _fail("redis_light_load", "redis_limiter_not_active")
        started = time.perf_counter()
        now = time.time()
        client_id = f"redis-load-{int(now * 1000)}"
        allowed_count = 0
        for index in range(request_count):
            decision = limiter.check(client_id, "/redis-load", now=now + index * 0.001)
            allowed_count += int(decision.allowed)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        ok = allowed_count == request_count
        if not ok:
            return _fail("redis_light_load", "unexpected_rate_limit_during_load")
        return _pass(
            "redis_light_load",
            {
                "requestCount": request_count,
                "allowedCount": allowed_count,
                "elapsedMs": elapsed_ms,
                "secretsReturned": False,
            },
        )
    except Exception as exc:
        return _fail("redis_light_load", exc.__class__.__name__)


def verify_redis_rate_limit_readiness(env: Optional[Mapping[str, str]] = None) -> dict[str, Any]:
    values = env or os.environ
    real_calls = _enabled(values.get("AI_LANGUAGE_PARTNER_REDIS_SMOKE_REAL_CALLS"))
    redis_url = (values.get("AI_LANGUAGE_PARTNER_REDIS_URL") or "").strip()
    timeout_seconds = max(1, min(30, int(values.get("AI_LANGUAGE_PARTNER_REDIS_SMOKE_TIMEOUT_SECONDS", "5"))))
    request_count = max(1, min(500, int(values.get("AI_LANGUAGE_PARTNER_REDIS_SMOKE_REQUESTS", "40"))))
    checks = [verify_fallback_does_not_leak_secret()]
    if not redis_url:
        checks.extend(
            [
                _skip("redis_live_ping", "redis_url_not_configured", configured=False),
                _skip("redis_distributed_counter", "redis_url_not_configured", configured=False),
                _skip("redis_light_load", "redis_url_not_configured", configured=False),
            ]
        )
    elif not real_calls:
        checks.extend(
            [
                _skip("redis_live_ping", "real_calls_disabled", configured=True),
                _skip("redis_distributed_counter", "real_calls_disabled", configured=True),
                _skip("redis_light_load", "real_calls_disabled", configured=True),
            ]
        )
    else:
        checks.extend(
            [
                verify_live_redis_ping(redis_url, timeout_seconds),
                verify_distributed_counter(redis_url),
                verify_light_load(redis_url, request_count),
            ]
        )

    failed = [item for item in checks if item["status"] == "failed"]
    passed = [item for item in checks if item["status"] == "passed"]
    skipped = [item for item in checks if item["status"] == "skipped"]
    live_checks = {item["id"]: item["status"] for item in checks if item["id"] != "redis_fallback_secret_redaction"}
    return {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "projectId": "ai-language-partner-mobile-shared-20260629-v1",
        "realCallsEnabled": real_calls,
        "redisUrlConfigured": bool(redis_url),
        "redisUrlReturned": False,
        "secretsReturned": False,
        "timeoutSeconds": timeout_seconds,
        "requestCount": request_count,
        "passed": not failed,
        "realRedisEvidenceComplete": real_calls and bool(redis_url) and not failed and all(status == "passed" for status in live_checks.values()),
        "summary": {
            "passed": len(passed),
            "skipped": len(skipped),
            "failed": len(failed),
        },
        "checks": {item["id"]: item for item in checks},
    }


def _public_readiness_result(result: dict[str, Any]) -> dict[str, Any]:
    checks = result.get("checks", {})
    return {
        "passed": bool(result.get("passed")),
        "realRedisEvidenceComplete": bool(result.get("realRedisEvidenceComplete")),
        "summary": {
            str(key): int(value)
            for key, value in result.get("summary", {}).items()
            if isinstance(value, int) and not isinstance(value, bool)
        },
        "checks": {
            str(check_id): {
                "id": str(item.get("id", check_id)),
                "status": str(item.get("status", "unknown")),
                "configured": bool(item.get("configured")),
            }
            for check_id, item in checks.items()
            if isinstance(item, Mapping)
        },
    }


def main() -> int:
    result = verify_redis_rate_limit_readiness()
    print(json.dumps(_public_readiness_result(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
