from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int
    limit_per_minute: int
    backend: str
    remaining: Optional[int] = None


class NoopRateLimiter:
    backend = "none"

    def __init__(self, limit_per_minute: int = 0):
        self.limit_per_minute = max(0, int(limit_per_minute))

    def check(self, client_id: str, path: str, now: Optional[float] = None) -> RateLimitDecision:
        return RateLimitDecision(True, 0, self.limit_per_minute, self.backend, remaining=None)

    def describe(self) -> Dict[str, Any]:
        return {"backend": self.backend, "limitPerMinute": self.limit_per_minute, "distributed": False}


class InMemoryRateLimiter:
    backend = "memory"

    def __init__(self, limit_per_minute: int, requested_backend: str = "memory", fallback_reason: Optional[str] = None):
        self.limit_per_minute = max(0, int(limit_per_minute))
        self.requested_backend = requested_backend
        self.fallback_reason = fallback_reason
        self._buckets: Dict[tuple[str, str, int], int] = {}

    def check(self, client_id: str, path: str, now: Optional[float] = None) -> RateLimitDecision:
        if self.limit_per_minute <= 0:
            return RateLimitDecision(True, 0, self.limit_per_minute, self.backend, remaining=None)
        timestamp = now if now is not None else time.time()
        window = int(timestamp // 60)
        key = (client_id or "unknown", path, window)
        self._buckets[key] = self._buckets.get(key, 0) + 1
        for old_key in list(self._buckets):
            if old_key[2] < window:
                self._buckets.pop(old_key, None)
        used = self._buckets[key]
        retry_after = max(1, 60 - int(timestamp % 60))
        return RateLimitDecision(
            allowed=used <= self.limit_per_minute,
            retry_after_seconds=retry_after if used > self.limit_per_minute else 0,
            limit_per_minute=self.limit_per_minute,
            backend=self.backend,
            remaining=max(0, self.limit_per_minute - used),
        )

    def describe(self) -> Dict[str, Any]:
        description = {
            "backend": self.backend,
            "requestedBackend": self.requested_backend,
            "limitPerMinute": self.limit_per_minute,
            "distributed": False,
        }
        if self.fallback_reason:
            description["fallbackReason"] = self.fallback_reason
        return description


class RedisRateLimiter:
    backend = "redis"

    def __init__(self, limit_per_minute: int, redis_url: str):
        import redis  # type: ignore

        self.limit_per_minute = max(0, int(limit_per_minute))
        self.redis_url = redis_url
        self._client = redis.Redis.from_url(redis_url)
        self._client.ping()

    def check(self, client_id: str, path: str, now: Optional[float] = None) -> RateLimitDecision:
        if self.limit_per_minute <= 0:
            return RateLimitDecision(True, 0, self.limit_per_minute, self.backend, remaining=None)
        timestamp = now if now is not None else time.time()
        window = int(timestamp // 60)
        key = f"ai_language_partner:rate:{window}:{client_id or 'unknown'}:{path}"
        used = int(self._client.incr(key))
        if used == 1:
            self._client.expire(key, 90)
        retry_after = max(1, 60 - int(timestamp % 60))
        return RateLimitDecision(
            allowed=used <= self.limit_per_minute,
            retry_after_seconds=retry_after if used > self.limit_per_minute else 0,
            limit_per_minute=self.limit_per_minute,
            backend=self.backend,
            remaining=max(0, self.limit_per_minute - used),
        )

    def describe(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "requestedBackend": self.backend,
            "limitPerMinute": self.limit_per_minute,
            "distributed": True,
            "redisConfigured": bool(self.redis_url),
            "secretsReturned": False,
        }


def build_rate_limiter(env: Optional[Dict[str, str]] = None):
    values = env or os.environ
    limit = int(values.get("AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE", "240"))
    backend = values.get("AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND", "memory").strip().lower()
    if limit <= 0 or backend in {"none", "off", "disabled"}:
        return NoopRateLimiter(limit)
    if backend == "redis":
        redis_url = values.get("AI_LANGUAGE_PARTNER_REDIS_URL", "redis://localhost:6379/0")
        try:
            return RedisRateLimiter(limit, redis_url)
        except Exception as exc:
            return InMemoryRateLimiter(limit, requested_backend="redis", fallback_reason=f"redis_unavailable:{exc.__class__.__name__}")
    return InMemoryRateLimiter(limit, requested_backend=backend)
