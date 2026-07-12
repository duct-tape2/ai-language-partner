from __future__ import annotations

import csv
import base64
import hashlib
import html
import hmac
import ipaddress
import io
import json
import logging
import os
import secrets
import sqlite3
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union

import genanki
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field, ValidationError

from .dialogue_match import DialogueMatcher, list_dialogue_packs
from .learner_model import MODEL_NAME as OFFLINE_LEARNER_MEMORY_MODEL_NAME
from .paths import resolve_project_root
from .providers import MockLLMProvider, MockPronunciationScorer, MockSTTProvider, MockTTSProvider, build_provider_stack, load_voice_catalog, tts_cache_key
from .rate_limit import build_rate_limiter
from .reputation_model import MODEL_NAME as OFFLINE_REPUTATION_MODEL_NAME
from .store import ApiStore, audit_subject_hash, default_db_path, normalize_experiment_key, normalize_learner_id

PROJECT_ID = "ai-language-partner-mobile-shared-20260629-v1"
PROJECT_ROOT = resolve_project_root(Path(__file__))
DIALOGUE_PACKS_ROOT = PROJECT_ROOT / "packs"
MAX_STT_HINT_LINE_IDS = 100
MAX_STT_HINT_LINE_ID_LENGTH = 160
LOGGER = logging.getLogger(__name__)
_EMAIL_HASH_SECRET = (
    os.environ.get("AI_LANGUAGE_PARTNER_EMAIL_HASH_SECRET")
    or os.environ.get("AI_LANGUAGE_PARTNER_JWT_SECRET")
    or os.environ.get("AI_LANGUAGE_PARTNER_AUTH_SECRET")
    or ""
).strip()
_EMAIL_HASH_KEY = (
    hmac.new(_EMAIL_HASH_SECRET.encode("utf-8"), b"ai-language-partner:email-hash:v1", hashlib.sha256).digest()
    if _EMAIL_HASH_SECRET
    else secrets.token_bytes(32)
)
_LOCAL_ANKI_CONNECT_V4_URL = "http://127.0.0.1:8765/"
_LOCAL_ANKI_CONNECT_V6_URL = "http://[::1]:8765/"
P256_P = int("ffffffff00000001000000000000000000000000ffffffffffffffffffffffff", 16)
P256_A = -3
P256_B = int("5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b", 16)
P256_N = int("ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551", 16)
P256_G = (
    int("6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296", 16),
    int("4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5", 16),
)
PKCE_ALLOWED_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
DEFAULT_ALLOWED_EVENT_NAMES = {
    "app_opened",
    "home_today_viewed",
    "persona_selected",
    "practice_room_opened",
    "practice_room_started",
    "conversation_started",
    "first_tts_played",
    "first_user_reply_submitted",
    "first_correction_shown",
    "practice_turn_completed",
    "review_card_created",
    "review_card_saved",
    "review_card_graded",
    "pronunciation_scored",
    "practice_room_completed",
    "day1_returned",
    "pricing_plan_clicked",
    "voice_limit_hit",
    "backend_health_checked",
    "api_error_seen",
}


def _load_allowed_event_names() -> set[str]:
    event_contract = PROJECT_ROOT / "contracts" / "events.yaml"
    if not event_contract.exists():
        return set(DEFAULT_ALLOWED_EVENT_NAMES)
    parsed = {
        line.strip().removeprefix("-").strip()
        for line in event_contract.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- ")
    }
    return parsed or set(DEFAULT_ALLOWED_EVENT_NAMES)


ALLOWED_EVENT_NAMES = _load_allowed_event_names()


def _cors_origins_from_env() -> list[str]:
    raw = os.environ.get(
        "AI_LANGUAGE_PARTNER_CORS_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8081,http://localhost:19006",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _auth_mode() -> str:
    return os.environ.get("AI_LANGUAGE_PARTNER_AUTH_MODE", "dev").strip().lower()


def _password_hash_iterations() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_PASSWORD_HASH_ITERATIONS", "210000"))


def _access_token_ttl_seconds() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_ACCESS_TOKEN_TTL_SECONDS", "900"))


def _refresh_token_ttl_seconds() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_REFRESH_TOKEN_TTL_SECONDS", str(30 * 24 * 3600)))


def _jwt_issuer() -> str:
    return os.environ.get("AI_LANGUAGE_PARTNER_JWT_ISSUER", PROJECT_ID).strip() or PROJECT_ID


def _jwt_audience() -> str:
    return os.environ.get("AI_LANGUAGE_PARTNER_JWT_AUDIENCE", "ai-language-partner-mobile").strip() or "ai-language-partner-mobile"


def _jwt_secret() -> Optional[str]:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_JWT_SECRET") or os.environ.get("AI_LANGUAGE_PARTNER_AUTH_SECRET")
    if configured:
        return configured
    if _auth_mode() == "dev":
        return "local-dev-jwt-secret"
    return None


def _auth_max_failures() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_AUTH_MAX_FAILURES", "8"))


def _auth_failure_window_seconds() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_AUTH_FAILURE_WINDOW_SECONDS", "900"))


def _auth_risk_max_distinct_emails() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_AUTH_RISK_MAX_DISTINCT_EMAILS", "12"))


def _auth_risk_window_seconds() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_AUTH_RISK_WINDOW_SECONDS", "900"))


def _auth_register_max_attempts() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_AUTH_REGISTER_MAX_ATTEMPTS", "5"))


def _auth_register_window_seconds() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_AUTH_REGISTER_WINDOW_SECONDS", "3600"))


def _device_attestation_secret() -> Optional[str]:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET")
    return configured.strip() if configured and configured.strip() else None


DEVICE_ATTESTATION_HMAC_PROVIDERS = {"signed_challenge", "hmac_signed_challenge"}
DEVICE_ATTESTATION_PUBLIC_KEY_PROVIDERS = {"public_key_challenge", "webauthn_public_key"}
DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS = {"webauthn_public_key"}


def _device_attestation_challenge_ttl_seconds() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_CHALLENGE_TTL_SECONDS", "300"))


def _platform_attestation_verification_status() -> str:
    return "signed_challenge_hmac" if _device_attestation_secret() else "not_configured"


def _provider_env_key(provider: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in provider.upper())
    return cleaned.strip("_") or "OIDC"


def _oidc_allowed_providers() -> list[str]:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS")
    if configured is None and _auth_mode() == "dev":
        configured = "local-oidc"
    return [item.strip().lower() for item in (configured or "").split(",") if item.strip()]


def _oidc_issuer(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    return (
        os.environ.get(f"AI_LANGUAGE_PARTNER_OIDC_{key}_ISSUER")
        or os.environ.get("AI_LANGUAGE_PARTNER_OIDC_ISSUER")
        or ("https://local-oidc.example" if _auth_mode() == "dev" else None)
    )


def _oidc_audience(provider: str) -> str:
    key = _provider_env_key(provider)
    return (
        os.environ.get(f"AI_LANGUAGE_PARTNER_OIDC_{key}_AUDIENCE")
        or os.environ.get("AI_LANGUAGE_PARTNER_OIDC_AUDIENCE")
        or _jwt_audience()
    ).strip()


def _oidc_hs256_secret(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    configured = os.environ.get(f"AI_LANGUAGE_PARTNER_OIDC_{key}_HS256_SECRET") or os.environ.get("AI_LANGUAGE_PARTNER_OIDC_HS256_SECRET")
    if configured:
        return configured
    if _auth_mode() == "dev":
        return _jwt_secret()
    return None


def _oidc_jwks_json(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    return os.environ.get(f"AI_LANGUAGE_PARTNER_OIDC_{key}_JWKS_JSON") or os.environ.get("AI_LANGUAGE_PARTNER_OIDC_JWKS_JSON")


def _oidc_jwks_url(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    return os.environ.get(f"AI_LANGUAGE_PARTNER_OIDC_{key}_JWKS_URL") or os.environ.get("AI_LANGUAGE_PARTNER_OIDC_JWKS_URL")


def _oidc_jwks_configured(provider: str) -> bool:
    return bool(_oidc_jwks_json(provider) or _oidc_jwks_url(provider))


def _oidc_any_jwks_configured() -> bool:
    return any(_oidc_jwks_configured(provider) for provider in _oidc_allowed_providers())


def _load_oidc_jwks(provider: str) -> Optional[Dict[str, Any]]:
    configured_json = _oidc_jwks_json(provider)
    if configured_json:
        try:
            parsed = json.loads(configured_json)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    configured_url = _oidc_jwks_url(provider)
    if configured_url:
        try:
            with urllib.request.urlopen(configured_url, timeout=3) as response:
                parsed = json.loads(response.read().decode("utf-8"))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


def _oidc_require_email_verified() -> bool:
    return os.environ.get("AI_LANGUAGE_PARTNER_OIDC_REQUIRE_EMAIL_VERIFIED", "true").strip().lower() not in {"0", "false", "no"}


def _oauth_pkce_ttl_seconds() -> int:
    return int(os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_PKCE_TTL_SECONDS", "600"))


def _oauth_authorization_endpoint(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    configured = (
        os.environ.get(f"AI_LANGUAGE_PARTNER_OAUTH_{key}_AUTHORIZATION_ENDPOINT")
        or os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_AUTHORIZATION_ENDPOINT")
    )
    if configured:
        return configured.strip()
    if _auth_mode() == "dev":
        return "https://local-oidc.example/oauth/authorize"
    return None


def _oauth_token_endpoint(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    configured = (
        os.environ.get(f"AI_LANGUAGE_PARTNER_OAUTH_{key}_TOKEN_ENDPOINT")
        or os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_TOKEN_ENDPOINT")
    )
    return configured.strip() if configured else None


def _oauth_client_id(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    configured = (
        os.environ.get(f"AI_LANGUAGE_PARTNER_OAUTH_{key}_CLIENT_ID")
        or os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_CLIENT_ID")
    )
    if configured:
        return configured.strip()
    if _auth_mode() == "dev":
        return _oidc_audience(provider)
    return None


def _oauth_client_secret(provider: str) -> Optional[str]:
    key = _provider_env_key(provider)
    configured = (
        os.environ.get(f"AI_LANGUAGE_PARTNER_OAUTH_{key}_CLIENT_SECRET")
        or os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_CLIENT_SECRET")
    )
    return configured.strip() if configured else None


def _oauth_default_scope(provider: str) -> str:
    key = _provider_env_key(provider)
    configured = os.environ.get(f"AI_LANGUAGE_PARTNER_OAUTH_{key}_SCOPES") or os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_SCOPES")
    return (configured or "openid email profile").strip()


def _oauth_redirect_uri_allowed(provider: str, redirect_uri: str) -> bool:
    uri = (redirect_uri or "").strip()
    if not uri:
        return False
    key = _provider_env_key(provider)
    configured = (
        os.environ.get(f"AI_LANGUAGE_PARTNER_OAUTH_{key}_REDIRECT_URIS")
        or os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_REDIRECT_URIS")
    )
    allowed = [item.strip() for item in (configured or "").split(",") if item.strip()]
    if uri in allowed:
        return True
    parsed = urllib.parse.urlparse(uri)
    if not parsed.scheme:
        return False
    if _auth_mode() == "dev":
        if parsed.scheme in {"http", "https"} and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            return True
        if parsed.scheme in {"exp", "ai-language-partner"}:
            return True
    return False


def _email_domain(email: str) -> str:
    _, _, domain = (email or "").strip().lower().rpartition("@")
    return domain


def _public_enterprise_sso_connection(connection: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": connection["id"],
        "provider": connection["provider"],
        "organizationName": connection["organizationName"],
        "domains": connection.get("domains") or [],
        "redirectUris": connection.get("redirectUris") or [],
        "requiredEmailDomain": connection.get("requiredEmailDomain"),
        "status": connection["status"],
        "enabled": bool(connection.get("enabled")),
        "createdAt": connection.get("createdAt"),
        "updatedAt": connection.get("updatedAt"),
    }


def _enterprise_sso_redirect_uri_allowed(connection: Dict[str, Any], redirect_uri: str) -> bool:
    uri = (redirect_uri or "").strip()
    if not uri:
        return False
    allowed_by_connection = uri in set(connection.get("redirectUris") or [])
    return allowed_by_connection and _oauth_redirect_uri_allowed(connection["provider"], uri)


def _enterprise_sso_email_allowed(connection: Dict[str, Any], email: str) -> bool:
    domain = _email_domain(email)
    if not domain:
        return False
    required_domain = connection.get("requiredEmailDomain")
    if required_domain and domain != required_domain:
        return False
    return domain in set(connection.get("domains") or [])


def _oauth_local_signed_code_allowed() -> bool:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_OAUTH_ALLOW_LOCAL_SIGNED_CODE")
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes"}
    return _auth_mode() == "dev"


def _oauth_pkce_configured_providers() -> list[str]:
    providers = []
    for provider in _oidc_allowed_providers():
        if _oauth_authorization_endpoint(provider) and _oauth_client_id(provider):
            providers.append(provider)
    return providers


def _oauth_token_exchange_configured_providers() -> list[str]:
    return [provider for provider in _oidc_allowed_providers() if bool(_oauth_token_endpoint(provider))]


def _pkce_token_valid(value: str) -> bool:
    return 43 <= len(value) <= 128 and all(ch in PKCE_ALLOWED_CHARS for ch in value)


def _pkce_s256_challenge(code_verifier: str) -> str:
    return _b64url_encode(hashlib.sha256(code_verifier.encode("ascii")).digest())


def _oauth_state_hash(state: str) -> str:
    return hashlib.sha256(("oauth_state:" + state).encode("utf-8")).hexdigest()


def _device_attestation_challenge_hash(challenge: str) -> str:
    return hashlib.sha256(("device_attestation:" + challenge).encode("utf-8")).hexdigest()


def _device_attestation_message(
    provider: str,
    challenge_id: str,
    challenge: str,
    attestation_subject: str,
) -> str:
    return json.dumps(
        {
            "attestationProvider": provider.strip().lower(),
            "attestationSubject": attestation_subject.strip(),
            "challenge": challenge.strip(),
            "challengeId": challenge_id.strip(),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _device_attestation_hmac_signature(
    secret: str,
    provider: str,
    challenge_id: str,
    challenge: str,
    attestation_subject: str,
) -> str:
    message = _device_attestation_message(provider, challenge_id, challenge, attestation_subject)
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def _device_attestation_public_key_jwk(attestation_subject: str, evidence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    candidate = evidence.get("publicKeyJwk") or evidence.get("public_key_jwk") or attestation_subject
    if isinstance(candidate, dict):
        return candidate
    if isinstance(candidate, str) and candidate.strip():
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


def _public_jwk_thumbprint(jwk: Dict[str, Any]) -> str:
    if jwk.get("kty") == "EC":
        thumbprint_keys = ("crv", "kty", "x", "y")
    else:
        thumbprint_keys = ("e", "kty", "n")
    public_fields = {key: jwk[key] for key in thumbprint_keys if key in jwk}
    canonical = json.dumps(public_fields or jwk, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _oauth_authorization_url(
    provider: str,
    redirect_uri: str,
    state: str,
    nonce: str,
    code_challenge: str,
    scope: str,
) -> str:
    endpoint = _oauth_authorization_endpoint(provider)
    client_id = _oauth_client_id(provider)
    if not endpoint or not client_id:
        raise HTTPException(status_code=503, detail="OAuth provider is not configured")
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    separator = "&" if "?" in endpoint else "?"
    return endpoint + separator + urllib.parse.urlencode(params)


def _future_iso(seconds: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(time.time()) + int(seconds)))


def _past_iso(seconds: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(time.time()) - int(seconds)))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padded = raw + "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _jwt_json(value: Dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sign_hs256(signing_input: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(signature)


def _jwk_int(jwk: Dict[str, Any], key: str) -> int:
    value = jwk.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing RSA JWK field: {key}")
    return int.from_bytes(_b64url_decode(value), "big")


def _rsa_public_key_from_jwk(jwk: Dict[str, Any]) -> rsa.RSAPublicKey:
    if jwk.get("kty") != "RSA" or jwk.get("use", "sig") != "sig":
        raise ValueError("JWK is not an RSA signing key")
    if jwk.get("alg") not in {None, "RS256"}:
        raise ValueError("JWK does not permit RS256")
    return rsa.RSAPublicNumbers(_jwk_int(jwk, "e"), _jwk_int(jwk, "n")).public_key()


def _rsa_private_key_from_jwk(jwk: Dict[str, Any]) -> rsa.RSAPrivateKey:
    public_numbers = _rsa_public_key_from_jwk(jwk).public_numbers()
    d = _jwk_int(jwk, "d")
    if "p" in jwk and "q" in jwk:
        p = _jwk_int(jwk, "p")
        q = _jwk_int(jwk, "q")
    else:
        p, q = rsa.rsa_recover_prime_factors(public_numbers.n, public_numbers.e, d)
    return rsa.RSAPrivateNumbers(
        p=p,
        q=q,
        d=d,
        dmp1=rsa.rsa_crt_dmp1(d, p),
        dmq1=rsa.rsa_crt_dmq1(d, q),
        iqmp=rsa.rsa_crt_iqmp(p, q),
        public_numbers=public_numbers,
    ).private_key()


def _verify_rs256_with_jwk(signing_input: str, signature: str, jwk: Dict[str, Any]) -> bool:
    try:
        _rsa_public_key_from_jwk(jwk).verify(
            _b64url_decode(signature),
            signing_input.encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except (InvalidSignature, ValueError, TypeError, OverflowError):
        return False
    return True


def _sign_rs256_with_jwk(signing_input: str, private_jwk: Dict[str, Any]) -> str:
    signature = _rsa_private_key_from_jwk(private_jwk).sign(
        signing_input.encode("ascii"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return _b64url_encode(signature)


def _verify_rs256_with_jwks(signing_input: str, signature: str, header: Dict[str, Any], jwks: Optional[Dict[str, Any]]) -> bool:
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    if not isinstance(keys, list):
        return False
    kid = header.get("kid")
    for jwk in keys:
        if not isinstance(jwk, dict):
            continue
        if kid and jwk.get("kid") != kid:
            continue
        if _verify_rs256_with_jwk(signing_input, signature, jwk):
            return True
    return False


def _p256_point_on_curve(point: tuple[int, int]) -> bool:
    x, y = point
    if not (0 <= x < P256_P and 0 <= y < P256_P):
        return False
    return (y * y - (x * x * x + P256_A * x + P256_B)) % P256_P == 0


def _p256_point_add(left: Optional[tuple[int, int]], right: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % P256_P == 0:
        return None
    if left == right:
        numerator = (3 * x1 * x1 + P256_A) % P256_P
        denominator = pow((2 * y1) % P256_P, -1, P256_P)
    else:
        numerator = (y2 - y1) % P256_P
        denominator = pow((x2 - x1) % P256_P, -1, P256_P)
    slope = (numerator * denominator) % P256_P
    x3 = (slope * slope - x1 - x2) % P256_P
    y3 = (slope * (x1 - x3) - y1) % P256_P
    return (x3, y3)


def _p256_point_mul(scalar: int, point: tuple[int, int] = P256_G) -> Optional[tuple[int, int]]:
    scalar = scalar % P256_N
    result: Optional[tuple[int, int]] = None
    addend: Optional[tuple[int, int]] = point
    while scalar:
        if scalar & 1:
            result = _p256_point_add(result, addend)
        addend = _p256_point_add(addend, addend)
        scalar >>= 1
    return result


def _parse_ecdsa_signature(signature_bytes: bytes) -> Optional[tuple[int, int]]:
    if len(signature_bytes) == 64:
        return (int.from_bytes(signature_bytes[:32], "big"), int.from_bytes(signature_bytes[32:], "big"))
    if len(signature_bytes) < 8 or signature_bytes[0] != 0x30:
        return None
    try:
        idx = 2
        total_len = signature_bytes[1]
        if total_len & 0x80:
            len_len = total_len & 0x7F
            total_len = int.from_bytes(signature_bytes[idx : idx + len_len], "big")
            idx += len_len
        if idx + total_len != len(signature_bytes) or signature_bytes[idx] != 0x02:
            return None
        r_len = signature_bytes[idx + 1]
        idx += 2
        r = int.from_bytes(signature_bytes[idx : idx + r_len], "big")
        idx += r_len
        if idx >= len(signature_bytes) or signature_bytes[idx] != 0x02:
            return None
        s_len = signature_bytes[idx + 1]
        idx += 2
        s = int.from_bytes(signature_bytes[idx : idx + s_len], "big")
        if idx + s_len != len(signature_bytes):
            return None
        return (r, s)
    except Exception:
        return None


def _der_encode_ecdsa_signature(r: int, s: int) -> bytes:
    def encode_int(value: int) -> bytes:
        raw = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
        raw = raw.lstrip(b"\x00") or b"\x00"
        if raw[0] & 0x80:
            raw = b"\x00" + raw
        return b"\x02" + len(raw).to_bytes(1, "big") + raw

    payload = encode_int(r) + encode_int(s)
    return b"\x30" + len(payload).to_bytes(1, "big") + payload


def _verify_es256_with_jwk(message: bytes, signature: str, jwk: Dict[str, Any]) -> bool:
    if jwk.get("kty") != "EC" or jwk.get("crv") != "P-256" or jwk.get("use", "sig") != "sig":
        return False
    if jwk.get("alg") not in {None, "ES256"}:
        return False
    try:
        x = _jwk_int(jwk, "x")
        y = _jwk_int(jwk, "y")
        parsed_signature = _parse_ecdsa_signature(_b64url_decode(signature))
    except Exception:
        return False
    if not parsed_signature:
        return False
    public_point = (x, y)
    if not _p256_point_on_curve(public_point):
        return False
    r, s = parsed_signature
    if not (1 <= r < P256_N and 1 <= s < P256_N):
        return False
    z = int.from_bytes(hashlib.sha256(message).digest(), "big")
    w = pow(s, -1, P256_N)
    u1 = (z * w) % P256_N
    u2 = (r * w) % P256_N
    point = _p256_point_add(_p256_point_mul(u1, P256_G), _p256_point_mul(u2, public_point))
    return bool(point and point[0] % P256_N == r)


def _sign_es256_with_jwk(message: bytes, private_jwk: Dict[str, Any], der: bool = True) -> str:
    d = _jwk_int(private_jwk, "d")
    if not (1 <= d < P256_N):
        raise ValueError("Invalid P-256 private key")
    z = int.from_bytes(hashlib.sha256(message).digest(), "big")
    seed = hashlib.sha256(d.to_bytes(32, "big") + hashlib.sha256(message).digest() + b":ai_language_partner_es256").digest()
    k = int.from_bytes(seed, "big") % P256_N
    if k == 0:
        k = 1
    while True:
        point = _p256_point_mul(k, P256_G)
        if not point:
            k = (k + 1) % P256_N or 1
            continue
        r = point[0] % P256_N
        s = (pow(k, -1, P256_N) * (z + r * d)) % P256_N
        if r and s:
            break
        k = (k + 1) % P256_N or 1
    if s > P256_N // 2:
        s = P256_N - s
    raw = _der_encode_ecdsa_signature(r, s) if der else r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return _b64url_encode(raw)


def _webauthn_allowed_origins() -> set[str]:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_WEBAUTHN_ALLOWED_ORIGINS")
    if configured:
        return {item.strip() for item in configured.split(",") if item.strip()}
    if _auth_mode() == "dev":
        return {
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8081",
            "http://localhost:19006",
        }
    return set()


def _webauthn_rp_id() -> str:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_WEBAUTHN_RP_ID")
    if configured and configured.strip():
        return configured.strip()
    return "localhost" if _auth_mode() == "dev" else _jwt_audience()


def _decode_webauthn_client_data(value: str) -> tuple[Optional[Dict[str, Any]], bytes]:
    raw = value.strip()
    if not raw:
        return None, b""
    try:
        decoded = raw.encode("utf-8") if raw.startswith("{") else _b64url_decode(raw)
        parsed = json.loads(decoded.decode("utf-8"))
        return (parsed if isinstance(parsed, dict) else None, decoded)
    except Exception:
        return None, b""


def _client_data_challenge_matches(client_challenge: Any, challenge: str) -> bool:
    if client_challenge == challenge:
        return True
    if isinstance(client_challenge, str):
        if client_challenge == _b64url_encode(challenge.encode("utf-8")):
            return True
        try:
            return _b64url_decode(client_challenge).decode("utf-8") == challenge
        except Exception:
            return False
    return False


def _verify_webauthn_es256_assertion(
    challenge: str,
    signature: str,
    public_jwk: Dict[str, Any],
    evidence: Dict[str, Any],
) -> tuple[bool, Dict[str, Any], str]:
    client_data, client_data_json = _decode_webauthn_client_data(str(evidence.get("clientDataJSON") or evidence.get("client_data_json") or ""))
    if not client_data:
        return False, {}, "invalid_client_data_json"
    if client_data.get("type") != "webauthn.get":
        return False, {}, "invalid_client_data_type"
    if not _client_data_challenge_matches(client_data.get("challenge"), challenge):
        return False, {}, "challenge_mismatch"
    origin = str(client_data.get("origin") or "").strip()
    allowed_origins = _webauthn_allowed_origins()
    if not origin or (allowed_origins and origin not in allowed_origins):
        return False, {"origin": origin}, "origin_not_allowed"
    try:
        authenticator_data = _b64url_decode(str(evidence.get("authenticatorData") or evidence.get("authenticator_data") or ""))
    except Exception:
        return False, {"origin": origin}, "invalid_authenticator_data"
    if len(authenticator_data) < 37:
        return False, {"origin": origin}, "invalid_authenticator_data"
    rp_id = _webauthn_rp_id()
    expected_rp_hash = hashlib.sha256(rp_id.encode("utf-8")).digest()
    if not hmac.compare_digest(authenticator_data[:32], expected_rp_hash):
        return False, {"origin": origin, "rpId": rp_id}, "rp_id_hash_mismatch"
    flags = authenticator_data[32]
    user_present = bool(flags & 0x01)
    user_verified = bool(flags & 0x04)
    if not user_present:
        return False, {"origin": origin, "rpId": rp_id, "userPresent": False}, "user_presence_required"
    sign_count = int.from_bytes(authenticator_data[33:37], "big")
    signed_message = authenticator_data + hashlib.sha256(client_data_json).digest()
    valid = _verify_es256_with_jwk(signed_message, signature, public_jwk)
    metadata = {
        "origin": origin,
        "rpId": rp_id,
        "userPresent": user_present,
        "userVerified": user_verified,
        "signCount": sign_count,
        "clientDataJsonHash": hashlib.sha256(client_data_json).hexdigest(),
        "authenticatorDataHash": hashlib.sha256(authenticator_data).hexdigest(),
    }
    return valid, metadata, "bad_signature" if not valid else "verified"


def _create_account_access_jwt(account: Dict[str, Any], expires_at_unix: int, jti: str, device_bound: bool = False) -> str:
    secret = _jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="AI_LANGUAGE_PARTNER_JWT_SECRET is required for account JWT access tokens")
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": _jwt_issuer(),
        "aud": _jwt_audience(),
        "sub": account["id"],
        "learnerId": account["learnerId"],
        "emailHash": _email_hash(account["email"]),
        "jti": jti,
        "typ": "access",
        "iat": now,
        "nbf": now - 5,
        "exp": int(expires_at_unix),
        "deviceBound": bool(device_bound),
        "projectId": PROJECT_ID,
    }
    encoded_header = _b64url_encode(_jwt_json(header))
    encoded_payload = _b64url_encode(_jwt_json(payload))
    signing_input = f"{encoded_header}.{encoded_payload}"
    return f"{signing_input}.{_sign_hs256(signing_input, secret)}"


def _decode_account_access_jwt(token: str, now_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
    secret = _jwt_secret()
    if not token or token.count(".") != 2 or not secret:
        return None
    try:
        encoded_header, encoded_payload, signature = token.split(".", 2)
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = _sign_hs256(signing_input, secret)
        if not hmac.compare_digest(signature, expected):
            return None
        header = json.loads(_b64url_decode(encoded_header).decode("utf-8"))
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    except Exception:
        return None
    if header.get("alg") != "HS256" or payload.get("typ") != "access":
        return None
    now = now_seconds if now_seconds is not None else int(time.time())
    if payload.get("iss") != _jwt_issuer() or payload.get("aud") != _jwt_audience():
        return None
    if int(payload.get("nbf") or 0) > now:
        return None
    if int(payload.get("exp") or 0) <= now:
        return None
    if not payload.get("sub") or not payload.get("jti") or not payload.get("learnerId"):
        return None
    return payload


def create_oidc_id_token(
    provider: str,
    subject: str,
    email: str,
    secret: str,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    ttl_seconds: int = 3600,
    email_verified: bool = True,
    nonce: Optional[str] = None,
) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: Dict[str, Any] = {
        "iss": issuer or _oidc_issuer(provider),
        "aud": audience or _oidc_audience(provider),
        "sub": subject,
        "email": email,
        "email_verified": bool(email_verified),
        "iat": now,
        "nbf": now - 5,
        "exp": now + int(ttl_seconds),
    }
    if nonce:
        payload["nonce"] = nonce
    encoded_header = _b64url_encode(_jwt_json(header))
    encoded_payload = _b64url_encode(_jwt_json(payload))
    signing_input = f"{encoded_header}.{encoded_payload}"
    return f"{signing_input}.{_sign_hs256(signing_input, secret)}"


def create_oidc_rs256_id_token(
    provider: str,
    subject: str,
    email: str,
    private_jwk: Dict[str, Any],
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    ttl_seconds: int = 3600,
    email_verified: bool = True,
    nonce: Optional[str] = None,
    kid: Optional[str] = None,
) -> str:
    now = int(time.time())
    header: Dict[str, Any] = {"alg": "RS256", "typ": "JWT"}
    key_id = kid or private_jwk.get("kid")
    if key_id:
        header["kid"] = key_id
    payload: Dict[str, Any] = {
        "iss": issuer or _oidc_issuer(provider),
        "aud": audience or _oidc_audience(provider),
        "sub": subject,
        "email": email,
        "email_verified": bool(email_verified),
        "iat": now,
        "nbf": now - 5,
        "exp": now + int(ttl_seconds),
    }
    if nonce:
        payload["nonce"] = nonce
    encoded_header = _b64url_encode(_jwt_json(header))
    encoded_payload = _b64url_encode(_jwt_json(payload))
    signing_input = f"{encoded_header}.{encoded_payload}"
    return f"{signing_input}.{_sign_rs256_with_jwk(signing_input, private_jwk)}"


def create_oauth_authorization_code(
    provider: str,
    subject: str,
    email: str,
    secret: Optional[str] = None,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    ttl_seconds: int = 300,
    email_verified: bool = True,
    nonce: Optional[str] = None,
    state: Optional[str] = None,
) -> str:
    signing_secret = secret or _oidc_hs256_secret(provider)
    if not signing_secret:
        raise ValueError("OAuth local signed code requires a configured HS256 secret")
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: Dict[str, Any] = {
        "iss": issuer or _oidc_issuer(provider),
        "aud": audience or _oidc_audience(provider),
        "sub": subject,
        "email": email,
        "email_verified": bool(email_verified),
        "token_use": "authorization_code",
        "iat": now,
        "nbf": now - 5,
        "exp": now + int(ttl_seconds),
    }
    if nonce:
        payload["nonce"] = nonce
    if state:
        payload["state"] = state
    encoded_header = _b64url_encode(_jwt_json(header))
    encoded_payload = _b64url_encode(_jwt_json(payload))
    signing_input = f"{encoded_header}.{encoded_payload}"
    return f"{signing_input}.{_sign_hs256(signing_input, signing_secret)}"


def _decode_oauth_authorization_code(
    provider: str,
    code: str,
    nonce: Optional[str],
    state: str,
    now_seconds: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    normalized_provider = provider.strip().lower()
    if normalized_provider not in _oidc_allowed_providers():
        return None
    issuer = _oidc_issuer(normalized_provider)
    audience = _oidc_audience(normalized_provider)
    secret = _oidc_hs256_secret(normalized_provider)
    if not code or code.count(".") != 2 or not issuer or not audience or not secret:
        return None
    try:
        encoded_header, encoded_payload, signature = code.split(".", 2)
        signing_input = f"{encoded_header}.{encoded_payload}"
        header = json.loads(_b64url_decode(encoded_header).decode("utf-8"))
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    except Exception:
        return None
    if header.get("alg") != "HS256" or payload.get("token_use") != "authorization_code":
        return None
    if not hmac.compare_digest(signature, _sign_hs256(signing_input, secret)):
        return None
    now = now_seconds if now_seconds is not None else int(time.time())
    aud = payload.get("aud")
    audience_ok = audience in aud if isinstance(aud, list) else aud == audience
    if payload.get("iss") != issuer or not audience_ok:
        return None
    if int(payload.get("nbf") or 0) > now or int(payload.get("exp") or 0) <= now:
        return None
    if nonce is not None and payload.get("nonce") != nonce:
        return None
    if payload.get("state") != state:
        return None
    if not payload.get("sub") or not payload.get("email"):
        return None
    if _oidc_require_email_verified() and payload.get("email_verified") is not True:
        return None
    return payload


def _exchange_oauth_code_for_id_token(
    provider: str,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> Optional[str]:
    token_endpoint = _oauth_token_endpoint(provider)
    client_id = _oauth_client_id(provider)
    if not token_endpoint or not client_id:
        return None
    body: Dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    client_secret = _oauth_client_secret(provider)
    if client_secret:
        body["client_secret"] = client_secret
    data = urllib.parse.urlencode(body).encode("utf-8")
    request = urllib.request.Request(
        token_endpoint,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    id_token = parsed.get("id_token") if isinstance(parsed, dict) else None
    return str(id_token) if id_token else None


def _oauth_claims_from_authorization_code(
    provider: str,
    code: str,
    code_verifier: str,
    redirect_uri: str,
    nonce: Optional[str],
    state: str,
) -> tuple[Optional[Dict[str, Any]], str]:
    if _oauth_token_endpoint(provider):
        id_token = _exchange_oauth_code_for_id_token(provider, code, redirect_uri, code_verifier)
        claims = _decode_oidc_id_token(provider, id_token or "", nonce=nonce)
        return claims, "token_endpoint_id_token"
    if _oauth_local_signed_code_allowed():
        return _decode_oauth_authorization_code(provider, code, nonce=nonce, state=state), "local_signed_code"
    return None, "unconfigured"


def _decode_oidc_id_token(
    provider: str,
    token: str,
    nonce: Optional[str] = None,
    now_seconds: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    normalized_provider = provider.strip().lower()
    if normalized_provider not in _oidc_allowed_providers():
        return None
    issuer = _oidc_issuer(normalized_provider)
    audience = _oidc_audience(normalized_provider)
    if not token or token.count(".") != 2 or not issuer or not audience:
        return None
    try:
        encoded_header, encoded_payload, signature = token.split(".", 2)
        signing_input = f"{encoded_header}.{encoded_payload}"
        header = json.loads(_b64url_decode(encoded_header).decode("utf-8"))
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    except Exception:
        return None
    algorithm = header.get("alg")
    if algorithm == "HS256":
        secret = _oidc_hs256_secret(normalized_provider)
        if not secret:
            return None
        expected = _sign_hs256(signing_input, secret)
        if not hmac.compare_digest(signature, expected):
            return None
    elif algorithm == "RS256":
        if not _verify_rs256_with_jwks(signing_input, signature, header, _load_oidc_jwks(normalized_provider)):
            return None
    else:
        return None
    now = now_seconds if now_seconds is not None else int(time.time())
    aud = payload.get("aud")
    audience_ok = audience in aud if isinstance(aud, list) else aud == audience
    if payload.get("iss") != issuer or not audience_ok:
        return None
    if int(payload.get("nbf") or 0) > now or int(payload.get("exp") or 0) <= now:
        return None
    if nonce is not None and payload.get("nonce") != nonce:
        return None
    if not payload.get("sub") or not payload.get("email"):
        return None
    if _oidc_require_email_verified() and payload.get("email_verified") is not True:
        return None
    return payload


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = _password_hash_iterations()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "$".join(
        [
            "pbkdf2_sha256",
            str(iterations),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        ]
    )


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_raw.encode("ascii"))
        expected = base64.b64decode(digest_raw.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations_raw))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Valid email required")
    return normalized[:254]


def _default_account_learner_id(email: str) -> str:
    return "learner_" + _email_hash(email)


def _device_id_hash(device_id: Optional[str]) -> Optional[str]:
    normalized = (device_id or "").strip()
    if not normalized:
        return None
    return hashlib.sha256(normalized[:256].encode("utf-8")).hexdigest()


def _client_hash(request: Request) -> str:
    forwarded = (request.headers.get("X-Forwarded-For") or "").split(",", 1)[0].strip()
    host = forwarded or (request.client.host if request.client else "unknown")
    return hashlib.sha256(host.encode("utf-8")).hexdigest()[:16]


def _email_hash(email: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        email.encode("utf-8"),
        _EMAIL_HASH_KEY,
        120_000,
        dklen=8,
    ).hex()


def _safe_path_segment(value: str, label: str) -> str:
    if (
        not value
        or len(value) > 160
        or value != value.strip()
        or any(not (char.isalnum() or char in {"_", "-"}) for char in value)
    ):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value


def _resolve_contained_path(root: Path, *segments: str) -> Path:
    try:
        root_path = root.resolve()
        candidate = root_path.joinpath(*segments).resolve()
    except (OSError, RuntimeError):
        raise HTTPException(status_code=400, detail="Invalid resource path") from None
    try:
        candidate.relative_to(root_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resource path") from None
    return candidate


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def _local_anki_connect_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit((url or "").strip())
        port = parsed.port
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid AnkiConnect URL") from None
    host = parsed.hostname
    if (
        parsed.scheme.lower() != "http"
        or not host
        or parsed.username
        or parsed.password
        or port != 8765
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise HTTPException(status_code=400, detail="AnkiConnect URL must use the local service")
    if host == "localhost":
        address = ipaddress.ip_address("127.0.0.1")
    else:
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            raise HTTPException(status_code=400, detail="AnkiConnect URL must use the local service") from None
    if not address.is_loopback:
        raise HTTPException(status_code=400, detail="AnkiConnect URL must use the local service")
    return _LOCAL_ANKI_CONNECT_V6_URL if address.version == 6 else _LOCAL_ANKI_CONNECT_V4_URL


def _post_to_local_anki_connect(url: str, body: bytes) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    # Never let a process-wide proxy reroute data intended for local AnkiConnect.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirectHandler())
    with opener.open(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def create_signed_learner_token(learner_id: str, secret: str, ttl_seconds: int = 3600) -> str:
    normalized = normalize_learner_id(learner_id)
    expires_at = int(time.time()) + int(ttl_seconds)
    signed = f"v2:{normalized}:{expires_at}"
    signature = hmac.new(secret.encode("utf-8"), signed.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{signed}:{signature}"


def _legacy_signed_learner_token(learner_id: str, secret: str) -> str:
    normalized = normalize_learner_id(learner_id)
    signature = hmac.new(secret.encode("utf-8"), normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"v1:{normalized}:{signature}"


def _legacy_tokens_allowed() -> bool:
    return os.environ.get("AI_LANGUAGE_PARTNER_ALLOW_LEGACY_TOKENS", "").strip().lower() in {"1", "true", "yes"}


def _verify_signed_learner_token(
    token: Optional[str],
    secret: Optional[str],
    allow_legacy: bool = False,
    now_seconds: Optional[int] = None,
) -> Optional[str]:
    if not token or not secret:
        return None
    parts = token.split(":")
    if len(parts) not in {3, 4}:
        return None
    if parts[0] == "v2" and len(parts) == 4:
        _, learner_id, expires_at_raw, signature = parts
        try:
            expires_at = int(expires_at_raw)
        except ValueError:
            return None
        if (now_seconds if now_seconds is not None else int(time.time())) > expires_at:
            return None
        normalized = normalize_learner_id(learner_id)
        expected_signed = f"v2:{normalized}:{expires_at}"
        expected = hmac.new(secret.encode("utf-8"), expected_signed.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        return normalized
    if parts[0] == "v1" and len(parts) == 3 and allow_legacy:
        _, learner_id, signature = parts
        normalized = normalize_learner_id(learner_id)
        expected = _legacy_signed_learner_token(normalized, secret).rsplit(":", 1)[1]
        if not hmac.compare_digest(signature, expected):
            return None
        return normalized
    return None


def _admin_key_valid(provided: Optional[str]) -> bool:
    configured = os.environ.get("AI_LANGUAGE_PARTNER_ADMIN_KEY")
    if configured:
        return hmac.compare_digest(provided or "", configured)
    if _auth_mode() == "dev":
        return hmac.compare_digest(provided or "", "local-dev-admin")
    return False


class CreateConversationRequest(BaseModel):
    personaId: str
    practiceRoomId: str
    mode: Literal["practice", "free_chat", "shadowing", "roleplay"] = "practice"


class CreateTurnRequest(BaseModel):
    inputType: Literal["text", "audio", "mock_audio"] = Field(default="text")
    text: Optional[str] = None
    audioBase64: Optional[str] = None
    requestTts: bool = True


class TtsRequest(BaseModel):
    text: str
    personaId: str
    language: Literal["ja", "ko", "en"] = "ja"
    speed: Optional[float] = 0.92
    emotion: Optional[str] = "gentle"


class SttRequest(BaseModel):
    audioBase64: Optional[str] = None
    language: Literal["ja", "ko", "en"] = "ja"
    mockText: Optional[str] = None
    hintLineIds: list[str] = Field(default_factory=list)


class DialogueMatchRequest(BaseModel):
    personaId: str
    packVersion: str = "v1"
    utterance: str
    candidateLineIds: list[str] = Field(default_factory=list)
    globalIntents: bool = True


class DialogueUnmatchedRequest(BaseModel):
    personaId: str
    nodeId: str
    utterance: str
    sttConfidence: Optional[float] = None
    packVersion: str = "v1"


class ReviewCardRequest(BaseModel):
    id: Optional[str] = None
    front: str
    back: str
    example: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    dueAt: Optional[str] = None


class AnalyticsEvent(BaseModel):
    eventName: str
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ProfileRequest(BaseModel):
    nativeLanguage: Optional[str] = None
    targetLanguage: Optional[str] = None
    level: Optional[str] = None
    jlptLevel: Optional[str] = None
    goals: Optional[list[str]] = None
    weakTags: Optional[list[str]] = None
    preferredPersonaId: Optional[str] = None


class ReviewGradeRequest(BaseModel):
    quality: int = Field(ge=0, le=5)


class PronunciationScoreRequest(BaseModel):
    expectedText: str
    actualText: str
    audioBase64: Optional[str] = None
    language: Literal["ja", "ko", "en"] = "ja"


class AnkiConnectExportRequest(BaseModel):
    deckName: str = "AI Language Partner"
    modelName: str = "Basic"
    apply: bool = False
    ankiConnectUrl: str = Field(default="http://127.0.0.1:8765", max_length=128)


class AuthRegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)
    learnerId: Optional[str] = None
    deviceLabel: Optional[str] = None
    deviceId: Optional[str] = None


class AuthLoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=256)
    deviceLabel: Optional[str] = None
    deviceId: Optional[str] = None


class AuthOidcRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    idToken: str = Field(min_length=10)
    nonce: Optional[str] = None
    learnerId: Optional[str] = None
    deviceLabel: Optional[str] = None
    deviceId: Optional[str] = None


class AuthOAuthPkceStartRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    redirectUri: str = Field(min_length=8, max_length=512)
    codeChallenge: str = Field(min_length=43, max_length=128)
    codeChallengeMethod: Literal["S256"] = "S256"
    scope: Optional[str] = Field(default=None, max_length=256)
    nonce: Optional[str] = Field(default=None, max_length=160)
    learnerId: Optional[str] = None
    deviceLabel: Optional[str] = None


class AuthOAuthPkceCallbackRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    state: str = Field(min_length=16, max_length=256)
    code: str = Field(min_length=10, max_length=4096)
    codeVerifier: str = Field(min_length=43, max_length=128)
    redirectUri: str = Field(min_length=8, max_length=512)
    learnerId: Optional[str] = None
    deviceLabel: Optional[str] = None
    deviceId: Optional[str] = None


class AuthSsoConnectionRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    organizationName: str = Field(min_length=1, max_length=160)
    domains: list[str] = Field(default_factory=list)
    redirectUris: list[str] = Field(default_factory=list)
    requiredEmailDomain: Optional[str] = Field(default=None, max_length=160)
    status: Literal["enabled", "disabled"] = "enabled"


class AuthSsoDiscoveryRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class AuthSsoPkceStartRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    redirectUri: str = Field(min_length=8, max_length=512)
    codeChallenge: str = Field(min_length=43, max_length=128)
    codeChallengeMethod: Literal["S256"] = "S256"
    scope: Optional[str] = Field(default=None, max_length=256)
    nonce: Optional[str] = Field(default=None, max_length=160)
    learnerId: Optional[str] = None
    deviceLabel: Optional[str] = None


class AuthSsoPkceCallbackRequest(BaseModel):
    connectionId: str = Field(min_length=1, max_length=80)
    state: str = Field(min_length=16, max_length=256)
    code: str = Field(min_length=10, max_length=4096)
    codeVerifier: str = Field(min_length=43, max_length=128)
    redirectUri: str = Field(min_length=8, max_length=512)
    learnerId: Optional[str] = None
    deviceLabel: Optional[str] = None
    deviceId: Optional[str] = None


class AuthRefreshRequest(BaseModel):
    refreshToken: str
    deviceLabel: Optional[str] = None
    deviceId: Optional[str] = None


class AuthChangePasswordRequest(BaseModel):
    currentPassword: str = Field(min_length=1, max_length=256)
    newPassword: str = Field(min_length=8, max_length=256)
    deviceLabel: Optional[str] = None
    deviceId: Optional[str] = None


class AuthDeleteAccountRequest(BaseModel):
    password: Optional[str] = Field(default=None, min_length=1, max_length=256)
    confirmation: Optional[str] = None


class AuthTrustDeviceRequest(BaseModel):
    confirmation: Literal["trust-this-device"]
    deviceLabel: Optional[str] = Field(default=None, max_length=120)
    platform: Optional[str] = Field(default=None, max_length=80)
    attestationProvider: Optional[str] = Field(default=None, max_length=80)
    attestationSubject: Optional[str] = Field(default=None, max_length=2048)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class AuthDeviceAttestationChallengeRequest(BaseModel):
    attestationProvider: Optional[str] = Field(default="signed_challenge", max_length=80)
    attestationSubject: Optional[str] = Field(default=None, max_length=2048)


class ContentBundleRequest(BaseModel):
    courses: list[Dict[str, Any]] = Field(default_factory=list)
    practiceRooms: list[Dict[str, Any]] = Field(default_factory=list)


class ContentImportRequest(ContentBundleRequest):
    dryRun: bool = True
    replaceExisting: bool = True


class ContentReviewRequest(BaseModel):
    note: Optional[str] = None


class ContentBranchRequest(BaseModel):
    label: Optional[str] = None
    branchName: Optional[str] = None
    assignee: Optional[str] = None
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    dueAt: Optional[str] = None
    note: Optional[str] = None


class ContentAssignmentRequest(BaseModel):
    assignee: str
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    dueAt: Optional[str] = None
    note: Optional[str] = None
    status: Literal["todo", "in_progress", "blocked", "done"] = "todo"


class ContentAssignmentStatusRequest(BaseModel):
    status: Literal["todo", "in_progress", "blocked", "done"]
    note: Optional[str] = None


class ContentReleaseRequest(BaseModel):
    versionId: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=160)
    releaseStrategy: Literal["immediate", "scheduled", "canary"] = "immediate"
    rolloutPercent: int = Field(default=100, ge=1, le=100)
    catalogScope: Literal["incremental", "full_catalog"] = "incremental"
    scheduledAt: Optional[str] = None
    guardrails: Dict[str, Any] = Field(default_factory=dict)
    note: Optional[str] = Field(default=None, max_length=1000)


class ContentReleaseApplyRequest(BaseModel):
    confirmation: Literal["apply-content-release"]
    force: bool = False
    note: Optional[str] = Field(default=None, max_length=1000)


class ContentReleaseRunDueRequest(BaseModel):
    confirmation: Literal["run-due-content-releases"]
    limit: int = Field(default=50, ge=1, le=200)


class ContentReleaseRollbackRequest(BaseModel):
    confirmation: Literal["rollback-content-release"]
    note: Optional[str] = Field(default=None, max_length=1000)


class ContentOperationJobRequest(BaseModel):
    jobType: Literal["validate_bundle", "import_bundle", "run_due_releases"]
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    payload: Dict[str, Any] = Field(default_factory=dict)


class ContentOperationJobRunNextRequest(BaseModel):
    confirmation: Literal["run-next-content-operation-job"]


class ContentOperationJobCancelRequest(BaseModel):
    confirmation: Literal["cancel-content-operation-job"]


class ContentSchedulerRunOnceRequest(BaseModel):
    confirmation: Literal["run-content-scheduler-once"]
    schedulerKey: str = Field(default="content_ops", min_length=1, max_length=80)
    leaseOwner: str = Field(default="local-scheduler", min_length=1, max_length=120)
    maxOperationJobs: int = Field(default=1, ge=0, le=20)
    releaseLimit: int = Field(default=50, ge=1, le=200)


class TranslationMemoryEntryRequest(BaseModel):
    sourceLanguage: str = "ko"
    targetLanguage: str = "ja"
    sourceText: str
    targetText: str
    tags: list[str] = Field(default_factory=list)
    sourceRef: Optional[str] = None
    quality: int = Field(default=100, ge=0, le=100)


class TranslationMemoryUpsertRequest(BaseModel):
    entries: list[TranslationMemoryEntryRequest] = Field(default_factory=list)


class TranslationMemorySuggestRequest(BaseModel):
    sourceText: str
    sourceLanguage: str = "ko"
    targetLanguage: str = "ja"
    limit: int = Field(default=5, ge=1, le=20)


class ContentBulkQaRequest(ContentBundleRequest):
    versionId: Optional[str] = None
    useCurrent: bool = True
    includeTranslationMemory: bool = True


class ExperimentVariantRequest(BaseModel):
    key: str
    label: Optional[str] = None
    weight: int = Field(default=1, ge=0, le=1000)
    payload: Dict[str, Any] = Field(default_factory=dict)


class ExperimentRequest(BaseModel):
    key: str
    name: str
    status: Literal["draft", "running", "paused", "archived"] = "draft"
    variants: list[ExperimentVariantRequest]
    allocation: Dict[str, Any] = Field(default_factory=dict)


class ExperimentStatusRequest(BaseModel):
    status: Literal["draft", "running", "paused", "archived"]


class ExperimentDecisionRequest(BaseModel):
    action: Literal["auto", "collect_more_data", "promote_variant", "pause", "archive", "no_winner"] = "auto"
    variantKey: Optional[str] = Field(default=None, max_length=80)
    minimumExposedLearners: int = Field(default=30, ge=1, le=100000)
    reason: Optional[str] = Field(default=None, max_length=1000)
    requireDecisionReady: bool = True
    requireStatisticalSignificance: bool = True


class ExperimentDecisionApplyRequest(BaseModel):
    confirmation: Literal["apply-experiment-decision"]
    note: Optional[str] = Field(default=None, max_length=1000)


class ExperimentEventRequest(BaseModel):
    eventName: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class XpAbuseFlagReviewRequest(BaseModel):
    status: Literal["open", "reviewing", "resolved", "dismissed"]
    note: Optional[str] = Field(default=None, max_length=1000)


class RewardShopItemUpdateRequest(BaseModel):
    priceCurrency: str = Field(default="gems", min_length=1, max_length=40)
    priceAmount: int = Field(default=0, ge=0, le=100000)
    available: bool = True
    dailyPurchaseLimit: Optional[int] = Field(default=None, ge=0, le=1000)
    inventoryLimit: Optional[int] = Field(default=None, ge=0, le=1000)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    sortOrder: int = Field(default=100, ge=0, le=100000)


class FriendInviteRequest(BaseModel):
    friendLearnerId: str = Field(min_length=1, max_length=80)
    message: Optional[str] = Field(default=None, max_length=240)


class SocialSettingsRequest(BaseModel):
    discoverable: bool = True
    allowFriendInvites: bool = True
    showWeeklyXp: bool = True


def dump_model(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _normalize_hint_line_ids(raw_values: list[Any]) -> list[str]:
    hints: list[str] = []
    for raw_value in raw_values:
        if not isinstance(raw_value, str):
            raise HTTPException(status_code=422, detail="hintLineIds values must be strings")
        raw_text = raw_value.strip()
        if not raw_text:
            continue
        values: list[str]
        if raw_text.startswith("["):
            try:
                parsed = json.loads(raw_text)
                if not isinstance(parsed, list):
                    values = [raw_text]
                elif not all(isinstance(value, str) for value in parsed):
                    raise HTTPException(status_code=422, detail="hintLineIds JSON array must contain only strings")
                else:
                    values = [value.strip() for value in parsed]
            except json.JSONDecodeError:
                raise HTTPException(status_code=422, detail="hintLineIds JSON array is malformed") from None
        elif "," in raw_text:
            values = [part.strip() for part in raw_text.split(",")]
        else:
            values = [raw_text]
        for value in values:
            if not value:
                continue
            if len(value) > MAX_STT_HINT_LINE_ID_LENGTH:
                raise HTTPException(status_code=422, detail="hintLineIds value is too long")
            hints.append(value)
    normalized = list(dict.fromkeys(hints))
    if len(normalized) > MAX_STT_HINT_LINE_IDS:
        raise HTTPException(status_code=422, detail="Too many hintLineIds")
    return normalized


async def _stt_payload_from_request(request: Request) -> Dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        audio_base64 = None
        if upload is not None and hasattr(upload, "read"):
            audio_bytes = await upload.read()
            media_type = getattr(upload, "content_type", None) or "audio/wav"
            audio_base64 = f"data:{media_type};base64," + base64.b64encode(audio_bytes).decode("ascii")
        raw_hint_values: list[Any] = []
        if hasattr(form, "getlist"):
            raw_hint_values = list(form.getlist("hintLineIds"))
        elif form.get("hintLineIds") is not None:
            raw_hint_values = [form.get("hintLineIds")]
        return {
            "audioBase64": audio_base64,
            "language": str(form.get("language") or "ja"),
            "mockText": str(form.get("mockText")) if form.get("mockText") is not None else None,
            "hintLineIds": _normalize_hint_line_ids(raw_hint_values),
        }
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    raw_json_hint_values = payload.get("hintLineIds")
    if raw_json_hint_values is not None:
        if not isinstance(raw_json_hint_values, list):
            raise HTTPException(status_code=422, detail="hintLineIds must be a list")
        if not all(isinstance(value, str) for value in raw_json_hint_values):
            raise HTTPException(status_code=422, detail="hintLineIds values must be strings")
    try:
        req = SttRequest(**payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc
    req_payload = dump_model(req)
    req_payload["hintLineIds"] = _normalize_hint_line_ids(req_payload.get("hintLineIds") or [])
    return req_payload


def _experiment_decision_plan(payload: Dict[str, Any], analytics: Dict[str, Any]) -> Dict[str, Any]:
    requested_action = payload.get("action") or "auto"
    winner = analytics.get("winnerVariantKey")
    variant_key = normalize_experiment_key(payload.get("variantKey")) if payload.get("variantKey") else None
    if requested_action == "auto":
        recommendation = analytics.get("decisionRecommendation")
        if recommendation == "promote_winner" and winner:
            action = "promote_variant"
            variant_key = winner
        elif recommendation == "no_statistically_significant_winner":
            action = "no_winner"
        else:
            action = "collect_more_data"
    else:
        action = requested_action
    if action == "promote_variant":
        variant_key = variant_key or winner
    return {"action": action, "variantKey": variant_key}


def _experiment_decision_guardrail(payload: Dict[str, Any], analytics: Dict[str, Any], action: str, variant_key: Optional[str]) -> Dict[str, Any]:
    variants = {variant["variantKey"]: variant for variant in analytics.get("variants") or []}
    selected = variants.get(variant_key or "") if variant_key else None
    decision_ready = bool(analytics.get("decisionReady"))
    winner = analytics.get("winnerVariantKey")
    require_ready = bool(payload.get("requireDecisionReady", True))
    require_significance = bool(payload.get("requireStatisticalSignificance", True))
    violations: list[str] = []
    if action == "promote_variant" and not variant_key:
        violations.append("promote_variant_requires_variant")
    if action == "promote_variant" and variant_key not in variants:
        violations.append("variant_not_found")
    if action in {"promote_variant", "no_winner"} and require_ready and not decision_ready:
        violations.append("decision_not_ready")
    if action == "promote_variant" and require_significance and winner != variant_key:
        violations.append("variant_is_not_statistically_significant_winner")
    if action == "promote_variant" and selected and (selected.get("absoluteLiftFromBaseline") or 0) <= 0:
        violations.append("variant_lift_not_positive")
    return {
        "ok": not violations,
        "violations": violations,
        "action": action,
        "variantKey": variant_key,
        "decisionReady": decision_ready,
        "winnerVariantKey": winner,
        "bestObservedVariantKey": analytics.get("bestObservedVariantKey"),
        "decisionRecommendation": analytics.get("decisionRecommendation"),
        "minimumExposedLearners": analytics.get("minimumExposedLearners"),
        "requireDecisionReady": require_ready,
        "requireStatisticalSignificance": require_significance,
        "selectedVariant": {
            "variantKey": selected.get("variantKey"),
            "exposedLearnerCount": selected.get("exposedLearnerCount"),
            "convertedLearnerCount": selected.get("convertedLearnerCount"),
            "exposedConversionRate": selected.get("exposedConversionRate"),
            "absoluteLiftFromBaseline": selected.get("absoluteLiftFromBaseline"),
            "pValue": selected.get("pValue"),
            "statisticallySignificant": selected.get("statisticallySignificant"),
        }
        if selected
        else None,
    }


REQUIRED_COURSE_FIELDS = {"id", "title", "targetLanguage", "nativeLanguage", "level", "units"}
REQUIRED_UNIT_FIELDS = {"id", "title", "order", "lessons"}
REQUIRED_LESSON_FIELDS = {"id", "title", "order", "practiceRoomIds"}
REQUIRED_ROOM_FIELDS = {
    "id",
    "title",
    "primaryPhraseKo",
    "primaryPhraseJa",
    "personaId",
    "scenario",
    "openingMessage",
    "tags",
}


def _content_issue(code: str, message: str, pointer: str, **extra: Any) -> Dict[str, Any]:
    issue = {"code": code, "message": message, "pointer": pointer}
    issue.update(extra)
    return issue


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _add_missing_field_errors(item: Dict[str, Any], required: set[str], pointer: str, errors: list[Dict[str, Any]]) -> None:
    for field_name in sorted(required):
        if not _has_value(item.get(field_name)):
            errors.append(
                _content_issue(
                    "missing_required_field",
                    f"Missing required field: {field_name}",
                    f"{pointer}/{field_name}",
                )
            )


def _duplicate_id_errors(items: list[Dict[str, Any]], pointer: str, kind: str, errors: list[Dict[str, Any]]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for index, item in enumerate(items):
        item_id = item.get("id") if isinstance(item, dict) else None
        if not item_id:
            continue
        if item_id in seen:
            duplicates.add(str(item_id))
            errors.append(
                _content_issue(
                    f"duplicate_{kind}_id",
                    f"Duplicate {kind} id: {item_id}",
                    f"{pointer}/{index}/id",
                    id=item_id,
                )
            )
        seen.add(str(item_id))
    return duplicates


def _content_quality_report(
    courses: list[Dict[str, Any]],
    practice_rooms: list[Dict[str, Any]],
    personas: list[Dict[str, Any]],
) -> Dict[str, Any]:
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    persona_ids = {persona.get("id") for persona in personas if persona.get("id")}
    if not courses:
        errors.append(_content_issue("empty_course_catalog", "At least one course is required", "/courses"))
    if not practice_rooms:
        errors.append(_content_issue("empty_practice_room_catalog", "At least one practice room is required", "/practiceRooms"))
    _duplicate_id_errors(courses, "/courses", "course", errors)
    _duplicate_id_errors(practice_rooms, "/practiceRooms", "practice_room", errors)

    rooms_by_id: Dict[str, Dict[str, Any]] = {}
    for index, room in enumerate(practice_rooms):
        pointer = f"/practiceRooms/{index}"
        if not isinstance(room, dict):
            errors.append(_content_issue("invalid_practice_room", "Practice room must be an object", pointer))
            continue
        _add_missing_field_errors(room, REQUIRED_ROOM_FIELDS, pointer, errors)
        room_id = room.get("id")
        if room_id and room_id not in rooms_by_id:
            rooms_by_id[str(room_id)] = room
        if room.get("personaId") and room.get("personaId") not in persona_ids:
            errors.append(
                _content_issue(
                    "unknown_persona",
                    f"Unknown personaId: {room.get('personaId')}",
                    f"{pointer}/personaId",
                    personaId=room.get("personaId"),
                )
            )
        if "tags" in room and (not isinstance(room.get("tags"), list) or not all(isinstance(tag, str) and tag.strip() for tag in room.get("tags", []))):
            errors.append(_content_issue("invalid_tags", "tags must be a non-empty string array", f"{pointer}/tags"))
        if "alternativePhrasesJa" in room and not isinstance(room.get("alternativePhrasesJa"), list):
            warnings.append(
                _content_issue(
                    "invalid_alternative_phrases_shape",
                    "alternativePhrasesJa should be an array when present",
                    f"{pointer}/alternativePhrasesJa",
                )
            )

    course_ids: set[str] = set()
    unit_ids: set[str] = set()
    lesson_ids: set[str] = set()
    referenced_room_ids: list[str] = []
    missing_room_refs: set[str] = set()
    room_assignments: Dict[str, str] = {}
    duplicate_room_refs: set[str] = set()

    for course_index, course in enumerate(courses):
        course_pointer = f"/courses/{course_index}"
        if not isinstance(course, dict):
            errors.append(_content_issue("invalid_course", "Course must be an object", course_pointer))
            continue
        _add_missing_field_errors(course, REQUIRED_COURSE_FIELDS, course_pointer, errors)
        course_id = str(course.get("id") or "")
        if course_id:
            course_ids.add(course_id)
        units = course.get("units") or []
        if not isinstance(units, list) or not units:
            errors.append(_content_issue("invalid_units", "Course units must be a non-empty array", f"{course_pointer}/units"))
            continue
        for unit_index, unit in enumerate(units):
            unit_pointer = f"{course_pointer}/units/{unit_index}"
            if not isinstance(unit, dict):
                errors.append(_content_issue("invalid_unit", "Course unit must be an object", unit_pointer))
                continue
            _add_missing_field_errors(unit, REQUIRED_UNIT_FIELDS, unit_pointer, errors)
            unit_id = unit.get("id")
            if unit_id:
                if str(unit_id) in unit_ids:
                    errors.append(
                        _content_issue("duplicate_unit_id", f"Duplicate unit id: {unit_id}", f"{unit_pointer}/id", id=unit_id)
                    )
                unit_ids.add(str(unit_id))
            lessons = unit.get("lessons") or []
            if not isinstance(lessons, list) or not lessons:
                errors.append(_content_issue("invalid_lessons", "Unit lessons must be a non-empty array", f"{unit_pointer}/lessons"))
                continue
            for lesson_index, lesson in enumerate(lessons):
                lesson_pointer = f"{unit_pointer}/lessons/{lesson_index}"
                if not isinstance(lesson, dict):
                    errors.append(_content_issue("invalid_lesson", "Course lesson must be an object", lesson_pointer))
                    continue
                _add_missing_field_errors(lesson, REQUIRED_LESSON_FIELDS, lesson_pointer, errors)
                lesson_id = lesson.get("id")
                if lesson_id:
                    if str(lesson_id) in lesson_ids:
                        errors.append(
                            _content_issue("duplicate_lesson_id", f"Duplicate lesson id: {lesson_id}", f"{lesson_pointer}/id", id=lesson_id)
                        )
                    lesson_ids.add(str(lesson_id))
                room_refs = lesson.get("practiceRoomIds") or []
                if not isinstance(room_refs, list) or not room_refs:
                    errors.append(
                        _content_issue(
                            "invalid_practice_room_refs",
                            "practiceRoomIds must be a non-empty string array",
                            f"{lesson_pointer}/practiceRoomIds",
                        )
                    )
                    continue
                for room_index, room_id in enumerate(room_refs):
                    ref_pointer = f"{lesson_pointer}/practiceRoomIds/{room_index}"
                    if not isinstance(room_id, str) or not room_id.strip():
                        errors.append(_content_issue("invalid_practice_room_ref", "Practice room ref must be a string", ref_pointer))
                        continue
                    referenced_room_ids.append(room_id)
                    if room_id not in rooms_by_id:
                        missing_room_refs.add(room_id)
                        errors.append(
                            _content_issue(
                                "missing_practice_room_ref",
                                f"Course references missing practice room: {room_id}",
                                ref_pointer,
                                practiceRoomId=room_id,
                            )
                        )
                    assignment = f"{course_id}/{unit.get('id')}/{lesson_id}"
                    if room_id in room_assignments:
                        duplicate_room_refs.add(room_id)
                        errors.append(
                            _content_issue(
                                "practice_room_referenced_multiple_times",
                                f"Practice room has multiple course placements: {room_id}",
                                ref_pointer,
                                practiceRoomId=room_id,
                            )
                        )
                    room_assignments[room_id] = assignment

    orphan_room_ids = sorted(set(rooms_by_id) - set(referenced_room_ids))
    for room_id in orphan_room_ids:
        errors.append(
            _content_issue(
                "orphan_practice_room",
                f"Practice room is not placed in any course lesson: {room_id}",
                f"/practiceRooms/{list(rooms_by_id).index(room_id)}/id",
                practiceRoomId=room_id,
            )
        )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "personas": len(persona_ids),
            "courses": len(courses),
            "units": len(unit_ids),
            "lessons": len(lesson_ids),
            "practiceRooms": len(rooms_by_id),
            "practiceRoomRefs": len(referenced_room_ids),
            "roomsWithCoursePlacement": len(set(referenced_room_ids) & set(rooms_by_id)),
        },
        "courseIds": sorted(course_ids),
        "missingPersonaIds": sorted(
            {str(room.get("personaId")) for room in practice_rooms if isinstance(room, dict) and room.get("personaId") and room.get("personaId") not in persona_ids}
        ),
        "missingPracticeRoomRefs": sorted(missing_room_refs),
        "duplicatePracticeRoomRefs": sorted(duplicate_room_refs),
        "orphanPracticeRoomIds": orphan_room_ids,
        "referencedPracticeRoomIds": sorted(set(referenced_room_ids)),
    }


def _annotate_practice_rooms_with_course_metadata(
    courses: list[Dict[str, Any]],
    practice_rooms: list[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    metadata_by_room_id: Dict[str, Dict[str, Any]] = {}
    for course in courses:
        for unit in course.get("units") or []:
            for lesson in unit.get("lessons") or []:
                for room_order, room_id in enumerate(lesson.get("practiceRoomIds") or [], start=1):
                    metadata_by_room_id[room_id] = {
                        "courseId": course.get("id"),
                        "courseTitle": course.get("title"),
                        "unitId": unit.get("id"),
                        "unitTitle": unit.get("title"),
                        "unitOrder": unit.get("order"),
                        "lessonId": lesson.get("id"),
                        "lessonTitle": lesson.get("title"),
                        "lessonOrder": lesson.get("order"),
                        "roomOrder": room_order,
                    }
    annotated = []
    for room in practice_rooms:
        updated = dict(room)
        updated.update(metadata_by_room_id.get(room.get("id"), {}))
        annotated.append(updated)
    return annotated


def _content_version_summary(version: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in version.items()
        if key not in {"courses", "practiceRooms"}
    }


def _resolve_content_qa_bundle(payload: Dict[str, Any], store: ApiStore) -> tuple[str, list[Dict[str, Any]], list[Dict[str, Any]]]:
    version_id = (payload.get("versionId") or "").strip()
    if version_id:
        version = store.get_content_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Content version not found")
        return f"version:{version_id}", version["courses"], version["practiceRooms"]
    if payload.get("courses") or payload.get("practiceRooms"):
        return "request", payload["courses"], _annotate_practice_rooms_with_course_metadata(payload["courses"], payload["practiceRooms"])
    if payload.get("useCurrent", True):
        return "current", store.list_courses(), store.list_practice_rooms()
    return "request", payload["courses"], payload["practiceRooms"]


def _content_bulk_qa_report(
    courses: list[Dict[str, Any]],
    practice_rooms: list[Dict[str, Any]],
    store: ApiStore,
    include_translation_memory: bool = True,
) -> Dict[str, Any]:
    quality_report = _content_quality_report(courses, practice_rooms, store.list_personas())
    issues: list[Dict[str, Any]] = []
    suggestions_by_room: list[Dict[str, Any]] = []
    counts = {
        "roomsChecked": 0,
        "translationMemoryExactMatches": 0,
        "translationMemoryFuzzyMatches": 0,
        "translationMemoryMissing": 0,
        "translationMemoryConflicts": 0,
    }
    if include_translation_memory:
        for index, room in enumerate(practice_rooms):
            if not isinstance(room, dict):
                continue
            source_text = str(room.get("primaryPhraseKo") or "").strip()
            target_text = str(room.get("primaryPhraseJa") or "").strip()
            if not source_text or not target_text:
                continue
            counts["roomsChecked"] += 1
            suggestions = store.suggest_translation_memory(source_text, source_language="ko", target_language="ja", limit=5)
            exact_source_matches = [item for item in suggestions if item.get("matchType") == "exact"]
            exact_target_matches = [item for item in exact_source_matches if item.get("targetText") == target_text]
            if exact_target_matches:
                counts["translationMemoryExactMatches"] += 1
            elif exact_source_matches:
                counts["translationMemoryConflicts"] += 1
                issues.append(
                    _content_issue(
                        "translation_memory_target_conflict",
                        "Same Korean source has a different Japanese target in translation memory",
                        f"/practiceRooms/{index}/primaryPhraseJa",
                        severity="warning",
                        practiceRoomId=room.get("id"),
                        sourceText=source_text,
                        targetText=target_text,
                        memoryTargets=[item["targetText"] for item in exact_source_matches[:3]],
                    )
                )
            elif suggestions:
                counts["translationMemoryFuzzyMatches"] += 1
            else:
                counts["translationMemoryMissing"] += 1
                issues.append(
                    _content_issue(
                        "translation_memory_missing",
                        "No translation memory suggestion exists for this Korean source",
                        f"/practiceRooms/{index}/primaryPhraseKo",
                        severity="info",
                        practiceRoomId=room.get("id"),
                        sourceText=source_text,
                    )
                )
            suggestions_by_room.append(
                {
                    "practiceRoomId": room.get("id"),
                    "sourceText": source_text,
                    "targetText": target_text,
                    "suggestions": suggestions[:3],
                }
            )
    critical_issue_count = sum(1 for issue in issues if issue.get("severity") == "error")
    return {
        "valid": quality_report["valid"] and critical_issue_count == 0,
        "qualityReport": quality_report,
        "issues": issues,
        "counts": counts,
        "translationMemorySuggestions": suggestions_by_room,
    }


def create_app(db_path: Optional[Union[str, Path]] = None) -> FastAPI:
    api = FastAPI(title="AI Language Partner Mobile API", version="0.1.0")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins_from_env(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.state.store = ApiStore(db_path or default_db_path())
    providers = build_provider_stack()
    api.state.tts = providers["tts"]
    api.state.stt = providers["stt"]
    api.state.llm = providers["llm"]
    api.state.pronunciation = providers["pronunciation"]
    api.state.dialogue_matcher = DialogueMatcher()
    api.state.rate_limiter = build_rate_limiter()

    @api.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        limiter = api.state.rate_limiter
        limit = int(getattr(limiter, "limit_per_minute", 0) or 0)
        if limit > 0:
            client_host = request.client.host if request.client else "unknown"
            learner_hint = _rate_limit_learner_hint(request)
            decision = limiter.check(f"{client_host}:{learner_hint}", request.url.path)
            if not decision.allowed:
                api.state.store.audit_log(
                    "rate_limit_exceeded",
                    actor=client_host,
                    target_type="path",
                    target_id=request.url.path,
                    payload={
                        "limitPerMinute": decision.limit_per_minute,
                        "retryAfterSeconds": decision.retry_after_seconds,
                        "backend": decision.backend,
                    },
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded", "retryAfterSeconds": decision.retry_after_seconds},
                    headers={
                        "Retry-After": str(decision.retry_after_seconds),
                        "X-RateLimit-Limit": str(decision.limit_per_minute),
                        "X-RateLimit-Backend": decision.backend,
                    },
                )
        response = await call_next(request)
        if limit > 0:
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Backend"] = limiter.describe()["backend"]
        return response

    def get_store() -> ApiStore:
        return api.state.store

    def admin_context(request: Request, allowed_roles: Optional[set[str]] = None) -> Dict[str, str]:
        if not _admin_key_valid(request.headers.get("X-Admin-Key")):
            raise HTTPException(status_code=403, detail="Admin access required")
        role = (request.headers.get("X-Admin-Role") or "owner").strip().lower()
        if role not in {"viewer", "editor", "reviewer", "publisher", "owner"}:
            raise HTTPException(status_code=403, detail="Invalid admin role")
        if allowed_roles is not None and role != "owner" and role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin role is not allowed for this operation")
        actor = (request.headers.get("X-Admin-User") or f"content_admin:{role}").strip()
        if not actor:
            actor = f"content_admin:{role}"
        return {"role": role, "actor": actor[:120]}

    def require_admin_key(request: Request) -> None:
        admin_context(request)

    def require_admin_role(request: Request, allowed_roles: set[str]) -> Dict[str, str]:
        return admin_context(request, allowed_roles=allowed_roles)

    def get_account_session(request: Request) -> Dict[str, Any]:
        session = _session_from_authorization(request, get_store(), raise_on_invalid=True)
        if not session:
            raise HTTPException(status_code=401, detail="Account bearer token required")
        return session

    def get_learner_id(request: Request) -> str:
        account_session = _session_from_authorization(request, api.state.store, raise_on_invalid=True)
        if account_session:
            return account_session["learnerId"]
        auth_secret = os.environ.get("AI_LANGUAGE_PARTNER_AUTH_SECRET")
        token = request.headers.get("X-Learner-Token")
        if token:
            learner_from_token = _verify_signed_learner_token(token, auth_secret, allow_legacy=_legacy_tokens_allowed())
            if not learner_from_token:
                raise HTTPException(status_code=401, detail="Invalid learner token")
            return learner_from_token
        if _auth_mode() in {"token", "hosted", "production"}:
            raise HTTPException(status_code=401, detail="Signed learner token required")
        return normalize_learner_id(
            request.headers.get("X-Learner-Id")
            or request.headers.get("X-Anonymous-Id")
            or request.headers.get("X-User-Id")
        )

    def get_tts() -> MockTTSProvider:
        return api.state.tts

    def get_stt() -> MockSTTProvider:
        return api.state.stt

    def get_llm() -> MockLLMProvider:
        return api.state.llm

    def get_pronunciation() -> MockPronunciationScorer:
        return api.state.pronunciation

    @api.get("/health")
    def health() -> Dict[str, Any]:
        return {"ok": True, "projectId": PROJECT_ID}

    @api.get("/v1/personas")
    def list_personas(store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        return {"personas": store.list_personas()}

    @api.get("/v1/practice-rooms")
    def list_practice_rooms(store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        return {"practiceRooms": store.list_practice_rooms()}

    @api.get("/v1/practice-rooms/{practiceRoomId}")
    def get_practice_room(practiceRoomId: str, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        room = store.get_practice_room(practiceRoomId)
        if not room:
            raise HTTPException(status_code=404, detail="Practice room not found")
        return {"practiceRoom": room}

    @api.get("/v1/courses")
    def list_courses(store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        return {"courses": store.list_courses()}

    @api.get("/v1/courses/{courseId}")
    def get_course(courseId: str, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        course = store.get_course(courseId)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"course": course}

    @api.post("/v1/content/validate")
    def validate_content_bundle(
        request: Request,
        req: ContentBundleRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor", "reviewer", "publisher"})
        payload = dump_model(req)
        report = _content_quality_report(payload["courses"], payload["practiceRooms"], store.list_personas())
        store.audit_log(
            "content_validation_completed",
            actor=context["actor"],
            target_type="content_bundle",
            payload={"valid": report["valid"], "counts": report["counts"], "errorCount": len(report["errors"])},
        )
        return {"ok": report["valid"], "report": report}

    @api.post("/v1/content/import")
    def import_content_bundle(
        request: Request,
        req: ContentImportRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        payload = dump_model(req)
        report = _content_quality_report(payload["courses"], payload["practiceRooms"], store.list_personas())
        if not report["valid"]:
            store.audit_log(
                "content_import_rejected",
                actor=context["actor"],
                target_type="content_bundle",
                payload={"counts": report["counts"], "errorCount": len(report["errors"])},
            )
            raise HTTPException(status_code=400, detail={"message": "Content validation failed", "report": report})
        if not payload["replaceExisting"]:
            existing_course_ids = {course["id"] for course in store.list_courses()}
            existing_room_ids = {room["id"] for room in store.list_practice_rooms()}
            conflicting_course_ids = sorted({course["id"] for course in payload["courses"]} & existing_course_ids)
            conflicting_room_ids = sorted({room["id"] for room in payload["practiceRooms"]} & existing_room_ids)
            if conflicting_course_ids or conflicting_room_ids:
                for course_id in conflicting_course_ids:
                    report["errors"].append(
                        _content_issue(
                            "course_id_already_exists",
                            f"Course already exists and replaceExisting is false: {course_id}",
                            "/courses",
                            courseId=course_id,
                        )
                    )
                for room_id in conflicting_room_ids:
                    report["errors"].append(
                        _content_issue(
                            "practice_room_id_already_exists",
                            f"Practice room already exists and replaceExisting is false: {room_id}",
                            "/practiceRooms",
                            practiceRoomId=room_id,
                        )
                    )
                report["valid"] = False
                store.audit_log(
                    "content_import_rejected",
                    actor=context["actor"],
                    target_type="content_bundle",
                    payload={
                        "counts": report["counts"],
                        "errorCount": len(report["errors"]),
                        "replaceExisting": payload["replaceExisting"],
                    },
                )
                raise HTTPException(status_code=409, detail={"message": "Content conflicts with existing records", "report": report})
        annotated_rooms = _annotate_practice_rooms_with_course_metadata(payload["courses"], payload["practiceRooms"])
        imported_counts = {"courses": 0, "practiceRooms": 0}
        if not payload["dryRun"]:
            imported_counts = store.upsert_content_bundle(payload["courses"], annotated_rooms)
        version = store.create_content_version(
            payload["courses"],
            annotated_rooms,
            report,
            imported_counts,
            source="content_import_dry_run" if payload["dryRun"] else "content_import_apply",
            label="Content import dry-run" if payload["dryRun"] else "Applied content import",
            status="draft" if payload["dryRun"] else "published",
            created_by=context["actor"],
        )
        store.audit_log(
            "content_version_created",
            actor=context["actor"],
            target_type="content_version",
            target_id=version["id"],
            payload={
                "status": version["status"],
                "source": version["source"],
                "snapshotCounts": version["snapshotCounts"],
                "importedCounts": imported_counts,
            },
        )
        action = "content_import_dry_run_completed" if payload["dryRun"] else "content_import_applied"
        store.audit_log(
            action,
            actor=context["actor"],
            target_type="content_bundle",
            payload={"counts": report["counts"], "importedCounts": imported_counts, "replaceExisting": payload["replaceExisting"]},
        )
        return {
            "ok": True,
            "dryRun": payload["dryRun"],
            "applied": not payload["dryRun"],
            "importedCounts": imported_counts,
            "version": _content_version_summary(version),
            "report": report,
        }

    @api.get("/v1/content/quality-report")
    def current_content_quality_report(request: Request, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        report = _content_quality_report(store.list_courses(), store.list_practice_rooms(), store.list_personas())
        return {"ok": report["valid"], "report": report}

    @api.get("/v1/content/translation-memory")
    def list_translation_memory(
        request: Request,
        query: Optional[str] = None,
        sourceLanguage: str = "ko",
        targetLanguage: str = "ja",
        limit: int = 50,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        entries = store.list_translation_memory(
            query=query,
            source_language=sourceLanguage,
            target_language=targetLanguage,
            limit=limit,
        )
        return {"entries": entries}

    @api.post("/v1/content/translation-memory")
    def upsert_translation_memory(
        request: Request,
        req: TranslationMemoryUpsertRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        payload = dump_model(req)
        result = store.upsert_translation_memory_entries(payload["entries"], created_by=context["actor"])
        store.audit_log(
            "content_translation_memory_upserted",
            actor=context["actor"],
            target_type="translation_memory",
            payload={"entryCount": result["entries"]},
        )
        return {"ok": True, "upsertedCounts": result}

    @api.post("/v1/content/translation-memory/suggest")
    def suggest_translation_memory(
        request: Request,
        req: TranslationMemorySuggestRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        payload = dump_model(req)
        suggestions = store.suggest_translation_memory(
            payload["sourceText"],
            source_language=payload["sourceLanguage"],
            target_language=payload["targetLanguage"],
            limit=payload["limit"],
        )
        return {"suggestions": suggestions}

    @api.post("/v1/content/bulk-qa")
    def bulk_qa_content(
        request: Request,
        req: ContentBulkQaRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        payload = dump_model(req)
        source, courses, practice_rooms = _resolve_content_qa_bundle(payload, store)
        report = _content_bulk_qa_report(
            courses,
            practice_rooms,
            store,
            include_translation_memory=payload["includeTranslationMemory"],
        )
        store.audit_log(
            "content_bulk_qa_completed",
            actor=context["actor"],
            target_type="content_bundle",
            target_id=source,
            payload={
                "valid": report["valid"],
                "source": source,
                "counts": report["counts"],
                "issueCount": len(report["issues"]),
            },
        )
        return {"ok": report["valid"], "source": source, "report": report}

    @api.get("/v1/content/assignments")
    def list_content_assignments(
        request: Request,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        limit: int = 50,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        if status and status not in {"todo", "in_progress", "blocked", "done"}:
            raise HTTPException(status_code=400, detail="Invalid assignment status")
        return {"assignments": store.list_content_assignments(status=status, assignee=assignee, limit=limit)}

    @api.post("/v1/content/assignments/{assignmentId}/status")
    def update_content_assignment_status(
        assignmentId: str,
        request: Request,
        req: ContentAssignmentStatusRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor", "reviewer"})
        assignment = store.update_content_assignment_status(assignmentId, req.status, context["actor"], note=req.note)
        if not assignment:
            raise HTTPException(status_code=404, detail="Content assignment not found")
        store.audit_log(
            "content_assignment_status_updated",
            actor=context["actor"],
            target_type="content_assignment",
            target_id=assignmentId,
            payload={"status": assignment["status"], "versionId": assignment["versionId"], "assignee": assignment["assignee"]},
        )
        return {"ok": True, "assignment": assignment}

    @api.get("/v1/content/versions")
    def list_content_versions(request: Request, limit: int = 50, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        return {"versions": store.list_content_versions(limit=limit)}

    @api.get("/v1/content/versions/{versionId}")
    def get_content_version(versionId: str, request: Request, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        version = store.get_content_version(versionId)
        if not version:
            raise HTTPException(status_code=404, detail="Content version not found")
        return {"version": version}

    @api.post("/v1/content/versions/{versionId}/branch")
    def branch_content_version(
        versionId: str,
        request: Request,
        req: ContentBranchRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        source_version = store.get_content_version(versionId)
        if not source_version:
            raise HTTPException(status_code=404, detail="Content version not found")
        branch = store.create_content_branch(
            source_version,
            actor=context["actor"],
            label=req.label,
            branch_name=req.branchName,
        )
        assignment = None
        if req.assignee:
            try:
                assignment = store.upsert_content_assignment(
                    branch["id"],
                    assignee=req.assignee,
                    actor=context["actor"],
                    priority=req.priority,
                    due_at=req.dueAt,
                    note=req.note,
                    status="todo",
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
        store.audit_log(
            "content_version_branched",
            actor=context["actor"],
            target_type="content_version",
            target_id=branch["id"],
            payload={
                "parentVersionId": versionId,
                "branchName": branch["branchName"],
                "assigned": assignment is not None,
                "assignee": assignment["assignee"] if assignment else None,
            },
        )
        if assignment:
            store.audit_log(
                "content_assignment_upserted",
                actor=context["actor"],
                target_type="content_assignment",
                target_id=assignment["id"],
                payload={"versionId": branch["id"], "assignee": assignment["assignee"], "status": assignment["status"]},
            )
        return {"ok": True, "version": branch, "assignment": assignment}

    @api.post("/v1/content/versions/{versionId}/assign")
    def assign_content_version(
        versionId: str,
        request: Request,
        req: ContentAssignmentRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        version = store.get_content_version(versionId)
        if not version:
            raise HTTPException(status_code=404, detail="Content version not found")
        try:
            assignment = store.upsert_content_assignment(
                versionId,
                assignee=req.assignee,
                actor=context["actor"],
                priority=req.priority,
                due_at=req.dueAt,
                note=req.note,
                status=req.status,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        store.audit_log(
            "content_assignment_upserted",
            actor=context["actor"],
            target_type="content_assignment",
            target_id=assignment["id"],
            payload={"versionId": versionId, "assignee": assignment["assignee"], "status": assignment["status"]},
        )
        return {"ok": True, "assignment": assignment}

    @api.post("/v1/content/versions/{versionId}/submit-review")
    def submit_content_version_review(
        versionId: str,
        request: Request,
        req: ContentReviewRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        existing = store.get_content_version(versionId)
        if not existing:
            raise HTTPException(status_code=404, detail="Content version not found")
        if existing["status"] not in {"draft", "rejected"}:
            raise HTTPException(status_code=409, detail="Only draft or rejected content versions can be submitted for review")
        version = store.submit_content_version_for_review(versionId, context["actor"], note=req.note)
        if not version:
            raise HTTPException(status_code=409, detail="Content version could not be submitted for review")
        store.audit_log(
            "content_version_submitted_for_review",
            actor=context["actor"],
            target_type="content_version",
            target_id=versionId,
            payload={"status": version["status"], "submittedAt": version["submittedAt"]},
        )
        return {"ok": True, "version": version}

    @api.post("/v1/content/versions/{versionId}/approve")
    def approve_content_version_review(
        versionId: str,
        request: Request,
        req: ContentReviewRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"reviewer"})
        existing = store.get_content_version(versionId)
        if not existing:
            raise HTTPException(status_code=404, detail="Content version not found")
        if existing["status"] != "in_review":
            raise HTTPException(status_code=409, detail="Only in-review content versions can be approved")
        if existing.get("submittedBy") == context["actor"]:
            raise HTTPException(status_code=409, detail="Content reviewer must be different from the submitter")
        report = _content_quality_report(existing["courses"], existing["practiceRooms"], store.list_personas())
        if not report["valid"]:
            raise HTTPException(status_code=400, detail={"message": "Content version validation failed", "report": report})
        version = store.approve_content_version(versionId, context["actor"], note=req.note)
        if not version:
            raise HTTPException(status_code=409, detail="Content version could not be approved")
        store.audit_log(
            "content_version_approved",
            actor=context["actor"],
            target_type="content_version",
            target_id=versionId,
            payload={"status": version["status"], "reviewedAt": version["reviewedAt"]},
        )
        return {"ok": True, "version": version}

    @api.post("/v1/content/versions/{versionId}/reject")
    def reject_content_version_review(
        versionId: str,
        request: Request,
        req: ContentReviewRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"reviewer"})
        existing = store.get_content_version(versionId)
        if not existing:
            raise HTTPException(status_code=404, detail="Content version not found")
        if existing["status"] != "in_review":
            raise HTTPException(status_code=409, detail="Only in-review content versions can be rejected")
        if existing.get("submittedBy") == context["actor"]:
            raise HTTPException(status_code=409, detail="Content reviewer must be different from the submitter")
        version = store.reject_content_version(versionId, context["actor"], note=req.note)
        if not version:
            raise HTTPException(status_code=409, detail="Content version could not be rejected")
        store.audit_log(
            "content_version_rejected",
            actor=context["actor"],
            target_type="content_version",
            target_id=versionId,
            payload={"status": version["status"], "reviewedAt": version["reviewedAt"]},
        )
        return {"ok": True, "version": version}

    @api.post("/v1/content/versions/{versionId}/publish")
    def publish_content_version(versionId: str, request: Request, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        context = require_admin_role(request, {"publisher"})
        version = store.get_content_version(versionId)
        if not version:
            raise HTTPException(status_code=404, detail="Content version not found")
        if version["status"] not in {"approved", "published"}:
            raise HTTPException(status_code=409, detail="Content version must be approved before publish")
        report = _content_quality_report(version["courses"], version["practiceRooms"], store.list_personas())
        if not report["valid"]:
            store.audit_log(
                "content_version_publish_rejected",
                actor=context["actor"],
                target_type="content_version",
                target_id=versionId,
                payload={"errorCount": len(report["errors"]), "counts": report["counts"]},
            )
            raise HTTPException(status_code=400, detail={"message": "Content version validation failed", "report": report})
        published = store.publish_content_version(versionId)
        if not published:
            raise HTTPException(status_code=404, detail="Content version not found")
        store.audit_log(
            "content_version_published",
            actor=context["actor"],
            target_type="content_version",
            target_id=versionId,
            payload={
                "snapshotCounts": published["snapshotCounts"],
                "importedCounts": published["importedCounts"],
                "publishedAt": published["publishedAt"],
            },
        )
        return {"ok": True, "version": published, "importedCounts": published["importedCounts"], "report": report}

    @api.get("/v1/content/releases")
    def list_content_releases(
        request: Request,
        status: Optional[str] = None,
        limit: int = 50,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        if status and status not in {"planned", "scheduled", "applied", "rolled_back", "canceled"}:
            raise HTTPException(status_code=400, detail="Invalid content release status")
        return {"releases": store.list_content_releases(status=status, limit=limit)}

    @api.post("/v1/content/releases")
    def create_content_release(
        request: Request,
        req: ContentReleaseRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor", "reviewer", "publisher"})
        payload = dump_model(req)
        if payload["releaseStrategy"] == "scheduled" and not payload.get("scheduledAt"):
            raise HTTPException(status_code=400, detail="scheduledAt is required for scheduled content releases")
        version = store.get_content_version(payload["versionId"])
        if not version:
            raise HTTPException(status_code=404, detail="Content version not found")
        if version["status"] not in {"approved", "published"}:
            raise HTTPException(status_code=409, detail="Content version must be approved before release planning")
        report = _content_quality_report(version["courses"], version["practiceRooms"], store.list_personas())
        if not report["valid"]:
            raise HTTPException(status_code=400, detail={"message": "Content version validation failed", "report": report})
        guardrails = {
            **payload.get("guardrails", {}),
            "qualityReportValid": report["valid"],
            "errorCount": len(report["errors"]),
            "warningCount": len(report["warnings"]),
            "snapshotCounts": version["snapshotCounts"],
        }
        try:
            release = store.create_content_release(
                version_id=version["id"],
                title=payload["title"],
                release_strategy=payload["releaseStrategy"],
                rollout_percent=payload["rolloutPercent"],
                catalog_scope=payload["catalogScope"],
                scheduled_at=payload.get("scheduledAt"),
                guardrails=guardrails,
                note=payload.get("note"),
                created_by=context["actor"],
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        store.audit_log(
            "content_release_planned",
            actor=context["actor"],
            target_type="content_release",
            target_id=release["id"],
            payload={
                "versionId": release["versionId"],
                "status": release["status"],
                "releaseStrategy": release["releaseStrategy"],
                "rolloutPercent": release["rolloutPercent"],
                "catalogScope": release["catalogScope"],
                "scheduledAt": release["scheduledAt"],
            },
        )
        return {"ok": True, "release": release, "report": report}

    def _execute_content_operation_job(job: Dict[str, Any], actor: str, store: ApiStore) -> Dict[str, Any]:
        payload = job.get("payload") or {}
        job_type = job["jobType"]
        if job_type == "validate_bundle":
            bundle = payload.get("bundle") if isinstance(payload.get("bundle"), dict) else payload
            courses = bundle.get("courses", []) if isinstance(bundle, dict) else []
            practice_rooms = bundle.get("practiceRooms", []) if isinstance(bundle, dict) else []
            report = _content_quality_report(courses, practice_rooms, store.list_personas())
            return {
                "ok": report["valid"],
                "jobType": job_type,
                "report": report,
                "counts": report["counts"],
            }
        if job_type == "import_bundle":
            bundle = payload.get("bundle") if isinstance(payload.get("bundle"), dict) else payload
            if not isinstance(bundle, dict):
                raise ValueError("import_bundle payload must include a bundle object or course/practiceRooms fields")
            courses = bundle.get("courses", [])
            practice_rooms = bundle.get("practiceRooms", [])
            dry_run = bool(payload.get("dryRun", bundle.get("dryRun", True)))
            replace_existing = bool(payload.get("replaceExisting", bundle.get("replaceExisting", True)))
            report = _content_quality_report(courses, practice_rooms, store.list_personas())
            if not report["valid"]:
                return {
                    "ok": False,
                    "jobType": job_type,
                    "rejected": True,
                    "report": report,
                    "counts": report["counts"],
                }
            if not replace_existing:
                existing_course_ids = {course["id"] for course in store.list_courses()}
                existing_room_ids = {room["id"] for room in store.list_practice_rooms()}
                conflicting_course_ids = sorted({course["id"] for course in courses} & existing_course_ids)
                conflicting_room_ids = sorted({room["id"] for room in practice_rooms} & existing_room_ids)
                if conflicting_course_ids or conflicting_room_ids:
                    for course_id in conflicting_course_ids:
                        report["errors"].append(
                            _content_issue(
                                "course_id_already_exists",
                                f"Course already exists and replaceExisting is false: {course_id}",
                                "/courses",
                                courseId=course_id,
                            )
                        )
                    for room_id in conflicting_room_ids:
                        report["errors"].append(
                            _content_issue(
                                "practice_room_id_already_exists",
                                f"Practice room already exists and replaceExisting is false: {room_id}",
                                "/practiceRooms",
                                practiceRoomId=room_id,
                            )
                        )
                    report["valid"] = False
                    return {
                        "ok": False,
                        "jobType": job_type,
                        "rejected": True,
                        "conflict": True,
                        "report": report,
                        "counts": report["counts"],
                    }
            annotated_rooms = _annotate_practice_rooms_with_course_metadata(courses, practice_rooms)
            imported_counts = {"courses": 0, "practiceRooms": 0}
            if not dry_run:
                imported_counts = store.upsert_content_bundle(courses, annotated_rooms)
            version = store.create_content_version(
                courses,
                annotated_rooms,
                report,
                imported_counts,
                source="content_operation_import_dry_run" if dry_run else "content_operation_import_apply",
                label="Content operation import dry-run" if dry_run else "Applied content operation import",
                status="draft" if dry_run else "published",
                created_by=actor,
            )
            return {
                "ok": True,
                "jobType": job_type,
                "dryRun": dry_run,
                "replaceExisting": replace_existing,
                "version": version,
                "importedCounts": imported_counts,
                "report": report,
            }
        if job_type == "run_due_releases":
            limit = int(payload.get("limit", 50))
            return {
                "ok": True,
                "jobType": job_type,
                **store.run_due_content_releases(actor=actor, limit=limit),
            }
        raise ValueError(f"unsupported content operation job type: {job_type}")

    def _run_next_content_operation_job_once(actor: Optional[str], store: ApiStore) -> Dict[str, Any]:
        job = store.claim_next_content_operation_job(actor)
        if not job:
            return {"ok": True, "job": None, "result": {"ok": True, "message": "no queued content operation jobs"}}
        try:
            result_payload = _execute_content_operation_job(job, actor, store)
            completed = store.complete_content_operation_job(job["id"], result_payload)
            if not completed:
                raise RuntimeError("content operation job could not be completed")
            store.audit_log(
                "content_operation_job_succeeded",
                actor=actor,
                target_type="content_operation_job",
                target_id=completed["id"],
                payload={"jobType": completed["jobType"], "resultOk": bool(result_payload.get("ok"))},
            )
            return {"ok": True, "job": completed, "result": result_payload}
        except Exception as exc:
            error_code = "content_operation_failed"
            LOGGER.warning("Content operation job failed: %s", exc.__class__.__name__)
            failed = store.fail_content_operation_job(job["id"], error_code, result_payload={"ok": False, "errorCode": error_code})
            store.audit_log(
                "content_operation_job_failed",
                actor=actor,
                target_type="content_operation_job",
                target_id=job["id"],
                payload={"jobType": job["jobType"], "errorCode": error_code, "errorType": exc.__class__.__name__[:80]},
            )
            return {"ok": False, "job": failed or store.get_content_operation_job(job["id"]), "error": "Content operation failed"}

    @api.get("/v1/content/operations/jobs")
    def list_content_operation_jobs(
        request: Request,
        status: Optional[str] = None,
        limit: int = 50,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        if status and status not in {"queued", "running", "succeeded", "failed", "canceled"}:
            raise HTTPException(status_code=400, detail="Invalid content operation job status")
        return {"jobs": store.list_content_operation_jobs(status=status, limit=limit)}

    @api.post("/v1/content/operations/jobs")
    def create_content_operation_job(
        request: Request,
        req: ContentOperationJobRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor", "reviewer", "publisher"})
        job = store.create_content_operation_job(
            job_type=req.jobType,
            payload=req.payload,
            priority=req.priority,
            created_by=context["actor"],
        )
        store.audit_log(
            "content_operation_job_queued",
            actor=context["actor"],
            target_type="content_operation_job",
            target_id=job["id"],
            payload={"jobType": job["jobType"], "priority": job["priority"]},
        )
        return {"ok": True, "job": job}

    @api.get("/v1/content/operations/jobs/{jobId}")
    def get_content_operation_job(jobId: str, request: Request, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        job = store.get_content_operation_job(jobId)
        if not job:
            raise HTTPException(status_code=404, detail="Content operation job not found")
        return {"job": job}

    @api.post("/v1/content/operations/jobs/run-next")
    def run_next_content_operation_job(
        request: Request,
        req: ContentOperationJobRunNextRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"publisher"})
        return _run_next_content_operation_job_once(context["actor"], store)

    @api.post("/v1/content/operations/jobs/{jobId}/cancel")
    def cancel_content_operation_job(
        jobId: str,
        request: Request,
        req: ContentOperationJobCancelRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor", "publisher"})
        job = store.cancel_content_operation_job(jobId, context["actor"])
        if not job:
            existing = store.get_content_operation_job(jobId)
            if not existing:
                raise HTTPException(status_code=404, detail="Content operation job not found")
            raise HTTPException(status_code=409, detail="Only queued content operation jobs can be canceled")
        store.audit_log(
            "content_operation_job_canceled",
            actor=context["actor"],
            target_type="content_operation_job",
            target_id=job["id"],
            payload={"jobType": job["jobType"], "priority": job["priority"]},
        )
        return {"ok": True, "job": job}

    @api.get("/v1/content/scheduler/runs")
    def list_content_scheduler_runs(
        request: Request,
        status: Optional[str] = None,
        limit: int = 50,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        if status and status not in {"running", "succeeded", "failed"}:
            raise HTTPException(status_code=400, detail="Invalid content scheduler run status")
        return {"runs": store.list_content_scheduler_runs(status=status, limit=limit)}

    @api.post("/v1/content/scheduler/run-once")
    def run_content_scheduler_once(
        request: Request,
        req: ContentSchedulerRunOnceRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"publisher"})
        try:
            run = store.start_content_scheduler_run(
                scheduler_key=req.schedulerKey,
                lease_owner=req.leaseOwner,
                actor=context["actor"],
                max_operation_jobs=req.maxOperationJobs,
                release_limit=req.releaseLimit,
            )
        except ValueError as exc:
            LOGGER.warning("Content scheduler could not start: %s", exc.__class__.__name__)
            raise HTTPException(status_code=409, detail="Content scheduler is currently unavailable") from None
        release_result: Dict[str, Any] = {}
        operation_job_runs: list[Dict[str, Any]] = []
        try:
            release_result = store.run_due_content_releases(actor=context["actor"], limit=req.releaseLimit)
            store.audit_log(
                "content_release_worker_run",
                actor=context["actor"],
                target_type="content_release_worker",
                payload={
                    "checkedCount": release_result["checkedCount"],
                    "appliedCount": release_result["appliedCount"],
                    "skippedCount": release_result["skippedCount"],
                    "ranAt": release_result["ranAt"],
                    "schedulerRunId": run["id"],
                },
            )
            for _ in range(req.maxOperationJobs):
                operation_job_run = _run_next_content_operation_job_once(context["actor"], store)
                if operation_job_run.get("job") is None:
                    break
                operation_job_runs.append(operation_job_run)
            failed_jobs = [item for item in operation_job_runs if not item.get("ok")]
            result_payload = {
                "ok": not failed_jobs,
                "releaseWorker": release_result,
                "operationJobs": operation_job_runs,
                "operationJobsRunCount": len(operation_job_runs),
                "operationJobsFailedCount": len(failed_jobs),
            }
            completed = store.complete_content_scheduler_run(
                run["id"],
                result_payload,
                status="failed" if failed_jobs else "succeeded",
                error=failed_jobs[0].get("error") if failed_jobs else None,
            )
            status_action = "content_scheduler_run_failed" if failed_jobs else "content_scheduler_run_succeeded"
            store.audit_log(
                status_action,
                actor=context["actor"],
                target_type="content_scheduler_run",
                target_id=run["id"],
                payload={
                    "schedulerKey": run["schedulerKey"],
                    "leaseOwner": run["leaseOwner"],
                    "appliedCount": release_result["appliedCount"],
                    "operationJobsRunCount": len(operation_job_runs),
                    "operationJobsFailedCount": len(failed_jobs),
                },
            )
            return {
                "ok": not failed_jobs,
                "run": completed or store.get_content_scheduler_run(run["id"]),
                "releaseWorker": release_result,
                "operationJobs": operation_job_runs,
            }
        except Exception as exc:
            error_code = "content_scheduler_failed"
            LOGGER.warning("Content scheduler run failed: %s", exc.__class__.__name__)
            result_payload = {
                "ok": False,
                "releaseWorker": release_result,
                "operationJobs": operation_job_runs,
                "operationJobsRunCount": len(operation_job_runs),
                "operationJobsFailedCount": len([item for item in operation_job_runs if not item.get("ok")]),
            }
            failed = store.complete_content_scheduler_run(run["id"], result_payload, status="failed", error=error_code)
            store.audit_log(
                "content_scheduler_run_failed",
                actor=context["actor"],
                target_type="content_scheduler_run",
                target_id=run["id"],
                payload={
                    "schedulerKey": run["schedulerKey"],
                    "leaseOwner": run["leaseOwner"],
                    "errorCode": error_code,
                    "errorType": exc.__class__.__name__[:80],
                },
            )
            return {
                "ok": False,
                "run": failed or store.get_content_scheduler_run(run["id"]),
                "releaseWorker": release_result,
                "operationJobs": operation_job_runs,
                "error": "Content scheduler failed",
            }

    @api.post("/v1/content/releases/run-due")
    def run_due_content_releases(
        request: Request,
        req: ContentReleaseRunDueRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"publisher"})
        result = store.run_due_content_releases(actor=context["actor"], limit=req.limit)
        store.audit_log(
            "content_release_worker_run",
            actor=context["actor"],
            target_type="content_release_worker",
            payload={
                "checkedCount": result["checkedCount"],
                "appliedCount": result["appliedCount"],
                "skippedCount": result["skippedCount"],
                "ranAt": result["ranAt"],
            },
        )
        return {"ok": True, **result}

    @api.post("/v1/content/releases/{releaseId}/apply")
    def apply_content_release(
        releaseId: str,
        request: Request,
        req: ContentReleaseApplyRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"publisher"})
        release = store.get_content_release(releaseId)
        if not release:
            raise HTTPException(status_code=404, detail="Content release not found")
        try:
            applied = store.apply_content_release(releaseId, actor=context["actor"], force=req.force)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        if not applied:
            raise HTTPException(status_code=404, detail="Content release not found")
        store.audit_log(
            "content_release_applied",
            actor=context["actor"],
            target_type="content_release",
            target_id=releaseId,
            payload={
                "versionId": applied["versionId"],
                "previousPublishedVersionId": applied["previousPublishedVersionId"],
                "releaseStrategy": applied["releaseStrategy"],
                "rolloutPercent": applied["rolloutPercent"],
                "catalogScope": applied["catalogScope"],
                "importedCounts": applied["importedCounts"],
                "forced": req.force,
            },
        )
        return {"ok": True, "release": applied, "version": applied.get("version"), "previousPublishedVersion": applied.get("previousPublishedVersion")}

    @api.post("/v1/content/releases/{releaseId}/rollback")
    def rollback_content_release(
        releaseId: str,
        request: Request,
        req: ContentReleaseRollbackRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"publisher"})
        if not store.get_content_release(releaseId):
            raise HTTPException(status_code=404, detail="Content release not found")
        try:
            rolled_back = store.rollback_content_release(releaseId, actor=context["actor"], note=req.note)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        if not rolled_back:
            raise HTTPException(status_code=404, detail="Content release not found")
        store.audit_log(
            "content_release_rolled_back",
            actor=context["actor"],
            target_type="content_release",
            target_id=releaseId,
            payload={
                "versionId": rolled_back["versionId"],
                "previousPublishedVersionId": rolled_back["previousPublishedVersionId"],
                "rollbackImportedCounts": rolled_back["rollbackImportedCounts"],
                "rollbackNote": rolled_back["rollbackNote"],
            },
        )
        return {"ok": True, "release": rolled_back, "version": rolled_back.get("previousPublishedVersion")}

    @api.get("/v1/experiments")
    def list_experiments(
        request: Request,
        status: Optional[str] = None,
        limit: int = 100,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        if status and status not in {"draft", "running", "paused", "archived"}:
            raise HTTPException(status_code=400, detail="Invalid experiment status")
        return {"experiments": store.list_experiments(status=status, limit=limit)}

    @api.post("/v1/experiments")
    def upsert_experiment(
        request: Request,
        req: ExperimentRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        payload = dump_model(req)
        try:
            experiment = store.upsert_experiment(
                key=payload["key"],
                name=payload["name"],
                status=payload["status"],
                variants=payload["variants"],
                allocation=payload["allocation"],
                created_by=context["actor"],
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        store.audit_log(
            "experiment_upserted",
            actor=context["actor"],
            target_type="experiment",
            target_id=experiment["key"],
            payload={"status": experiment["status"], "variantCount": len(experiment["variants"])},
        )
        return {"ok": True, "experiment": experiment}

    @api.get("/v1/experiments/assignments")
    def list_my_experiment_assignments(
        exposure: bool = True,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        assignments = store.list_experiment_assignments(learner_id=learner_id, project_id=PROJECT_ID, log_exposure=exposure)
        return {"assignments": assignments, "exposureLogged": bool(exposure), "assignmentCount": len(assignments)}

    @api.get("/v1/experiments/{experimentKey}/analytics")
    def get_experiment_analytics(
        experimentKey: str,
        request: Request,
        minimumExposedLearners: int = 30,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        analytics = store.experiment_analytics(experimentKey, minimum_exposed_learners=minimumExposedLearners)
        if not analytics:
            raise HTTPException(status_code=404, detail="Experiment not found")
        store.audit_log(
            "experiment_analytics_viewed",
            actor=context["actor"],
            target_type="experiment",
            target_id=analytics["experiment"]["key"],
            payload={
                "minimumExposedLearners": analytics["minimumExposedLearners"],
                "decisionReady": analytics["decisionReady"],
                "bestObservedVariantKey": analytics["bestObservedVariantKey"],
                "winnerVariantKey": analytics["winnerVariantKey"],
            },
        )
        return {"ok": True, "analytics": analytics}

    @api.get("/v1/experiments/{experimentKey}/decisions")
    def list_experiment_decisions(
        experimentKey: str,
        request: Request,
        limit: int = 50,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        if not store.get_experiment(experimentKey):
            raise HTTPException(status_code=404, detail="Experiment not found")
        return {"decisions": store.list_experiment_decisions(experimentKey, limit=limit)}

    @api.post("/v1/experiments/{experimentKey}/decisions")
    def propose_experiment_decision(
        experimentKey: str,
        request: Request,
        req: ExperimentDecisionRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor", "reviewer", "publisher"})
        payload = dump_model(req)
        analytics = store.experiment_analytics(experimentKey, minimum_exposed_learners=payload["minimumExposedLearners"])
        if not analytics:
            raise HTTPException(status_code=404, detail="Experiment not found")
        plan = _experiment_decision_plan(payload, analytics)
        guardrail = _experiment_decision_guardrail(payload, analytics, plan["action"], plan["variantKey"])
        if not guardrail["ok"]:
            store.audit_log(
                "experiment_decision_rejected",
                actor=context["actor"],
                target_type="experiment",
                target_id=analytics["experiment"]["key"],
                payload=guardrail,
            )
            raise HTTPException(status_code=409, detail={"message": "Experiment decision guardrail failed", "guardrail": guardrail})
        decision = store.create_experiment_decision(
            experiment_key=analytics["experiment"]["key"],
            action=plan["action"],
            variant_key=plan["variantKey"],
            analytics_snapshot=analytics,
            guardrail=guardrail,
            minimum_exposed_learners=payload["minimumExposedLearners"],
            created_by=context["actor"],
            reason=payload.get("reason"),
        )
        store.audit_log(
            "experiment_decision_proposed",
            actor=context["actor"],
            target_type="experiment_decision",
            target_id=decision["id"],
            payload={
                "experimentKey": decision["experimentKey"],
                "action": decision["action"],
                "variantKey": decision["variantKey"],
                "decisionReady": guardrail["decisionReady"],
                "winnerVariantKey": guardrail["winnerVariantKey"],
            },
        )
        return {"ok": True, "decision": decision, "guardrail": guardrail}

    @api.post("/v1/experiments/{experimentKey}/decisions/{decisionId}/apply")
    def apply_experiment_decision(
        experimentKey: str,
        decisionId: str,
        request: Request,
        req: ExperimentDecisionApplyRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"publisher"})
        decision = store.get_experiment_decision(decisionId)
        if not decision or decision["experimentKey"] != normalize_experiment_key(experimentKey):
            raise HTTPException(status_code=404, detail="Experiment decision not found")
        guardrail = decision.get("guardrail") or {}
        if not guardrail.get("ok"):
            raise HTTPException(status_code=409, detail="Experiment decision guardrail is not satisfied")
        try:
            applied = store.apply_experiment_decision(decisionId, actor=context["actor"], note=req.note)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        if not applied:
            raise HTTPException(status_code=404, detail="Experiment decision not found")
        store.audit_log(
            "experiment_decision_applied",
            actor=context["actor"],
            target_type="experiment_decision",
            target_id=decisionId,
            payload={
                "experimentKey": applied["experimentKey"],
                "action": applied["action"],
                "variantKey": applied["variantKey"],
                "experimentStatus": (applied.get("experimentAfterApply") or {}).get("status"),
            },
        )
        return {"ok": True, "decision": applied, "experiment": applied.get("experimentAfterApply")}

    @api.post("/v1/experiments/{experimentKey}/status")
    def update_experiment_status(
        experimentKey: str,
        request: Request,
        req: ExperimentStatusRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        experiment = store.update_experiment_status(experimentKey, req.status)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        store.audit_log(
            "experiment_status_updated",
            actor=context["actor"],
            target_type="experiment",
            target_id=experiment["key"],
            payload={"status": experiment["status"]},
        )
        return {"ok": True, "experiment": experiment}

    @api.post("/v1/experiments/{experimentKey}/events")
    def record_experiment_event(
        experimentKey: str,
        req: ExperimentEventRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        payload = dump_model(req)
        event = store.record_experiment_event(
            learner_id=learner_id,
            experiment_key=experimentKey,
            event_name=payload["eventName"],
            payload=payload["payload"],
        )
        if not event:
            raise HTTPException(status_code=404, detail="Experiment assignment not found")
        return {"ok": True, "event": event}

    @api.post("/v1/auth/register")
    def auth_register(request: Request, req: AuthRegisterRequest, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        email = _normalize_email(req.email)
        email_hash = _email_hash(email)
        client_hash = _client_hash(request)
        register_window_seconds = _auth_register_window_seconds()
        recent_attempts = store.count_auth_attempts(email_hash, client_hash, _past_iso(register_window_seconds), purpose="register")
        if recent_attempts >= _auth_register_max_attempts():
            store.audit_log(
                "auth_registration_throttled",
                actor="account_auth",
                target_type="client_hash",
                target_id=client_hash,
                payload={
                    "emailHash": email_hash,
                    "recentAttempts": recent_attempts,
                    "windowSeconds": register_window_seconds,
                },
            )
            raise HTTPException(status_code=429, detail="Too many registration attempts")
        if store.get_account_by_email(email):
            store.record_auth_attempt(email_hash, client_hash, succeeded=False, purpose="register")
            store.audit_log(
                "auth_registration_rejected",
                actor="account_auth",
                target_type="email_hash",
                target_id=email_hash,
                payload={"reason": "account_exists"},
            )
            raise HTTPException(status_code=409, detail="Account already exists")
        learner_id = normalize_learner_id(req.learnerId or _default_account_learner_id(email))
        try:
            account = store.create_account(email, learner_id, _hash_password(req.password))
        except sqlite3.IntegrityError:
            store.record_auth_attempt(email_hash, client_hash, succeeded=False, purpose="register")
            store.audit_log(
                "auth_registration_rejected",
                actor="account_auth",
                target_type="email_hash",
                target_id=email_hash,
                payload={"reason": "integrity_conflict", "learnerId": learner_id},
            )
            raise HTTPException(status_code=409, detail="Account or learner id already exists")
        store.record_auth_attempt(email_hash, client_hash, succeeded=True, purpose="register")
        tokens = _issue_account_tokens(store, account, req.deviceLabel, req.deviceId)
        store.audit_log(
            "auth_account_registered",
            actor="account_auth",
            target_type="account",
            target_id=account["id"],
            payload={"deviceBound": bool(req.deviceId), "registrationThrottleWindowSeconds": register_window_seconds},
        )
        return {"account": _public_account(account), **tokens}

    @api.post("/v1/auth/login")
    def auth_login(request: Request, req: AuthLoginRequest, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        email = _normalize_email(req.email)
        email_hash = _email_hash(email)
        client_hash = _client_hash(request)
        risk_window_seconds = _auth_risk_window_seconds()
        distinct_failed_emails = store.count_distinct_failed_login_emails_by_client(client_hash, _past_iso(risk_window_seconds))
        if distinct_failed_emails >= _auth_risk_max_distinct_emails():
            store.audit_log(
                "auth_login_risk_blocked",
                actor="account_auth",
                target_type="client_hash",
                target_id=client_hash,
                payload={
                    "distinctFailedEmailHashes": distinct_failed_emails,
                    "windowSeconds": risk_window_seconds,
                    "control": "password_spray_client_guard",
                },
            )
            raise HTTPException(status_code=429, detail="Login temporarily blocked by risk controls")
        recent_failures = store.count_failed_auth_attempts(email_hash, client_hash, _past_iso(_auth_failure_window_seconds()))
        if recent_failures >= _auth_max_failures():
            store.audit_log(
                "auth_login_throttled",
                actor="account_auth",
                target_type="email_hash",
                target_id=email_hash,
                payload={"recentFailures": recent_failures, "windowSeconds": _auth_failure_window_seconds()},
            )
            raise HTTPException(status_code=429, detail="Too many failed login attempts")
        account = store.get_account_by_email(email)
        if not account or account.get("disabledAt") or not _verify_password(req.password, account.get("passwordHash", "")):
            store.record_auth_attempt(email_hash, client_hash, succeeded=False)
            store.audit_log(
                "auth_login_failed",
                actor="account_auth",
                target_type="email_hash",
                target_id=email_hash,
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")
        store.record_auth_attempt(email_hash, client_hash, succeeded=True)
        store.clear_failed_auth_attempts(email_hash, client_hash)
        tokens = _issue_account_tokens(store, account, req.deviceLabel, req.deviceId)
        store.audit_log("auth_login_succeeded", actor="account_auth", target_type="account", target_id=account["id"])
        return {"account": _public_account(account), **tokens}

    @api.get("/v1/auth/sso/discovery")
    def auth_sso_discovery(email: str, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        normalized_email = _normalize_email(email)
        domain = _email_domain(normalized_email)
        connection = store.find_enterprise_sso_connection_for_email(normalized_email)
        return {
            "ok": True,
            "emailDomain": domain,
            "matched": bool(connection),
            "connection": _public_enterprise_sso_connection(connection) if connection else None,
        }

    @api.get("/v1/admin/auth/sso-connections")
    def admin_list_sso_connections(
        request: Request,
        includeDisabled: bool = True,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        connections = [
            _public_enterprise_sso_connection(connection)
            for connection in store.list_enterprise_sso_connections(include_disabled=includeDisabled)
        ]
        return {"connections": connections, "count": len(connections)}

    @api.put("/v1/admin/auth/sso-connections/{connectionId}")
    def admin_upsert_sso_connection(
        connectionId: str,
        request: Request,
        req: AuthSsoConnectionRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        provider = req.provider.strip().lower()
        if provider not in _oidc_allowed_providers():
            raise HTTPException(status_code=400, detail="SSO provider is not allowed")
        if not req.domains:
            raise HTTPException(status_code=400, detail="At least one SSO domain is required")
        if not req.redirectUris:
            raise HTTPException(status_code=400, detail="At least one SSO redirect URI is required")
        connection = store.upsert_enterprise_sso_connection(
            connection_id=connectionId,
            provider=provider,
            organization_name=req.organizationName,
            domains=req.domains,
            redirect_uris=req.redirectUris,
            required_email_domain=req.requiredEmailDomain,
            status=req.status,
            actor=context["actor"],
        )
        store.audit_log(
            "auth_sso_connection_upserted",
            actor=context["actor"],
            target_type="enterprise_sso_connection",
            target_id=connection["id"],
            payload={
                "provider": connection["provider"],
                "domains": connection["domains"],
                "redirectUriCount": len(connection["redirectUris"]),
                "status": connection["status"],
            },
        )
        return {"ok": True, "connection": _public_enterprise_sso_connection(connection)}

    @api.post("/v1/auth/sso/pkce/start")
    def auth_sso_pkce_start(
        request: Request,
        req: AuthSsoPkceStartRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        email = _normalize_email(req.email)
        connection = store.find_enterprise_sso_connection_for_email(email)
        if not connection:
            raise HTTPException(status_code=404, detail="No enterprise SSO connection matches this email domain")
        provider = connection["provider"]
        if provider not in _oidc_allowed_providers():
            raise HTTPException(status_code=400, detail="SSO provider is not allowed")
        if req.codeChallengeMethod != "S256" or not _pkce_token_valid(req.codeChallenge):
            raise HTTPException(status_code=400, detail="Only valid S256 PKCE code challenges are accepted")
        redirect_uri = req.redirectUri.strip()
        if not _enterprise_sso_redirect_uri_allowed(connection, redirect_uri):
            raise HTTPException(status_code=400, detail="SSO redirect URI is not allowed for this connection")
        if not _oauth_authorization_endpoint(provider) or not _oauth_client_id(provider):
            raise HTTPException(status_code=503, detail="SSO provider is not configured")
        if not _oauth_token_endpoint(provider) and not _oauth_local_signed_code_allowed():
            raise HTTPException(status_code=503, detail="SSO token endpoint is not configured")
        state = "alp_sso_state_" + secrets.token_urlsafe(32)
        nonce = (req.nonce or "alp_sso_nonce_" + secrets.token_urlsafe(24)).strip()
        scope = (req.scope or _oauth_default_scope(provider)).strip()
        expires_at = _future_iso(_oauth_pkce_ttl_seconds())
        pkce_request = store.create_oauth_pkce_request(
            provider=provider,
            state_hash=_oauth_state_hash(state),
            redirect_uri=redirect_uri,
            code_challenge=req.codeChallenge,
            code_challenge_method="S256",
            scope=scope,
            nonce=nonce,
            learner_id=req.learnerId,
            device_label=req.deviceLabel,
            client_hash=_client_hash(request),
            expires_at=expires_at,
            enterprise_sso_connection_id=connection["id"],
        )
        authorization_url = _oauth_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
            state=state,
            nonce=nonce,
            code_challenge=req.codeChallenge,
            scope=scope,
        )
        store.audit_log(
            "auth_sso_pkce_started",
            actor="account_auth",
            target_type="enterprise_sso_connection",
            target_id=connection["id"],
            payload={"provider": provider, "emailDomain": _email_domain(email), "pkceRequestId": pkce_request["id"], "expiresAt": expires_at},
        )
        return {
            "ok": True,
            "provider": provider,
            "connectionId": connection["id"],
            "connection": _public_enterprise_sso_connection(connection),
            "authorizationUrl": authorization_url,
            "state": state,
            "nonce": nonce,
            "redirectUri": redirect_uri,
            "codeChallengeMethod": "S256",
            "expiresAt": expires_at,
        }

    @api.post("/v1/auth/sso/pkce/callback")
    def auth_sso_pkce_callback(
        request: Request,
        req: AuthSsoPkceCallbackRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        connection = store.get_enterprise_sso_connection(req.connectionId, enabled_only=True)
        if not connection:
            raise HTTPException(status_code=404, detail="Enterprise SSO connection not found")
        provider = connection["provider"]
        pkce_request = store.consume_oauth_pkce_request(provider, _oauth_state_hash(req.state))
        if not pkce_request:
            store.audit_log(
                "auth_sso_pkce_rejected",
                actor="account_auth",
                target_type="client_hash",
                target_id=_client_hash(request),
                payload={"connectionId": req.connectionId, "provider": provider, "reason": "invalid_or_expired_state"},
            )
            raise HTTPException(status_code=401, detail="Invalid or expired SSO state")
        if pkce_request.get("enterpriseSsoConnectionId") != connection["id"]:
            store.audit_log(
                "auth_sso_pkce_rejected",
                actor="account_auth",
                target_type="oauth_pkce_request",
                target_id=pkce_request["id"],
                payload={"connectionId": connection["id"], "provider": provider, "reason": "connection_mismatch"},
            )
            raise HTTPException(status_code=401, detail="SSO connection mismatch")
        if req.redirectUri.strip() != pkce_request["redirectUri"]:
            store.audit_log(
                "auth_sso_pkce_rejected",
                actor="account_auth",
                target_type="oauth_pkce_request",
                target_id=pkce_request["id"],
                payload={"connectionId": connection["id"], "provider": provider, "reason": "redirect_uri_mismatch"},
            )
            raise HTTPException(status_code=401, detail="SSO redirect URI mismatch")
        if not _pkce_token_valid(req.codeVerifier):
            raise HTTPException(status_code=400, detail="Invalid PKCE code verifier")
        expected_challenge = _pkce_s256_challenge(req.codeVerifier)
        if not hmac.compare_digest(expected_challenge, pkce_request["codeChallenge"]):
            store.audit_log(
                "auth_sso_pkce_rejected",
                actor="account_auth",
                target_type="oauth_pkce_request",
                target_id=pkce_request["id"],
                payload={"connectionId": connection["id"], "provider": provider, "reason": "pkce_challenge_mismatch"},
            )
            raise HTTPException(status_code=401, detail="Invalid SSO PKCE verifier")
        claims, exchange_mode = _oauth_claims_from_authorization_code(
            provider=provider,
            code=req.code,
            code_verifier=req.codeVerifier,
            redirect_uri=pkce_request["redirectUri"],
            nonce=pkce_request.get("nonce"),
            state=req.state,
        )
        if not claims:
            store.audit_log(
                "auth_sso_pkce_rejected",
                actor="account_auth",
                target_type="oauth_pkce_request",
                target_id=pkce_request["id"],
                payload={"connectionId": connection["id"], "provider": provider, "reason": "code_exchange_or_id_token_verification_failed", "exchangeMode": exchange_mode},
            )
            raise HTTPException(status_code=401, detail="Invalid SSO authorization code")
        email = _normalize_email(str(claims["email"]))
        if not _enterprise_sso_email_allowed(connection, email):
            store.audit_log(
                "auth_sso_pkce_rejected",
                actor="account_auth",
                target_type="enterprise_sso_connection",
                target_id=connection["id"],
                payload={"provider": provider, "reason": "email_domain_not_allowed", "emailDomain": _email_domain(email)},
            )
            raise HTTPException(status_code=401, detail="SSO email domain is not allowed for this connection")
        identity_provider = f"sso:{connection['id']}"
        profile = {
            "issuer": claims.get("iss"),
            "audience": claims.get("aud"),
            "noncePresent": bool(claims.get("nonce")),
            "oauthPkce": True,
            "enterpriseSso": True,
            "connectionId": connection["id"],
            "organizationName": connection["organizationName"],
            "underlyingProvider": provider,
            "codeExchangeMode": exchange_mode,
        }
        try:
            account = store.upsert_external_identity_account(
                provider=identity_provider,
                subject=str(claims["sub"]),
                email=email,
                email_verified=bool(claims.get("email_verified")),
                profile=profile,
                learner_id=req.learnerId or pkce_request.get("learnerId"),
                password_hash=_hash_password("external:" + secrets.token_urlsafe(48)),
            )
        except sqlite3.IntegrityError:
            store.audit_log(
                "auth_sso_pkce_rejected",
                actor="account_auth",
                target_type="email_hash",
                target_id=_email_hash(email),
                payload={"connectionId": connection["id"], "provider": provider, "reason": "identity_or_learner_conflict"},
            )
            raise HTTPException(status_code=409, detail="SSO account link conflict")
        if account.get("disabledAt"):
            raise HTTPException(status_code=401, detail="Account is disabled")
        tokens = _issue_account_tokens(store, account, req.deviceLabel or pkce_request.get("deviceLabel"), req.deviceId)
        store.audit_log(
            "auth_sso_pkce_succeeded",
            actor="account_auth",
            target_type="account",
            target_id=account["id"],
            payload={
                "connectionId": connection["id"],
                "provider": provider,
                "identityProvider": identity_provider,
                "emailHash": _email_hash(email),
                "emailDomain": _email_domain(email),
                "deviceBound": bool(req.deviceId),
                "exchangeMode": exchange_mode,
                "pkceRequestId": pkce_request["id"],
            },
        )
        return {
            "account": _public_account(account),
            **tokens,
            "oauth": {"provider": provider, "stateConsumed": True, "codeExchangeMode": exchange_mode},
            "sso": {
                "connectionId": connection["id"],
                "provider": provider,
                "identityProvider": identity_provider,
                "organizationName": connection["organizationName"],
                "emailDomain": _email_domain(email),
            },
        }

    @api.post("/v1/auth/oidc")
    def auth_oidc(request: Request, req: AuthOidcRequest, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        provider = req.provider.strip().lower()
        claims = _decode_oidc_id_token(provider, req.idToken, nonce=req.nonce)
        if not claims:
            store.audit_log(
                "auth_oidc_rejected",
                actor="account_auth",
                target_type="client_hash",
                target_id=_client_hash(request),
                payload={"provider": provider, "reason": "invalid_id_token"},
            )
            raise HTTPException(status_code=401, detail="Invalid OIDC id token")
        email = _normalize_email(str(claims["email"]))
        profile = {
            "issuer": claims.get("iss"),
            "audience": claims.get("aud"),
            "name": claims.get("name"),
            "picture": claims.get("picture"),
            "noncePresent": bool(claims.get("nonce")),
        }
        try:
            account = store.upsert_external_identity_account(
                provider=provider,
                subject=str(claims["sub"]),
                email=email,
                email_verified=bool(claims.get("email_verified")),
                profile=profile,
                learner_id=req.learnerId,
                password_hash=_hash_password("external:" + secrets.token_urlsafe(48)),
            )
        except sqlite3.IntegrityError:
            store.audit_log(
                "auth_oidc_rejected",
                actor="account_auth",
                target_type="email_hash",
                target_id=_email_hash(email),
                payload={"provider": provider, "reason": "identity_or_learner_conflict"},
            )
            raise HTTPException(status_code=409, detail="OIDC account link conflict")
        if account.get("disabledAt"):
            raise HTTPException(status_code=401, detail="Account is disabled")
        tokens = _issue_account_tokens(store, account, req.deviceLabel, req.deviceId)
        store.audit_log(
            "auth_oidc_succeeded",
            actor="account_auth",
            target_type="account",
            target_id=account["id"],
            payload={"provider": provider, "emailHash": _email_hash(email), "deviceBound": bool(req.deviceId)},
        )
        return {"account": _public_account(account), **tokens}

    @api.post("/v1/auth/oauth/pkce/start")
    def auth_oauth_pkce_start(
        request: Request,
        req: AuthOAuthPkceStartRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        provider = req.provider.strip().lower()
        if provider not in _oidc_allowed_providers():
            raise HTTPException(status_code=400, detail="OAuth provider is not allowed")
        if req.codeChallengeMethod != "S256" or not _pkce_token_valid(req.codeChallenge):
            raise HTTPException(status_code=400, detail="Only valid S256 PKCE code challenges are accepted")
        redirect_uri = req.redirectUri.strip()
        if not _oauth_redirect_uri_allowed(provider, redirect_uri):
            raise HTTPException(status_code=400, detail="OAuth redirect URI is not allowed")
        if not _oauth_authorization_endpoint(provider) or not _oauth_client_id(provider):
            raise HTTPException(status_code=503, detail="OAuth provider is not configured")
        if not _oauth_token_endpoint(provider) and not _oauth_local_signed_code_allowed():
            raise HTTPException(status_code=503, detail="OAuth token endpoint is not configured")
        state = "alp_oauth_state_" + secrets.token_urlsafe(32)
        nonce = (req.nonce or "alp_oauth_nonce_" + secrets.token_urlsafe(24)).strip()
        scope = (req.scope or _oauth_default_scope(provider)).strip()
        expires_at = _future_iso(_oauth_pkce_ttl_seconds())
        pkce_request = store.create_oauth_pkce_request(
            provider=provider,
            state_hash=_oauth_state_hash(state),
            redirect_uri=redirect_uri,
            code_challenge=req.codeChallenge,
            code_challenge_method="S256",
            scope=scope,
            nonce=nonce,
            learner_id=req.learnerId,
            device_label=req.deviceLabel,
            client_hash=_client_hash(request),
            expires_at=expires_at,
        )
        authorization_url = _oauth_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
            state=state,
            nonce=nonce,
            code_challenge=req.codeChallenge,
            scope=scope,
        )
        store.audit_log(
            "auth_oauth_pkce_started",
            actor="account_auth",
            target_type="oauth_pkce_request",
            target_id=pkce_request["id"],
            payload={"provider": provider, "redirectUri": redirect_uri, "scope": scope, "expiresAt": expires_at},
        )
        return {
            "ok": True,
            "provider": provider,
            "authorizationUrl": authorization_url,
            "state": state,
            "nonce": nonce,
            "redirectUri": redirect_uri,
            "codeChallengeMethod": "S256",
            "expiresAt": expires_at,
        }

    @api.post("/v1/auth/oauth/pkce/callback")
    def auth_oauth_pkce_callback(
        request: Request,
        req: AuthOAuthPkceCallbackRequest,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        provider = req.provider.strip().lower()
        pkce_request = store.consume_oauth_pkce_request(provider, _oauth_state_hash(req.state))
        if not pkce_request:
            store.audit_log(
                "auth_oauth_pkce_rejected",
                actor="account_auth",
                target_type="client_hash",
                target_id=_client_hash(request),
                payload={"provider": provider, "reason": "invalid_or_expired_state"},
            )
            raise HTTPException(status_code=401, detail="Invalid or expired OAuth state")
        if req.redirectUri.strip() != pkce_request["redirectUri"]:
            store.audit_log(
                "auth_oauth_pkce_rejected",
                actor="account_auth",
                target_type="oauth_pkce_request",
                target_id=pkce_request["id"],
                payload={"provider": provider, "reason": "redirect_uri_mismatch"},
            )
            raise HTTPException(status_code=401, detail="OAuth redirect URI mismatch")
        if not _pkce_token_valid(req.codeVerifier):
            raise HTTPException(status_code=400, detail="Invalid PKCE code verifier")
        expected_challenge = _pkce_s256_challenge(req.codeVerifier)
        if not hmac.compare_digest(expected_challenge, pkce_request["codeChallenge"]):
            store.audit_log(
                "auth_oauth_pkce_rejected",
                actor="account_auth",
                target_type="oauth_pkce_request",
                target_id=pkce_request["id"],
                payload={"provider": provider, "reason": "pkce_challenge_mismatch"},
            )
            raise HTTPException(status_code=401, detail="Invalid OAuth PKCE verifier")
        claims, exchange_mode = _oauth_claims_from_authorization_code(
            provider=provider,
            code=req.code,
            code_verifier=req.codeVerifier,
            redirect_uri=pkce_request["redirectUri"],
            nonce=pkce_request.get("nonce"),
            state=req.state,
        )
        if not claims:
            store.audit_log(
                "auth_oauth_pkce_rejected",
                actor="account_auth",
                target_type="oauth_pkce_request",
                target_id=pkce_request["id"],
                payload={"provider": provider, "reason": "code_exchange_or_id_token_verification_failed", "exchangeMode": exchange_mode},
            )
            raise HTTPException(status_code=401, detail="Invalid OAuth authorization code")
        email = _normalize_email(str(claims["email"]))
        profile = {
            "issuer": claims.get("iss"),
            "audience": claims.get("aud"),
            "noncePresent": bool(claims.get("nonce")),
            "oauthPkce": True,
            "codeExchangeMode": exchange_mode,
        }
        try:
            account = store.upsert_external_identity_account(
                provider=provider,
                subject=str(claims["sub"]),
                email=email,
                email_verified=bool(claims.get("email_verified")),
                profile=profile,
                learner_id=req.learnerId or pkce_request.get("learnerId"),
                password_hash=_hash_password("external:" + secrets.token_urlsafe(48)),
            )
        except sqlite3.IntegrityError:
            store.audit_log(
                "auth_oauth_pkce_rejected",
                actor="account_auth",
                target_type="email_hash",
                target_id=_email_hash(email),
                payload={"provider": provider, "reason": "identity_or_learner_conflict"},
            )
            raise HTTPException(status_code=409, detail="OAuth account link conflict")
        if account.get("disabledAt"):
            raise HTTPException(status_code=401, detail="Account is disabled")
        tokens = _issue_account_tokens(store, account, req.deviceLabel or pkce_request.get("deviceLabel"), req.deviceId)
        store.audit_log(
            "auth_oauth_pkce_succeeded",
            actor="account_auth",
            target_type="account",
            target_id=account["id"],
            payload={
                "provider": provider,
                "emailHash": _email_hash(email),
                "deviceBound": bool(req.deviceId),
                "exchangeMode": exchange_mode,
                "pkceRequestId": pkce_request["id"],
            },
        )
        return {
            "account": _public_account(account),
            **tokens,
            "oauth": {"provider": provider, "stateConsumed": True, "codeExchangeMode": exchange_mode},
        }

    @api.post("/v1/auth/refresh")
    def auth_refresh(req: AuthRefreshRequest, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        refresh_hash = _token_hash(req.refreshToken)
        session = store.get_session_by_refresh_hash(refresh_hash, device_id_hash=_device_id_hash(req.deviceId))
        if not session:
            replayed = store.get_any_session_by_refresh_hash(refresh_hash)
            if replayed and replayed.get("revokedAt"):
                revoked_count = store.revoke_account_sessions(replayed["accountId"])
                store.audit_log(
                    "auth_refresh_reuse_detected",
                    actor="account_auth",
                    target_type="account",
                    target_id=replayed["accountId"],
                    payload={
                        "replayedSessionId": replayed["id"],
                        "revokedCount": revoked_count,
                        "deviceBound": bool(replayed.get("deviceBound")),
                    },
                )
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        account = store.get_account_by_id(session["accountId"])
        if not account:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        store.revoke_session(session["id"])
        tokens = _issue_account_tokens(store, account, req.deviceLabel or session.get("deviceLabel"), req.deviceId)
        return {"account": _public_account(account), **tokens}

    @api.get("/v1/auth/me")
    def auth_me(session: Dict[str, Any] = Depends(get_account_session)) -> Dict[str, Any]:
        return {"account": _public_account(session), "session": _public_session(session)}

    @api.post("/v1/auth/logout")
    def auth_logout(session: Dict[str, Any] = Depends(get_account_session), store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        return {"ok": store.revoke_session(session["id"])}

    @api.get("/v1/auth/sessions")
    def auth_sessions(
        includeRevoked: bool = False,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        sessions = [
            _public_session(item, current_session_id=session["id"])
            for item in store.list_account_sessions(session["accountId"], include_revoked=includeRevoked)
        ]
        return {
            "sessions": sessions,
            "currentSessionId": session["id"],
            "activeSessionCount": sum(1 for item in sessions if not item.get("revokedAt")),
        }

    @api.get("/v1/auth/devices")
    def auth_devices(
        includeRevoked: bool = False,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        devices = [
            _public_device(item)
            for item in store.list_account_devices(
                session["accountId"],
                include_revoked=includeRevoked,
                current_device_id_hash=session.get("deviceIdHash"),
            )
        ]
        return {
            "devices": devices,
            "currentDeviceId": next((item["id"] for item in devices if item.get("isCurrent")), None),
            "activeDeviceCount": sum(1 for item in devices if item.get("trustStatus") != "revoked"),
        }

    @api.post("/v1/auth/devices/attestation/challenge")
    def auth_device_attestation_challenge(
        req: AuthDeviceAttestationChallengeRequest,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        if not session.get("deviceBound") or not session.get("deviceIdHash"):
            raise HTTPException(status_code=400, detail="Current session is not bound to a device")
        provider = (req.attestationProvider or "signed_challenge").strip().lower()
        if provider not in DEVICE_ATTESTATION_HMAC_PROVIDERS | DEVICE_ATTESTATION_PUBLIC_KEY_PROVIDERS:
            raise HTTPException(status_code=400, detail="Unsupported device attestation provider")
        if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS and not _device_attestation_secret():
            raise HTTPException(status_code=503, detail="Device attestation verifier is not configured")
        attestation_subject = (req.attestationSubject or session.get("deviceLabel") or "bound-device").strip()
        if provider in DEVICE_ATTESTATION_PUBLIC_KEY_PROVIDERS and not (req.attestationSubject or "").strip():
            raise HTTPException(status_code=400, detail="attestationSubject is required for public-key attestation")
        challenge = "alp_dev_att_" + secrets.token_urlsafe(32)
        expires_at = _future_iso(_device_attestation_challenge_ttl_seconds())
        record = store.create_account_device_attestation_challenge(
            account_id=session["accountId"],
            device_id_hash=session["deviceIdHash"],
            provider=provider,
            challenge_hash=_device_attestation_challenge_hash(challenge),
            expires_at=expires_at,
        )
        message = _device_attestation_message(provider, record["id"], challenge, attestation_subject)
        store.audit_log(
            "auth_device_attestation_challenge_issued",
            actor="account_auth",
            target_type="device",
            target_id=session["deviceIdHash"][:16],
            payload={
                "accountId": session["accountId"],
                "challengeId": record["id"],
                "provider": provider,
                "expiresAt": expires_at,
            },
        )
        return {
            "challengeId": record["id"],
            "challenge": challenge,
            "expiresAt": expires_at,
            "attestationProvider": provider,
            "attestationSubject": attestation_subject,
            "signatureAlgorithm": (
                "hmac-sha256"
                if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS
                else "webauthn-es256"
                if provider in DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS
                else "rs256"
            ),
            "message": message,
        }

    @api.post("/v1/auth/devices/trust")
    def auth_trust_device(
        req: AuthTrustDeviceRequest,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        if not session.get("deviceBound") or not session.get("deviceIdHash"):
            raise HTTPException(status_code=400, detail="Current session is not bound to a device")
        provider = (req.attestationProvider or "account_session").strip().lower()
        attestation_subject = (req.attestationSubject or "").strip()
        attestation_subject_hash = (
            hashlib.sha256(attestation_subject.encode("utf-8")).hexdigest()
            if attestation_subject
            else None
        )
        attestation_verified = False
        evidence_payload = {**(req.evidence or {}), "verificationMode": "account_confirmed_not_platform_verified"}
        if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS | DEVICE_ATTESTATION_PUBLIC_KEY_PROVIDERS:
            if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS and not _device_attestation_secret():
                raise HTTPException(status_code=503, detail="Device attestation verifier is not configured")
            if provider in DEVICE_ATTESTATION_PUBLIC_KEY_PROVIDERS:
                if not attestation_subject:
                    raise HTTPException(status_code=400, detail="attestationSubject is required for public-key attestation")
                public_jwk = _device_attestation_public_key_jwk(attestation_subject, req.evidence or {})
                if not public_jwk:
                    raise HTTPException(status_code=400, detail="publicKeyJwk or attestationSubject JWK is required for public-key attestation")
                attestation_subject_hash = _public_jwk_thumbprint(public_jwk)
            elif not attestation_subject:
                raise HTTPException(status_code=400, detail="attestationSubject is required for signed challenge attestation")
            raw_evidence = req.evidence or {}
            challenge_id = str(raw_evidence.get("challengeId") or "").strip()
            challenge = str(raw_evidence.get("challenge") or "").strip()
            signature = str(raw_evidence.get("signature") or "").strip()
            default_algorithm = (
                "hmac-sha256"
                if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS
                else "webauthn-es256"
                if provider in DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS
                else "rs256"
            )
            algorithm = str(raw_evidence.get("algorithm") or default_algorithm).strip().lower()
            if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS and algorithm != "hmac-sha256":
                raise HTTPException(status_code=400, detail="Unsupported device attestation signature algorithm")
            if provider == "public_key_challenge" and algorithm != "rs256":
                raise HTTPException(status_code=400, detail="Unsupported device attestation signature algorithm")
            if provider in DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS and algorithm not in {"webauthn-es256", "es256"}:
                raise HTTPException(status_code=400, detail="Unsupported device attestation signature algorithm")
            if provider in DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS and not (
                raw_evidence.get("clientDataJSON") or raw_evidence.get("client_data_json")
            ):
                raise HTTPException(status_code=400, detail="WebAuthn evidence requires clientDataJSON")
            if provider in DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS and not (
                raw_evidence.get("authenticatorData") or raw_evidence.get("authenticator_data")
            ):
                raise HTTPException(status_code=400, detail="WebAuthn evidence requires authenticatorData")
            if not challenge_id or not challenge or not signature:
                raise HTTPException(status_code=400, detail="Signed challenge evidence requires challengeId, challenge, and signature")
            challenge_hash = _device_attestation_challenge_hash(challenge)
            challenge_record = store.consume_account_device_attestation_challenge(
                account_id=session["accountId"],
                device_id_hash=session["deviceIdHash"],
                provider=provider,
                challenge_id=challenge_id,
                challenge_hash=challenge_hash,
            )
            if not challenge_record:
                store.audit_log(
                    "auth_device_attestation_failed",
                    actor="account_auth",
                    target_type="device",
                    target_id=session["deviceIdHash"][:16],
                    payload={"accountId": session["accountId"], "provider": provider, "reason": "missing_expired_or_replayed_challenge"},
                )
                raise HTTPException(status_code=401, detail="Invalid device attestation challenge")
            message = _device_attestation_message(provider, challenge_id, challenge, attestation_subject)
            signature_valid = False
            if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS:
                secret = _device_attestation_secret()
                expected = _device_attestation_hmac_signature(secret or "", provider, challenge_id, challenge, attestation_subject)
                signature_valid = hmac.compare_digest(expected, signature.lower())
                verification_metadata: Dict[str, Any] = {}
            elif provider in DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS:
                signature_valid, verification_metadata, failure_reason = _verify_webauthn_es256_assertion(
                    challenge,
                    signature,
                    public_jwk,
                    raw_evidence,
                )
                if not signature_valid:
                    store.audit_log(
                        "auth_device_attestation_failed",
                        actor="account_auth",
                        target_type="device",
                        target_id=session["deviceIdHash"][:16],
                        payload={
                            "accountId": session["accountId"],
                            "provider": provider,
                            "challengeId": challenge_id,
                            "reason": failure_reason,
                            **verification_metadata,
                        },
                    )
                    raise HTTPException(status_code=401, detail="Invalid WebAuthn device attestation")
            else:
                signature_valid = _verify_rs256_with_jwk(message, signature, public_jwk)
                verification_metadata = {}
            if not signature_valid:
                store.audit_log(
                    "auth_device_attestation_failed",
                    actor="account_auth",
                    target_type="device",
                    target_id=session["deviceIdHash"][:16],
                    payload={"accountId": session["accountId"], "provider": provider, "challengeId": challenge_id, "reason": "bad_signature"},
                )
                raise HTTPException(status_code=401, detail="Invalid device attestation signature")
            attestation_verified = True
            evidence_payload = {
                key: value
                for key, value in raw_evidence.items()
                if key
                not in {
                    "challenge",
                    "signature",
                    "publicKeyJwk",
                    "public_key_jwk",
                    "clientDataJSON",
                    "client_data_json",
                    "authenticatorData",
                    "authenticator_data",
                }
            }
            verification_mode = (
                "signed_challenge_hmac"
                if provider in DEVICE_ATTESTATION_HMAC_PROVIDERS
                else "webauthn_assertion_es256"
                if provider in DEVICE_ATTESTATION_WEBAUTHN_PROVIDERS
                else "public_key_challenge_rs256"
            )
            evidence_payload.update(
                {
                    "algorithm": algorithm,
                    "challengeId": challenge_id,
                    "challengeHash": challenge_hash,
                    "verificationMode": verification_mode,
                    **verification_metadata,
                }
            )
            if provider in DEVICE_ATTESTATION_PUBLIC_KEY_PROVIDERS:
                evidence_payload["publicKeyThumbprint"] = attestation_subject_hash
        device = store.mark_account_device_trusted(
            account_id=session["accountId"],
            device_id_hash=session["deviceIdHash"],
            label=req.deviceLabel or session.get("deviceLabel"),
            platform=req.platform,
            attestation_provider=provider,
            attestation_subject_hash=attestation_subject_hash,
            attestation_verified=attestation_verified,
            evidence=evidence_payload,
        )
        if not device:
            raise HTTPException(status_code=409, detail="Device has been revoked")
        store.audit_log(
            "auth_device_trusted",
            actor="account_auth",
            target_type="device",
            target_id=device["id"],
            payload={
                "accountId": session["accountId"],
                "attestationProvider": device.get("attestationProvider"),
                "attestationVerified": device.get("attestationVerified"),
                "verificationMode": _public_device(device).get("verificationMode"),
            },
        )
        return {"ok": True, "device": _public_device(device)}

    @api.delete("/v1/auth/devices/{deviceId}")
    def auth_revoke_device(
        deviceId: str,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        device = store.revoke_account_device(session["accountId"], deviceId)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        store.audit_log(
            "auth_device_revoked",
            actor="account_auth",
            target_type="device",
            target_id=deviceId,
            payload={
                "accountId": session["accountId"],
                "selfRevoked": device.get("deviceIdHash") == session.get("deviceIdHash"),
                "revokedSessionCount": device.get("revokedSessionCount", 0),
            },
        )
        return {
            "ok": True,
            "revokedDeviceId": deviceId,
            "revokedSessionCount": device.get("revokedSessionCount", 0),
            "device": _public_device(device),
        }

    @api.delete("/v1/auth/sessions/{sessionId}")
    def auth_revoke_session(
        sessionId: str,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        revoked = store.revoke_account_session(session["accountId"], sessionId)
        if not revoked:
            raise HTTPException(status_code=404, detail="Session not found")
        store.audit_log(
            "auth_session_revoked",
            actor="account_auth",
            target_type="session",
            target_id=sessionId,
            payload={"accountId": session["accountId"], "selfRevoked": sessionId == session["id"]},
        )
        return {"ok": True, "revokedSessionId": sessionId, "selfRevoked": sessionId == session["id"]}

    @api.post("/v1/auth/logout-all")
    def auth_logout_all(
        keepCurrent: bool = False,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        revoked_count = store.revoke_account_sessions(
            session["accountId"],
            except_session_id=session["id"] if keepCurrent else None,
        )
        store.audit_log(
            "auth_all_sessions_revoked",
            actor="account_auth",
            target_type="account",
            target_id=session["accountId"],
            payload={"keepCurrent": keepCurrent, "revokedCount": revoked_count},
        )
        return {"ok": True, "revokedCount": revoked_count, "currentSessionKept": keepCurrent}

    @api.post("/v1/auth/change-password")
    def auth_change_password(
        req: AuthChangePasswordRequest,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        account = store.get_account_by_id(session["accountId"], include_password_hash=True)
        if not account or not _verify_password(req.currentPassword, account.get("passwordHash", "")):
            store.audit_log(
                "auth_password_change_failed",
                actor="account_auth",
                target_type="account",
                target_id=session["accountId"],
            )
            raise HTTPException(status_code=401, detail="Invalid current password")
        if not store.update_account_password(account["id"], _hash_password(req.newPassword)):
            raise HTTPException(status_code=409, detail="Account is not active")
        store.revoke_account_sessions(account["id"])
        refreshed_account = store.get_account_by_id(account["id"]) or account
        tokens = _issue_account_tokens(store, refreshed_account, req.deviceLabel or session.get("deviceLabel"), req.deviceId)
        store.audit_log("auth_password_changed", actor="account_auth", target_type="account", target_id=account["id"])
        return {"account": _public_account(refreshed_account), **tokens}

    @api.delete("/v1/auth/account")
    def auth_delete_account(
        req: AuthDeleteAccountRequest,
        session: Dict[str, Any] = Depends(get_account_session),
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        account = store.get_account_by_id(session["accountId"], include_password_hash=True)
        password_ok = bool(req.password and account and _verify_password(req.password, account.get("passwordHash", "")))
        oidc_confirmation_ok = bool(account and account.get("identityProvider") and req.confirmation == "delete-my-account")
        if not account or not (password_ok or oidc_confirmation_ok):
            store.audit_log(
                "auth_account_delete_failed",
                actor="account_auth",
                target_type="account",
                target_id=session["accountId"],
            )
            raise HTTPException(status_code=401, detail="Password or OIDC deletion confirmation required")
        privacy = store.delete_learner_data(actor="account_self_service", learner_id=session["learnerId"])
        disabled = store.disable_account(account["id"])
        store.audit_log(
            "auth_account_deleted",
            actor="account_auth",
            target_type="account",
            target_id=account["id"],
            payload={"learnerHash": hashlib.sha256(session["learnerId"].encode("utf-8")).hexdigest()[:16]},
        )
        return {"ok": bool(disabled), "accountDisabled": bool(disabled), "privacyDeletion": privacy}

    @api.post("/v1/conversations")
    def create_conversation(
        req: CreateConversationRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        persona = store.get_persona(req.personaId)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        room = store.get_practice_room(req.practiceRoomId)
        if not room:
            raise HTTPException(status_code=404, detail="Practice room not found")
        conversation = store.create_conversation(req.personaId, req.practiceRoomId, req.mode, learner_id=learner_id)
        store.track_event(
            "conversation_started",
            learner_id=learner_id,
            session_id=conversation["id"],
            payload={"personaId": req.personaId, "practiceRoomId": req.practiceRoomId, "mode": req.mode},
        )
        return {"conversationId": conversation["id"], "learnerId": learner_id, "persona": persona, "practiceRoom": room}

    @api.post("/v1/conversations/{conversationId}/turns")
    def create_turn(
        conversationId: str,
        req: CreateTurnRequest,
        store: ApiStore = Depends(get_store),
        stt: MockSTTProvider = Depends(get_stt),
        tts: MockTTSProvider = Depends(get_tts),
        llm: MockLLMProvider = Depends(get_llm),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        conversation_id = conversationId
        conversation = store.get_conversation(conversation_id)
        if not conversation or conversation["learnerId"] != learner_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        persona = store.get_persona(conversation["personaId"])
        room = store.get_practice_room(conversation["practiceRoomId"])
        if not persona or not room:
            raise HTTPException(status_code=404, detail="Conversation seed not found")

        stt_usage = {"sttSeconds": 0.0}
        if req.inputType in {"audio", "mock_audio"}:
            transcript = stt.transcribe({"audioBase64": req.audioBase64, "mockText": req.text, "language": "ja"})
            user_text = transcript["text"]
            stt_usage = {"sttSeconds": transcript["sttSeconds"]}
        else:
            user_text = req.text or room["primaryPhraseKo"]

        user_message = store.add_message(conversation_id, "user", user_text, req.inputType)
        llm_turn = llm.generate_turn(persona, room, user_text)

        audio_url = None
        tts_usage = {"ttsCharacters": 0, "ttsSeconds": 0.0, "cacheHit": False}
        if req.requestTts:
            tts_response = synthesize_tts_internal(
                TtsRequest(text=llm_turn["spokenText"], personaId=persona["id"], language="ja"),
                store=store,
                tts=tts,
                conversation=conversation,
                learner_id=learner_id,
            )
            audio_url = tts_response["audioUrl"]
            tts_usage = {
                "ttsCharacters": len(llm_turn["spokenText"]),
                "ttsSeconds": round((tts_response.get("durationMs") or 0) / 1000, 2),
                "cacheHit": bool(tts_response["cacheHit"]),
            }

        review_cards = []
        for card in llm_turn["reviewCards"]:
            review_cards.append(store.save_review_card(card, conversation_id=conversation_id, learner_id=learner_id))

        usage = {
            "llmInputTokens": llm_turn["usage"]["llmInputTokens"],
            "llmOutputTokens": llm_turn["usage"]["llmOutputTokens"],
            "sttSeconds": stt_usage["sttSeconds"],
            "ttsCharacters": tts_usage["ttsCharacters"],
            "ttsSeconds": tts_usage["ttsSeconds"],
            "cacheHit": tts_usage["cacheHit"],
        }
        store.record_usage(
            usage,
            conversation_id=conversation_id,
            practice_room_id=conversation["practiceRoomId"],
            persona_id=conversation["personaId"],
            provider={"llm": llm.provider, "stt": stt.provider, "tts": tts.provider},
            learner_id=learner_id,
        )
        store.add_message(
            conversation_id,
            "assistant",
            llm_turn["assistantText"],
            metadata={
                "spokenText": llm_turn["spokenText"],
                "reviewCardIds": [card["id"] for card in review_cards],
                "safety": llm_turn["safety"],
                "corrections": llm_turn["corrections"],
            },
        )
        store.track_event(
            "practice_turn_completed",
            learner_id=learner_id,
            session_id=conversation_id,
            payload={"practiceRoomId": conversation["practiceRoomId"], "reviewCardsCreated": len(review_cards)},
        )
        store.record_xp_event(
            learner_id=learner_id,
            source="practice_turn_completed",
            points=10,
            payload={"practiceRoomId": conversation["practiceRoomId"], "conversationId": conversation_id},
            idempotency_key=f"practice_turn_completed:{user_message['id']}",
        )
        if review_cards:
            store.track_event(
                "review_card_created",
                learner_id=learner_id,
                session_id=conversation_id,
                payload={"reviewCardIds": [card["id"] for card in review_cards]},
            )
            for card in review_cards:
                store.record_xp_event(
                    learner_id=learner_id,
                    source="review_card_created",
                    points=5,
                    payload={"reviewCardId": card["id"], "conversationId": conversation_id},
                    idempotency_key=f"review_card_created:{card['id']}",
                )
        pronunciation = None
        if req.inputType in {"audio", "mock_audio"}:
            pronunciation = get_pronunciation().score(llm_turn["spokenText"], user_text, audio_base64=req.audioBase64)
            store.track_event(
                "pronunciation_scored",
                learner_id=learner_id,
                session_id=conversation_id,
                payload={
                    "score": pronunciation["score"],
                    "rating": pronunciation["rating"],
                    "scoringMode": pronunciation.get("scoringMode"),
                    "acousticEvidencePresent": pronunciation.get("acousticEvidencePresent"),
                },
            )
            store.record_xp_event(
                learner_id=learner_id,
                source="pronunciation_scored",
                points=5,
                payload={"score": pronunciation["score"], "conversationId": conversation_id},
                idempotency_key=f"pronunciation_scored:{user_message['id']}",
            )

        response = {
            "conversationId": conversation_id,
            "learnerId": learner_id,
            "userText": user_text,
            "assistantText": llm_turn["assistantText"],
            "spokenText": llm_turn["spokenText"],
            "suggestedUserReply": llm_turn["suggestedUserReply"],
            "audioUrl": audio_url,
            "corrections": llm_turn["corrections"],
            "reviewCards": review_cards,
            "usage": usage,
        }
        if pronunciation:
            response["pronunciation"] = pronunciation
        return response

    @api.get("/v1/voices")
    def list_voices() -> list[Dict[str, Any]]:
        return load_voice_catalog()

    @api.get("/v1/voices/samples/{voiceId}.wav")
    def voice_sample(voiceId: str) -> Response:
        voice_id = _safe_path_segment(voiceId, "voice identifier")
        voices = {str(voice.get("voiceId")): voice for voice in load_voice_catalog()}
        voice = voices.get(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
        catalog_voice_id = _safe_path_segment(str(voice.get("voiceId") or ""), "voice identifier")
        sample_file = _resolve_contained_path(
            PROJECT_ROOT / "artifacts" / "voices" / "catalog_samples",
            f"{catalog_voice_id}.wav",
        )
        if sample_file.is_file():
            return Response(content=sample_file.read_bytes(), media_type="audio/wav")
        sample = MockTTSProvider().synthesize(
            {
                "text": "こんにちは。今日も一緒に話しましょう。",
                "personaId": voice.get("personaId") or "yui",
                "language": "ja",
                "speed": 0.95,
                "emotion": "default",
            }
        )
        return Response(content=base64.b64decode(sample["audioBase64"]), media_type="audio/wav")

    @api.post("/v1/tts/synthesize")
    def synthesize_tts(
        req: TtsRequest,
        store: ApiStore = Depends(get_store),
        tts: MockTTSProvider = Depends(get_tts),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return synthesize_tts_internal(req, store=store, tts=tts, learner_id=learner_id)

    @api.post("/v1/stt/transcribe")
    async def transcribe_stt(
        request: Request,
        store: ApiStore = Depends(get_store),
        stt: MockSTTProvider = Depends(get_stt),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        req_payload = await _stt_payload_from_request(request)
        result = stt.transcribe(req_payload)
        store.record_usage(
            {"sttSeconds": result.get("sttSeconds") or 0},
            provider={"stt": stt.provider},
            learner_id=learner_id,
        )
        return {
            "text": result["text"],
            "provider": result["provider"],
            "confidence": result["confidence"],
            "latencyMs": int(result.get("latencyMs") or 0),
        }

    @api.post("/v1/dialogue/match")
    def match_dialogue(req: DialogueMatchRequest) -> Dict[str, Any]:
        return api.state.dialogue_matcher.match(
            persona_id=req.personaId,
            pack_version=req.packVersion,
            utterance=req.utterance,
            candidate_line_ids=req.candidateLineIds,
            global_intents=req.globalIntents,
        )

    @api.get("/v1/dialogue/packs")
    def dialogue_packs() -> list[Dict[str, Any]]:
        return list_dialogue_packs()

    @api.get("/v1/dialogue/packs/{personaId}/{packVersion}.zip")
    def dialogue_pack_zip(personaId: str, packVersion: str) -> Response:
        persona_id = _safe_path_segment(personaId, "persona identifier")
        pack_version = _safe_path_segment(packVersion, "pack version")
        pack = next(
            (
                item
                for item in list_dialogue_packs()
                if item.get("personaId") == persona_id and item.get("packVersion") == pack_version
            ),
            None,
        )
        if not pack:
            raise HTTPException(status_code=404, detail="Dialogue pack not found")
        catalog_persona_id = _safe_path_segment(str(pack["personaId"]), "persona identifier")
        catalog_pack_version = _safe_path_segment(str(pack["packVersion"]), "pack version")
        version_dir = _resolve_contained_path(DIALOGUE_PACKS_ROOT, catalog_persona_id, catalog_pack_version)
        if not version_dir.exists() or not version_dir.is_dir():
            raise HTTPException(status_code=404, detail="Dialogue pack not found")
        prebuilt_zip = _resolve_contained_path(version_dir, "pack.zip")
        if prebuilt_zip.is_file():
            return Response(content=prebuilt_zip.read_bytes(), media_type="application/zip")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(item for item in version_dir.rglob("*") if item.is_file() and item.name != "pack.zip"):
                relative_path = path.relative_to(version_dir)
                contained_path = _resolve_contained_path(version_dir, *relative_path.parts)
                archive.write(contained_path, contained_path.relative_to(version_dir))
        return Response(content=buffer.getvalue(), media_type="application/zip")

    @api.post("/v1/dialogue/unmatched", status_code=202)
    def log_dialogue_unmatched(
        req: DialogueUnmatchedRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        record = store.log_dialogue_unmatched(
            persona_id=req.personaId,
            pack_version=req.packVersion,
            node_id=req.nodeId,
            utterance=req.utterance,
            stt_confidence=req.sttConfidence,
            learner_id=learner_id,
        )
        return {"accepted": True, "id": record["id"]}

    @api.get("/v1/review-cards")
    def list_review_cards(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return {"reviewCards": store.list_review_cards(learner_id=learner_id)}

    @api.get("/v1/review-cards/due")
    def list_due_review_cards(
        limit: int = 20,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return {"reviewCards": store.list_due_review_cards(limit=limit, learner_id=learner_id)}

    @api.post("/v1/review-cards")
    def create_review_card(
        card: ReviewCardRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        saved = store.save_review_card(dump_model(card), learner_id=learner_id)
        store.track_event("review_card_created", learner_id=learner_id, payload={"reviewCardIds": [saved["id"]], "source": "manual"})
        return {"reviewCard": saved}

    @api.post("/v1/review-cards/{reviewCardId}/grade")
    def grade_review_card(
        reviewCardId: str,
        req: ReviewGradeRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        card = store.grade_review_card(reviewCardId, req.quality, learner_id=learner_id)
        if not card:
            raise HTTPException(status_code=404, detail="Review card not found")
        return {"reviewCard": card}

    @api.get("/v1/progress/today")
    def get_today_progress(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.progress_today(learner_id=learner_id)

    @api.get("/v1/gamification/me")
    def get_gamification_summary(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.gamification_summary(learner_id=learner_id)

    @api.get("/v1/reputation/me")
    def get_my_reputation(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.learner_reputation_profile(learner_id=learner_id)

    @api.get("/v1/friends")
    def get_friends(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.friends_summary(learner_id=learner_id)

    @api.get("/v1/friends/recommendations")
    def get_friend_recommendations(
        limit: int = 10,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.friend_recommendations(learner_id=learner_id, limit=limit)

    @api.get("/v1/social/discovery")
    def get_social_discovery(
        limit: int = 10,
        targetLanguage: Optional[str] = None,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.social_discovery(learner_id=learner_id, limit=limit, target_language=targetLanguage)

    @api.get("/v1/social/settings")
    def get_social_settings(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.social_settings(learner_id=learner_id)

    @api.put("/v1/social/settings")
    def update_social_settings(
        req: SocialSettingsRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.update_social_settings(
            learner_id=learner_id,
            discoverable=req.discoverable,
            allow_friend_invites=req.allowFriendInvites,
            show_weekly_xp=req.showWeeklyXp,
        )

    @api.get("/v1/social/blocks")
    def get_social_blocks(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.list_social_blocks(learner_id=learner_id)

    @api.post("/v1/social/blocks/{blockedLearnerId}")
    def block_social_learner(
        blockedLearnerId: str,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        result = store.block_learner(learner_id=learner_id, blocked_learner_id=blockedLearnerId)
        if result["reason"] == "cannot_block_self":
            raise HTTPException(status_code=400, detail="Cannot block self")
        return result

    @api.delete("/v1/social/blocks/{blockedLearnerId}")
    def unblock_social_learner(
        blockedLearnerId: str,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.unblock_learner(learner_id=learner_id, blocked_learner_id=blockedLearnerId)

    @api.post("/v1/friends/invites")
    def create_friend_invite(
        req: FriendInviteRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        result = store.create_friend_invite(
            learner_id=learner_id,
            friend_learner_id=req.friendLearnerId,
            message=req.message,
        )
        if result["reason"] == "cannot_invite_self":
            raise HTTPException(status_code=400, detail="Cannot invite self")
        if result["reason"] in {"blocked", "invite_not_allowed"}:
            raise HTTPException(status_code=409, detail={"reason": result["reason"]})
        return result

    @api.post("/v1/friends/invites/{inviteId}/accept")
    def accept_friend_invite(
        inviteId: str,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        result = store.accept_friend_invite(learner_id=learner_id, invite_id=inviteId)
        if result is None:
            raise HTTPException(status_code=404, detail="Friend invite not found")
        return result

    @api.delete("/v1/friends/{friendLearnerId}")
    def remove_friend(
        friendLearnerId: str,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        result = store.remove_friend(learner_id=learner_id, friend_learner_id=friendLearnerId)
        if result is None:
            raise HTTPException(status_code=404, detail="Friend relationship not found")
        return result

    @api.get("/v1/friends/quests")
    def get_friend_quests(
        partnerLearnerId: Optional[str] = None,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.list_friend_quests(learner_id=learner_id, partner_learner_id=partnerLearnerId)

    @api.post("/v1/friends/quests/{questId}/claim")
    def claim_friend_quest_reward(
        questId: str,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        result = store.claim_friend_quest_reward(learner_id=learner_id, quest_id=questId)
        if result is None:
            raise HTTPException(status_code=404, detail="Friend quest not found")
        if not result["claimed"]:
            raise HTTPException(status_code=409, detail={"reason": "friend_quest_not_completed", "quest": result["quest"]})
        return result

    @api.get("/v1/rewards/inventory")
    def get_reward_inventory(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.reward_inventory_summary(learner_id=learner_id)

    @api.get("/v1/rewards/shop")
    def get_reward_shop(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.reward_shop(learner_id=learner_id)

    @api.get("/v1/admin/rewards/shop")
    def list_admin_reward_shop(
        request: Request,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "editor"})
        return store.list_admin_reward_shop_items()

    @api.put("/v1/admin/rewards/shop/{rewardKey}")
    def upsert_admin_reward_shop_item(
        rewardKey: str,
        req: RewardShopItemUpdateRequest,
        request: Request,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"editor"})
        try:
            item = store.upsert_reward_shop_item(
                reward_key=rewardKey,
                price_currency=req.priceCurrency,
                price_amount=req.priceAmount,
                available=req.available,
                daily_purchase_limit=req.dailyPurchaseLimit,
                inventory_limit=req.inventoryLimit,
                starts_at=req.startsAt,
                ends_at=req.endsAt,
                sort_order=req.sortOrder,
                updated_by=context["actor"],
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        store.audit_log(
            "reward_shop_item_updated",
            actor=context["actor"],
            target_type="reward_shop_item",
            target_id=rewardKey,
            payload={"item": item},
        )
        return {"item": item, "updated": True}

    @api.post("/v1/rewards/shop/{rewardKey}/purchase")
    def purchase_reward(
        rewardKey: str,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        result = store.purchase_reward(learner_id=learner_id, reward_key=rewardKey)
        if result is None:
            raise HTTPException(status_code=404, detail="Reward not found")
        if not result["purchased"]:
            raise HTTPException(status_code=409, detail={"reason": result["reason"], "shop": result["shop"]})
        return result

    @api.post("/v1/rewards/boosts/{rewardKey}/activate")
    def activate_xp_boost(
        rewardKey: str,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        result = store.activate_xp_boost(learner_id=learner_id, reward_key=rewardKey)
        if result is None:
            raise HTTPException(status_code=404, detail="Reward not found")
        if not result["activated"]:
            raise HTTPException(status_code=409, detail={"reason": "reward_not_available", "inventory": result["inventory"]})
        return result

    @api.get("/v1/achievements/me")
    def get_achievements_summary(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        store.refresh_achievement_awards(learner_id=learner_id)
        return store.achievements_summary(learner_id=learner_id)

    @api.get("/v1/leagues/me")
    def get_league_status(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.league_status(learner_id=learner_id)

    @api.get("/v1/leaderboards/weekly")
    def get_weekly_leaderboard(
        limit: int = 20,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.weekly_leaderboard(learner_id=learner_id, limit=limit)

    @api.get("/v1/admin/xp-abuse-flags")
    def list_admin_xp_abuse_flags(
        request: Request,
        learnerId: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "reviewer"})
        flags = store.list_xp_abuse_flags(
            learner_id=normalize_learner_id(learnerId) if learnerId else None,
            status=status,
            limit=limit,
        )
        return {"flags": flags, "count": len(flags)}

    @api.post("/v1/admin/xp-abuse-flags/{flagId}/status")
    def update_xp_abuse_flag_status(
        flagId: str,
        req: XpAbuseFlagReviewRequest,
        request: Request,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        context = require_admin_role(request, {"reviewer"})
        try:
            flag = store.review_xp_abuse_flag(
                flag_id=flagId,
                status=req.status,
                reviewer=context["actor"],
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if flag is None:
            raise HTTPException(status_code=404, detail="XP abuse flag not found")
        store.audit_log(
            "xp_abuse_flag_reviewed",
            actor=context["actor"],
            target_type="xp_abuse_flag",
            target_id=flagId,
            payload={"status": req.status, "notePresent": bool(req.note), "learnerIdHash": audit_subject_hash(flag["learnerId"])},
        )
        return {"ok": True, "flag": flag}

    @api.get("/v1/admin/reputation/learners")
    def list_admin_reputation_learners(
        request: Request,
        band: Optional[str] = None,
        limit: int = 100,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "reviewer"})
        try:
            return store.list_reputation_profiles(band=band, limit=limit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.get("/v1/admin/reputation/learners/{learnerId}")
    def get_admin_reputation_learner(
        learnerId: str,
        request: Request,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        require_admin_role(request, {"viewer", "reviewer"})
        return store.learner_reputation_profile(learner_id=learnerId)

    @api.get("/v1/entitlements/me")
    def entitlements() -> Dict[str, Any]:
        return {
            "plan": "master_sandbox",
            "voiceMinutesPerMonth": "unlimited_for_master_sandbox",
            "maxPersonas": "unlimited",
            "customPersona": True,
            "reviewCardsLimit": "unlimited",
            "premiumVoices": True,
        }

    @api.get("/v1/profile/me")
    def get_profile(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return {"profile": store.get_profile(learner_id=learner_id)}

    @api.put("/v1/profile/me")
    def update_profile(
        req: ProfileRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return {"profile": store.update_profile({k: v for k, v in dump_model(req).items() if v is not None}, learner_id=learner_id)}

    @api.get("/v1/recommendations/today")
    def get_recommendations_today(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.recommendations_today(learner_id=learner_id)

    @api.get("/v1/memory/summary")
    def get_memory_summary(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.memory_summary(learner_id=learner_id)

    @api.post("/v1/pronunciation/score")
    def score_pronunciation(
        req: PronunciationScoreRequest,
        scorer: MockPronunciationScorer = Depends(get_pronunciation),
    ) -> Dict[str, Any]:
        return scorer.score(req.expectedText, req.actualText, audio_base64=req.audioBase64)

    @api.get("/v1/export/anki")
    def export_anki(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["front", "back", "example", "tags", "dueAt", "reviewCount", "easeFactor"])
        for card in store.list_review_cards(learner_id=learner_id):
            writer.writerow(
                [
                    card["front"],
                    card["back"],
                    card.get("example") or "",
                    ",".join(card.get("tags") or []),
                    card.get("dueAt") or "",
                    card.get("reviewCount") or 0,
                    card.get("easeFactor") or 2.5,
                ]
            )
        return {"format": "csv", "filename": "ai_language_partner_review_cards.csv", "content": buffer.getvalue()}

    @api.get("/v1/export/anki-apkg")
    def export_anki_apkg(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        cards = store.list_review_cards(learner_id=learner_id)
        deck = genanki.Deck(2059400110, "AI Language Partner")
        model = genanki.Model(
            1607392319,
            "AI Language Partner Basic",
            fields=[{"name": "Front"}, {"name": "Back"}, {"name": "Example"}],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=\"answer\">{{Back}}<br><br><small>{{Example}}</small>",
                }
            ],
        )
        for card in cards:
            deck.add_note(
                genanki.Note(
                    model=model,
                    fields=[card["front"], card["back"], card.get("example") or ""],
                    tags=["ai_language_partner"] + [_anki_tag(tag) for tag in card.get("tags") or []],
                )
            )
        with tempfile.NamedTemporaryFile(suffix=".apkg") as handle:
            genanki.Package(deck).write_to_file(handle.name)
            handle.seek(0)
            content_base64 = base64.b64encode(handle.read()).decode("ascii")
        return {
            "format": "apkg",
            "filename": "ai_language_partner_review_cards.apkg",
            "contentBase64": content_base64,
            "noteCount": len(cards),
        }

    @api.post("/v1/export/anki-connect")
    def export_anki_connect(
        req: AnkiConnectExportRequest,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        notes = [_review_card_to_anki_note(card, req.deckName, req.modelName) for card in store.list_review_cards(learner_id=learner_id)]
        if not req.apply:
            return {"ok": True, "dryRun": True, "notes": notes, "count": len(notes)}
        payload = {"action": "addNotes", "version": 6, "params": {"notes": notes}}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        local_url = _local_anki_connect_url(req.ankiConnectUrl)
        try:
            data = _post_to_local_anki_connect(local_url, body)
        except Exception:
            raise HTTPException(status_code=502, detail="AnkiConnect export failed") from None
        if not isinstance(data, dict):
            raise HTTPException(status_code=502, detail="AnkiConnect export failed")
        return {"ok": data.get("error") is None, "dryRun": False, "count": len(notes), "ankiConnect": data}

    @api.get("/v1/grammar/jlpt")
    def list_jlpt_grammar(level: Optional[str] = None, tag: Optional[str] = None, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        return {"grammarPoints": store.list_grammar_points(level=level, tag=tag)}

    @api.get("/v1/mistakes/korean-patterns")
    def list_korean_mistake_patterns(
        category: Optional[str] = None,
        tag: Optional[str] = None,
        store: ApiStore = Depends(get_store),
    ) -> Dict[str, Any]:
        return {"mistakePatterns": store.list_korean_mistake_patterns(category=category, tag=tag)}

    @api.get("/v1/weaknesses/summary")
    def weakness_summary(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return store.weakness_summary(learner_id=learner_id)

    @api.get("/v1/providers/status")
    def provider_status(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        usage = store.usage_summary(learner_id=learner_id)
        llm_status = api.state.llm.describe()
        tts_status = api.state.tts.describe()
        stt_status = api.state.stt.describe()
        pronunciation_status = api.state.pronunciation.describe()
        dialogue_status = api.state.dialogue_matcher.describe()
        tts_status["cacheEntries"] = usage["ttsCacheEntries"]
        enterprise_sso_connections = store.list_enterprise_sso_connections(include_disabled=False)
        return {
            "mode": "mock_open_core" if not any(
                status.get("externalConfigured") for status in [llm_status, tts_status, stt_status, pronunciation_status]
            ) else "hybrid_provider_adapters",
            "externalApiKeysRequired": False,
            "providers": {
                "llm": llm_status,
                "tts": tts_status,
                "stt": stt_status,
                "pronunciation": pronunciation_status,
                "dialogue": dialogue_status,
            },
            "openCoreBoundary": {
                "publicCore": [
                    "mock providers",
                    "SRS scheduler",
                    "review card export",
                    "usage logging",
                    "provider adapters",
                    "acoustic pronunciation adapter",
                    "rate limiting",
                    "audit logging",
                    "privacy deletion",
                    "account device registry and trust lifecycle",
                    "enterprise SSO connection discovery and PKCE handoff",
                    "content versioned publishing",
                    "content translation memory",
                    "content bulk QA",
                    "content branching assignments",
                    "content managed scheduler runs",
                    "experiment stable assignment and exposure logging",
                    "experiment variant analytics and decision readiness guard",
                    "experiment statistical testing",
                    "XP ledger, streaks, daily quests, friend graph, invites, recommendations, social discovery, social privacy/blocking, friend quests, reward currency ledger, operated reward shop, reward inventory, XP boosts, achievements, league tiers, anomaly flags, multi-signal reputation review, and weekly leaderboard",
                ],
                "privateMoat": ["premium voices", "voice embeddings", "advanced correction prompts", "production learner analytics"],
            },
            "operations": {
                "dialogue": dialogue_status,
                "auth": {
                    "mode": _auth_mode(),
                    "tokenVersion": "v2_expiring_hmac",
                    "legacyTokensAllowed": _legacy_tokens_allowed(),
                    "accountSessionAuth": True,
                    "passwordAuth": True,
                    "passwordChange": True,
                    "accountDeletionRequiresPassword": True,
                    "optionalDeviceBinding": True,
                    "deviceRegistry": True,
                    "deviceTrustLifecycle": True,
                    "trustedDeviceEnrollment": True,
                    "deviceRevokeRevokesSessions": True,
                    "platformAttestationVerification": _platform_attestation_verification_status(),
                    "deviceAttestationChallenge": True,
                    "deviceAttestationProviders": sorted(
                        (DEVICE_ATTESTATION_HMAC_PROVIDERS if _device_attestation_secret() else set())
                        | DEVICE_ATTESTATION_PUBLIC_KEY_PROVIDERS
                    ),
                    "hmacDeviceAttestationChallenge": bool(_device_attestation_secret()),
                    "publicKeyDeviceAttestationChallenge": True,
                    "publicKeyDeviceAttestationVerification": "public_key_challenge_rs256",
                    "webauthnDeviceAttestationChallenge": True,
                    "webauthnDeviceAttestationVerification": "webauthn_assertion_es256",
                    "webauthnRpId": _webauthn_rp_id(),
                    "webauthnAllowedOrigins": sorted(_webauthn_allowed_origins()),
                    "webauthnUserPresenceRequired": True,
                    "deviceAttestationChallengeTtlSeconds": _device_attestation_challenge_ttl_seconds(),
                    "loginFailureThrottle": True,
                    "registrationThrottle": True,
                    "passwordSprayRiskControl": True,
                    "riskBasedAbuseControls": True,
                    "sessionInventory": True,
                    "remoteSessionRevoke": True,
                    "logoutAllSessions": True,
                    "refreshReuseDetection": True,
                    "accessTokenFormat": "jwt_hs256",
                    "jwtIssuer": _jwt_issuer(),
                    "jwtAudience": _jwt_audience(),
                    "jwtSigningSecretConfigured": bool(os.environ.get("AI_LANGUAGE_PARTNER_JWT_SECRET") or os.environ.get("AI_LANGUAGE_PARTNER_AUTH_SECRET")),
                    "legacyOpaqueAccessTokensAccepted": True,
                    "oauth": bool(_oauth_pkce_configured_providers()),
                    "oidcFederation": True,
                    "oidcAllowedProviders": _oidc_allowed_providers(),
                    "oidcIdTokenVerification": "hs256_rs256_jwks",
                    "oidcEmailVerifiedRequired": _oidc_require_email_verified(),
                    "oidcJwksVerification": _oidc_any_jwks_configured(),
                    "oidcJwksConfiguredProviders": [
                        provider for provider in _oidc_allowed_providers() if _oidc_jwks_configured(provider)
                    ],
                    "oauthAuthorizationCodePkce": True,
                    "oauthPkceS256Only": True,
                    "oauthPkceStateStoredHashed": True,
                    "oauthPkceOneTimeState": True,
                    "oauthPkceConfiguredProviders": _oauth_pkce_configured_providers(),
                    "oauthPkceTokenExchangeConfiguredProviders": _oauth_token_exchange_configured_providers(),
                    "oauthPkceLocalSignedCodeAllowed": _oauth_local_signed_code_allowed(),
                    "enterpriseSso": True,
                    "enterpriseSsoDomainDiscovery": True,
                    "enterpriseSsoAuthorizationCodePkce": True,
                    "enterpriseSsoConnectionCount": len(enterprise_sso_connections),
                    "enterpriseSsoConfiguredProviders": sorted({connection["provider"] for connection in enterprise_sso_connections}),
                    "jwtAccessTokens": True,
                    "fullAccountAuth": False,
                },
                "rateLimit": api.state.rate_limiter.describe(),
                "rateLimitPerMinute": api.state.rate_limiter.describe()["limitPerMinute"],
                "content": {
                    "authoringValidation": True,
                    "importDryRun": True,
                    "versionSnapshots": True,
                    "roleBasedReview": True,
                    "approvalRequiredForPublish": True,
                    "publishFromSnapshot": True,
                    "versionedPublishing": True,
                    "translationMemory": True,
                    "bulkQa": True,
                    "branchingAssignments": True,
                    "operationJobs": True,
                    "operationJobRunner": True,
                    "managedScheduler": True,
                    "schedulerRunHistory": True,
                    "adminOpsConsole": True,
                    "adminActionConsole": True,
                    "adminContentConsole": True,
                    "releasePlans": True,
                    "releaseScheduling": True,
                    "canaryReleaseMetadata": True,
                    "releaseWorker": True,
                    "releaseRollback": True,
                },
                "experiments": {
                    "stableAssignments": True,
                    "weightedVariants": True,
                    "exposureLogging": True,
                    "conversionEventLogging": True,
                    "adminExperimentControls": True,
                    "analyticsDashboard": True,
                    "variantAnalytics": True,
                    "decisionConsole": True,
                    "decisionActionConsole": True,
                    "decisionReadinessGuard": True,
                    "statisticalTesting": True,
                    "decisionWorkflow": True,
                    "decisionGuardrails": True,
                    "winnerRolloutApplication": True,
                },
                "learnerModel": {
                    "currentRecallEstimator": "hlr_inspired_local_estimator_v1",
                    "offlineTrainEvaluatePipeline": True,
                    "offlineModelName": OFFLINE_LEARNER_MEMORY_MODEL_NAME,
                    "usesLiveProductionModelForScheduling": False,
                    "productionTrainedModel": False,
                },
                "gamification": {
                    "xpLedger": True,
                    "streaks": True,
                    "dailyQuests": True,
                    "weeklyLeaderboard": True,
                    "antiDuplicateXpEvents": True,
                    "achievements": True,
                    "achievementLevels": True,
                    "achievementRewardCurrency": True,
                    "leagueTiers": True,
                    "xpAnomalyFlags": True,
                    "friendQuests": True,
                    "friendGraph": True,
                    "friendInvites": True,
                    "friendRecommendations": True,
                    "socialDiscovery": True,
                    "socialPrivacySettings": True,
                    "socialBlocking": True,
                    "rewardCurrencyLedger": True,
                    "rewardShop": True,
                    "rewardShopOperations": True,
                    "rewardShopPurchaseLimits": True,
                    "rewardInventory": True,
                    "xpBoosts": True,
                    "boostedXpLedger": True,
                    "singleSourceAnomalyFlags": True,
                    "boostAbuseFlags": True,
                    "duplicatePayloadAbuseFlags": True,
                    "leaderboardExclusionFlags": True,
                    "xpAbuseReviewQueue": True,
                    "multiSignalReputation": True,
                    "reputationReviewQueue": True,
                    "offlineReputationModelEvaluation": True,
                    "offlineReputationModelName": OFFLINE_REPUTATION_MODEL_NAME,
                    "productionLearnedAntiCheatModel": False,
                },
                "auditLogging": True,
                "privacyDeletion": True,
            },
        }

    @api.get("/v1/admin/ops-console", response_class=HTMLResponse)
    def admin_ops_console(request: Request, store: ApiStore = Depends(get_store)) -> HTMLResponse:
        context = require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        quality = _content_quality_report(store.list_courses(), store.list_practice_rooms(), store.list_personas())
        releases = store.list_content_releases(limit=8)
        jobs = store.list_content_operation_jobs(limit=8)
        scheduler_runs = store.list_content_scheduler_runs(limit=8)
        versions = store.list_content_versions(limit=8)
        experiments = store.list_experiments(limit=8)
        audit_logs = store.list_audit_logs(limit=200)

        def esc(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            return html.escape(str(value), quote=True)

        def json_text(value: Any) -> str:
            return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)

        def status_badge(value: Any) -> str:
            status = str(value or "unknown")
            normalized = status.replace("_", "-").lower()
            tone = "neutral"
            if normalized in {"succeeded", "applied", "published", "running"}:
                tone = "good"
            elif normalized in {"queued", "planned", "scheduled", "draft", "in-review"}:
                tone = "watch"
            elif normalized in {"failed", "canceled", "rolled-back", "archived", "rejected"}:
                tone = "bad"
            return f'<span class="badge badge-{tone}">{esc(status)}</span>'

        def table(headers: list[str], rows: list[list[str]], empty: str) -> str:
            header_html = "".join(f"<th>{esc(header)}</th>" for header in headers)
            if not rows:
                return f'<table><thead><tr>{header_html}</tr></thead><tbody><tr><td colspan="{len(headers)}" class="muted">{esc(empty)}</td></tr></tbody></table>'
            body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
            return f"<table><thead><tr>{header_html}</tr></thead><tbody>{body}</tbody></table>"

        release_rows = [
            [
                status_badge(release["status"]),
                esc(release["title"]),
                esc(release["releaseStrategy"]),
                f'{int(release["rolloutPercent"])}%',
                esc(release.get("scheduledAt") or release.get("createdAt")),
                esc(release.get("appliedAt") or release.get("rolledBackAt") or ""),
            ]
            for release in releases
        ]
        job_rows = [
            [
                status_badge(job["status"]),
                esc(job["jobType"]),
                esc(job["priority"]),
                esc(job.get("createdBy")),
                esc(job.get("claimedBy") or job.get("canceledBy") or ""),
                esc(job.get("updatedAt")),
            ]
            for job in jobs
        ]
        scheduler_rows = [
            [
                status_badge(run["status"]),
                esc(run["leaseOwner"]),
                esc(run["result"].get("releaseWorker", {}).get("appliedCount", 0)),
                esc(run["result"].get("operationJobsRunCount", 0)),
                esc(run.get("startedAt")),
                esc(run.get("completedAt") or ""),
            ]
            for run in scheduler_runs
        ]
        experiment_rows = [
            [
                status_badge(experiment["status"]),
                esc(experiment["key"]),
                esc(experiment["name"]),
                esc(len(experiment.get("variants", []))),
                esc(experiment.get("allocation")),
                esc(experiment.get("updatedAt")),
            ]
            for experiment in experiments
        ]
        audit_rows = [
            [
                esc(entry["action"]),
                esc(entry.get("actor")),
                esc(entry.get("targetType")),
                esc(entry.get("targetId")),
                esc(entry.get("createdAt")),
            ]
            for entry in audit_logs
        ]
        release_options = "".join(
            f'<option value="{esc(release["id"])}">{esc(release["status"])} · {esc(release["title"])}</option>'
            for release in releases
        ) or '<option value="">No releases</option>'
        approved_version_options = "".join(
            f'<option value="{esc(version["id"])}">{esc(version["status"])} · {esc(version.get("label") or version["id"])}</option>'
            for version in versions
            if version["status"] in {"approved", "published"}
        ) or '<option value="">No approved versions</option>'
        counts = quality["counts"]
        generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        quality_status = "valid" if quality["valid"] else "needs review"
        latest_scheduler = scheduler_runs[0]["status"] if scheduler_runs else "none"
        html_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Language Partner Ops Console</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17201d;
      --muted: #60746d;
      --line: #d8dfdc;
      --paper: #fbfbf7;
      --panel: #ffffff;
      --green: #1f7a5d;
      --blue: #2f5f98;
      --amber: #b4661c;
      --red: #a33a32;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Aptos", "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 28px clamp(18px, 4vw, 44px) 20px;
    }}
    main {{
      padding: 22px clamp(18px, 4vw, 44px) 40px;
      display: grid;
      gap: 18px;
    }}
    h1, h2 {{ margin: 0; font-weight: 700; letter-spacing: 0; }}
    h1 {{ font-size: 30px; }}
    h2 {{ font-size: 16px; }}
    .topline {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      align-items: end;
      justify-content: space-between;
    }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }}
    .metric, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric {{ padding: 14px 16px; min-height: 76px; }}
    .metric b {{ display: block; font-size: 22px; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    section {{ overflow: hidden; }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #f7f9f8;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid #edf1ef;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: 0; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 18px;
    }}
    .badge {{
      display: inline-flex;
      min-width: 72px;
      justify-content: center;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid transparent;
    }}
    .badge-good {{ color: var(--green); background: #e8f4ee; border-color: #b7ddce; }}
    .badge-watch {{ color: var(--amber); background: #fff2df; border-color: #edc995; }}
    .badge-bad {{ color: var(--red); background: #fdeceb; border-color: #e5b6b1; }}
    .badge-neutral {{ color: var(--blue); background: #eaf1fa; border-color: #bed0e6; }}
    .muted {{ color: var(--muted); }}
    .actions {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      padding: 14px 16px 16px;
    }}
    .action-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      display: grid;
      gap: 8px;
      align-content: start;
      background: #fff;
    }}
    label {{ display: grid; gap: 4px; color: var(--muted); font-size: 12px; }}
    input, select, button {{
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      padding: 7px 9px;
    }}
    button {{
      cursor: pointer;
      border-color: #1f5f55;
      background: #1f5f55;
      color: #fff;
      font-weight: 700;
    }}
    button.secondary {{ background: #2f5f98; border-color: #2f5f98; }}
    button.warning {{ background: #a33a32; border-color: #a33a32; }}
    .auth-strip {{
      display: grid;
      grid-template-columns: minmax(190px, 1fr) minmax(120px, .5fr) minmax(150px, .7fr);
      gap: 10px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfb;
    }}
    pre {{
      margin: 0;
      padding: 12px 16px 16px;
      max-height: 260px;
      overflow: auto;
      border-top: 1px solid var(--line);
      background: #101816;
      color: #d8f0e8;
      font-size: 12px;
      white-space: pre-wrap;
    }}
    @media (max-width: 760px) {{
      h1 {{ font-size: 24px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .auth-strip {{ grid-template-columns: 1fr; }}
      table {{ table-layout: auto; }}
      th, td {{ padding: 9px 10px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topline">
      <div>
        <h1>Ops Console</h1>
        <div class="meta">{esc(PROJECT_ID)} / role {esc(context["role"])} / actor {esc(context["actor"])}</div>
      </div>
      <div class="meta">generated {esc(generated_at)}</div>
    </div>
  </header>
  <main>
    <div class="metrics">
      <div class="metric"><b>{status_badge(quality_status)}</b><span>content quality</span></div>
      <div class="metric"><b>{esc(counts["courses"])}</b><span>courses</span></div>
      <div class="metric"><b>{esc(counts["practiceRooms"])}</b><span>practice rooms</span></div>
      <div class="metric"><b>{esc(sum(1 for item in jobs if item["status"] == "queued"))}</b><span>queued jobs in view</span></div>
      <div class="metric"><b>{status_badge(latest_scheduler)}</b><span>latest scheduler run</span></div>
      <div class="metric"><b>{esc(sum(1 for item in experiments if item["status"] == "running"))}</b><span>running experiments in view</span></div>
    </div>
    <section>
      <div class="section-head"><h2>Action Console</h2><span class="meta">publisher/editor operations</span></div>
      <div class="auth-strip">
        <label>Admin key<input id="opsAdminKey" type="password" autocomplete="off" value=""></label>
        <label>Role<select id="opsAdminRole"><option value="publisher">publisher</option><option value="editor">editor</option><option value="reviewer">reviewer</option><option value="viewer">viewer</option></select></label>
        <label>Actor<input id="opsAdminUser" value="{esc(context["actor"])}"></label>
      </div>
      <div class="actions">
        <form class="action-panel" data-method="POST" data-path="/v1/content/releases/run-due" data-payload='{{"confirmation":"run-due-content-releases","limit":10}}'>
          <h2>Run Due Releases</h2>
          <button type="submit">Run worker</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/scheduler/run-once" data-payload='{{"confirmation":"run-content-scheduler-once","schedulerKey":"content_ops","leaseOwner":"ops-console","maxOperationJobs":1,"releaseLimit":10}}'>
          <h2>Run Scheduler</h2>
          <button class="secondary" type="submit">Run tick</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/operations/jobs/run-next" data-payload='{{"confirmation":"run-next-content-operation-job"}}'>
          <h2>Run Next Job</h2>
          <button class="secondary" type="submit">Claim job</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/releases/__releaseId__/apply" data-payload='{{"confirmation":"apply-content-release","force":true,"note":"ops console apply"}}'>
          <h2>Apply Release</h2>
          <label>Release<select name="releaseId">{release_options}</select></label>
          <button type="submit">Apply</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/releases/__releaseId__/rollback" data-payload='{{"confirmation":"rollback-content-release","note":"ops console rollback"}}'>
          <h2>Rollback Release</h2>
          <label>Release<select name="releaseId">{release_options}</select></label>
          <button class="warning" type="submit">Rollback</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/releases" data-payload='{{"releaseStrategy":"canary","rolloutPercent":25,"catalogScope":"incremental","note":"ops console planned release"}}'>
          <h2>Plan Canary</h2>
          <label>Version<select name="versionId">{approved_version_options}</select></label>
          <label>Title<input name="title" value="Ops console canary"></label>
          <button type="submit">Plan release</button>
        </form>
      </div>
      <pre id="opsActionResult">{{"ok":true,"message":"ready"}}</pre>
    </section>
    <div class="grid">
      <section><div class="section-head"><h2>Content Releases</h2><span class="meta">latest 8</span></div>{table(["Status", "Title", "Strategy", "Rollout", "Scheduled", "Finalized"], release_rows, "No releases found")}</section>
      <section><div class="section-head"><h2>Operation Jobs</h2><span class="meta">priority order</span></div>{table(["Status", "Type", "Priority", "Created By", "Worker", "Updated"], job_rows, "No jobs found")}</section>
      <section><div class="section-head"><h2>Scheduler Runs</h2><span class="meta">latest 8</span></div>{table(["Status", "Lease Owner", "Releases", "Jobs", "Started", "Completed"], scheduler_rows, "No scheduler runs found")}</section>
      <section><div class="section-head"><h2>Experiments</h2><span class="meta">latest 8</span></div>{table(["Status", "Key", "Name", "Variants", "Allocation", "Updated"], experiment_rows, "No experiments found")}</section>
    </div>
    <section><div class="section-head"><h2>Audit Trail</h2><span class="meta">latest 200</span></div>{table(["Action", "Actor", "Target Type", "Target ID", "Created"], audit_rows, "No audit events found")}</section>
  </main>
  <script>
    const resultEl = document.getElementById("opsActionResult");
    const headerValue = (id) => document.getElementById(id).value.trim();
    const renderResult = (payload) => {{
      resultEl.textContent = JSON.stringify(payload, null, 2);
    }};
    const submitAction = async (event) => {{
      event.preventDefault();
      const form = event.currentTarget;
      const formData = new FormData(form);
      let path = form.dataset.path || "";
      for (const [key, value] of formData.entries()) {{
        path = path.replace(`__${{key}}__`, encodeURIComponent(String(value)));
      }}
      const payload = JSON.parse(form.dataset.payload || "{{}}");
      for (const [key, value] of formData.entries()) {{
        if (!path.includes(`__${{key}}__`)) {{
          payload[key] = value;
        }}
      }}
      try {{
        const response = await fetch(path, {{
          method: form.dataset.method || "POST",
          headers: {{
            "Content-Type": "application/json",
            "X-Admin-Key": headerValue("opsAdminKey"),
            "X-Admin-Role": headerValue("opsAdminRole"),
            "X-Admin-User": headerValue("opsAdminUser") || "ops-console",
          }},
          body: JSON.stringify(payload),
        }});
        const text = await response.text();
        let body = text;
        try {{ body = JSON.parse(text); }} catch (error) {{}}
        renderResult({{status: response.status, ok: response.ok, body}});
      }} catch (error) {{
        renderResult({{ok: false, error: String(error)}});
      }}
    }};
    document.querySelectorAll(".action-panel").forEach((form) => form.addEventListener("submit", submitAction));
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_page)

    @api.get("/v1/admin/content-console", response_class=HTMLResponse)
    def admin_content_console(request: Request, store: ApiStore = Depends(get_store)) -> HTMLResponse:
        context = require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        courses = store.list_courses()
        practice_rooms = store.list_practice_rooms()
        quality = _content_quality_report(courses, practice_rooms, store.list_personas())
        versions = store.list_content_versions(limit=12)
        assignments = store.list_content_assignments(limit=12)
        translation_memory = store.list_translation_memory(limit=12)
        audit_logs = store.list_audit_logs(limit=200)
        qa_audit_logs = [entry for entry in audit_logs if entry.get("action") == "content_bulk_qa_completed"][:8]

        def esc(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            return html.escape(str(value), quote=True)

        def json_text(value: Any) -> str:
            return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)

        def status_badge(value: Any) -> str:
            status = str(value or "unknown")
            normalized = status.replace("_", "-").lower()
            tone = "neutral"
            if normalized in {"valid", "succeeded", "published", "approved", "done"}:
                tone = "good"
            elif normalized in {"draft", "todo", "in-progress", "queued", "in-review", "needs-review"}:
                tone = "watch"
            elif normalized in {"invalid", "failed", "blocked", "rejected"}:
                tone = "bad"
            return f'<span class="badge badge-{tone}">{esc(status)}</span>'

        def table(headers: list[str], rows: list[list[str]], empty: str) -> str:
            header_html = "".join(f"<th>{esc(header)}</th>" for header in headers)
            if not rows:
                return f'<table><thead><tr>{header_html}</tr></thead><tbody><tr><td colspan="{len(headers)}" class="muted">{esc(empty)}</td></tr></tbody></table>'
            body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
            return f"<table><thead><tr>{header_html}</tr></thead><tbody>{body}</tbody></table>"

        def version_label(version: Dict[str, Any]) -> str:
            return f"{version.get('status', 'unknown')} · {version.get('label') or version.get('id')}"

        sample_courses = courses[:1]
        sample_room_ids = {
            room_id
            for course in sample_courses
            for unit in course.get("units") or []
            for lesson in unit.get("lessons") or []
            for room_id in lesson.get("practiceRoomIds") or []
        }
        sample_rooms = [room for room in practice_rooms if room.get("id") in sample_room_ids] or practice_rooms[:1]
        sample_bundle = {"courses": sample_courses, "practiceRooms": sample_rooms}
        import_sample = {**sample_bundle, "dryRun": True, "replaceExisting": True}
        selected_version_id = versions[0]["id"] if versions else ""
        sample_room = practice_rooms[0] if practice_rooms else {}
        tm_source_text = sample_room.get("primaryPhraseKo") or "새로운 표현 테스트"
        validate_sample = json_text(sample_bundle)
        import_sample_text = json_text(import_sample)
        bulk_qa_sample = json_text({"versionId": selected_version_id, "useCurrent": not bool(selected_version_id), "includeTranslationMemory": True})
        tm_suggest_sample = json_text({"sourceText": tm_source_text, "sourceLanguage": "ko", "targetLanguage": "ja", "limit": 5})
        tm_upsert_sample = json_text(
            {
                "entries": [
                    {
                        "sourceText": "콘텐츠 콘솔 샘플 표현",
                        "targetText": "コンテンツコンソールのサンプル表現",
                        "sourceLanguage": "ko",
                        "targetLanguage": "ja",
                        "sourceRef": "content-console:manual",
                        "tags": ["console", "cms"],
                        "quality": 95,
                    }
                ]
            }
        )
        branch_sample = json_text(
            {
                "label": "Content console copy branch",
                "branchName": "content-console-copy",
                "assignee": "writer-a",
                "priority": "normal",
                "note": "copy and QA pass",
            }
        )
        assign_sample = json_text(
            {
                "assignee": "writer-a",
                "priority": "normal",
                "status": "todo",
                "note": "assigned from content console",
            }
        )
        version_options = "".join(
            f'<option value="{esc(version["id"])}">{esc(version_label(version))}</option>'
            for version in versions
        ) or '<option value="">No versions</option>'
        counts = quality["counts"]
        version_rows = [
            [
                status_badge(version.get("status")),
                esc(version.get("label") or version.get("id")),
                esc(version.get("source")),
                esc(version.get("snapshotCounts", {}).get("courses", 0)),
                esc(version.get("snapshotCounts", {}).get("practiceRooms", 0)),
                esc(version.get("createdBy")),
                esc(version.get("updatedAt") or version.get("createdAt")),
            ]
            for version in versions
        ]
        assignment_rows = [
            [
                status_badge(assignment.get("status")),
                esc(assignment.get("assignee")),
                esc(assignment.get("priority")),
                esc(assignment.get("versionId")),
                esc(assignment.get("dueAt")),
                esc(assignment.get("updatedBy") or assignment.get("createdBy")),
            ]
            for assignment in assignments
        ]
        translation_rows = [
            [
                esc(entry.get("sourceText")),
                esc(entry.get("targetText")),
                esc(entry.get("sourceRef")),
                esc(entry.get("quality")),
                esc(", ".join(entry.get("tags") or [])),
            ]
            for entry in translation_memory
        ]
        qa_rows = [
            [
                status_badge("valid" if (entry.get("payload") or {}).get("valid") else "needs review"),
                esc((entry.get("payload") or {}).get("source") or entry.get("targetId")),
                esc((entry.get("payload") or {}).get("issueCount")),
                esc((entry.get("payload") or {}).get("counts", {})),
                esc(entry.get("actor")),
                esc(entry.get("createdAt")),
            ]
            for entry in qa_audit_logs
        ]
        issue_rows = [
            [esc(issue.get("code")), esc(issue.get("pointer")), esc(issue.get("message"))]
            for issue in quality["errors"][:12]
        ]
        generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        quality_status = "valid" if quality["valid"] else "needs review"
        active_assignments = sum(1 for assignment in assignments if assignment.get("status") in {"todo", "in_progress", "blocked"})
        html_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Language Partner Content Console</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17201d;
      --muted: #60746d;
      --line: #d8dfdc;
      --paper: #fbfbf7;
      --panel: #ffffff;
      --green: #1f7a5d;
      --blue: #2f5f98;
      --amber: #b4661c;
      --red: #a33a32;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Aptos", "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 28px clamp(18px, 4vw, 44px) 20px;
    }}
    main {{
      padding: 22px clamp(18px, 4vw, 44px) 40px;
      display: grid;
      gap: 18px;
    }}
    h1, h2 {{ margin: 0; font-weight: 700; letter-spacing: 0; }}
    h1 {{ font-size: 30px; }}
    h2 {{ font-size: 16px; }}
    .topline {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      align-items: end;
      justify-content: space-between;
    }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }}
    .metric, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric {{ padding: 14px 16px; min-height: 76px; }}
    .metric b {{ display: block; font-size: 22px; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    section {{ overflow: hidden; }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #f7f9f8;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid #edf1ef;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: 0; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 18px;
    }}
    .badge {{
      display: inline-flex;
      min-width: 72px;
      justify-content: center;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid transparent;
    }}
    .badge-good {{ color: var(--green); background: #e8f4ee; border-color: #b7ddce; }}
    .badge-watch {{ color: var(--amber); background: #fff2df; border-color: #edc995; }}
    .badge-bad {{ color: var(--red); background: #fdeceb; border-color: #e5b6b1; }}
    .badge-neutral {{ color: var(--blue); background: #eaf1fa; border-color: #bed0e6; }}
    .muted {{ color: var(--muted); }}
    .actions {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
      padding: 14px 16px 16px;
    }}
    .action-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      display: grid;
      gap: 8px;
      align-content: start;
      background: #fff;
    }}
    label {{ display: grid; gap: 4px; color: var(--muted); font-size: 12px; }}
    input, select, textarea, button {{
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      padding: 7px 9px;
    }}
    textarea {{
      min-height: 150px;
      resize: vertical;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 12px;
      line-height: 1.42;
      white-space: pre;
    }}
    button {{
      cursor: pointer;
      border-color: #1f5f55;
      background: #1f5f55;
      color: #fff;
      font-weight: 700;
    }}
    button.secondary {{ background: #2f5f98; border-color: #2f5f98; }}
    .auth-strip {{
      display: grid;
      grid-template-columns: minmax(190px, 1fr) minmax(120px, .5fr) minmax(150px, .7fr);
      gap: 10px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfb;
    }}
    pre {{
      margin: 0;
      padding: 12px 16px 16px;
      max-height: 300px;
      overflow: auto;
      border-top: 1px solid var(--line);
      background: #101816;
      color: #d8f0e8;
      font-size: 12px;
      white-space: pre-wrap;
    }}
    @media (max-width: 760px) {{
      h1 {{ font-size: 24px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .auth-strip {{ grid-template-columns: 1fr; }}
      table {{ table-layout: auto; }}
      th, td {{ padding: 9px 10px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topline">
      <div>
        <h1>Content Console</h1>
        <div class="meta">{esc(PROJECT_ID)} / role {esc(context["role"])} / actor {esc(context["actor"])}</div>
      </div>
      <div class="meta">generated {esc(generated_at)}</div>
    </div>
  </header>
  <main>
    <div class="metrics">
      <div class="metric"><b>{status_badge(quality_status)}</b><span>catalog quality</span></div>
      <div class="metric"><b>{esc(counts["courses"])}</b><span>courses</span></div>
      <div class="metric"><b>{esc(counts["practiceRooms"])}</b><span>practice rooms</span></div>
      <div class="metric"><b>{esc(len(versions))}</b><span>versions in view</span></div>
      <div class="metric"><b>{esc(active_assignments)}</b><span>active assignments in view</span></div>
      <div class="metric"><b>{esc(len(translation_memory))}</b><span>translation memory samples</span></div>
    </div>
    <section>
      <div class="section-head"><h2>Authoring Action Console</h2><span class="meta">existing content JSON APIs</span></div>
      <div class="auth-strip">
        <label>Admin key<input id="contentAdminKey" type="password" autocomplete="off" value=""></label>
        <label>Role<select id="contentAdminRole"><option value="editor">editor</option><option value="reviewer">reviewer</option><option value="publisher">publisher</option><option value="viewer">viewer</option></select></label>
        <label>Actor<input id="contentAdminUser" value="{esc(context["actor"])}"></label>
      </div>
      <div class="actions">
        <form class="action-panel" data-method="POST" data-path="/v1/content/validate">
          <h2>Validate Bundle</h2>
          <textarea name="payload">{esc(validate_sample)}</textarea>
          <button type="submit">Validate</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/import">
          <h2>Import Dry Run</h2>
          <textarea name="payload">{esc(import_sample_text)}</textarea>
          <button type="submit">Import dry run</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/bulk-qa">
          <h2>Bulk QA</h2>
          <textarea name="payload">{esc(bulk_qa_sample)}</textarea>
          <button class="secondary" type="submit">Run QA</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/translation-memory/suggest">
          <h2>TM Suggest</h2>
          <textarea name="payload">{esc(tm_suggest_sample)}</textarea>
          <button class="secondary" type="submit">Suggest</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/translation-memory">
          <h2>TM Upsert</h2>
          <textarea name="payload">{esc(tm_upsert_sample)}</textarea>
          <button type="submit">Upsert</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/versions/__versionId__/branch">
          <h2>Branch Version</h2>
          <label>Version<select name="versionId">{version_options}</select></label>
          <textarea name="payload">{esc(branch_sample)}</textarea>
          <button type="submit">Branch</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/content/versions/__versionId__/assign">
          <h2>Assign Version</h2>
          <label>Version<select name="versionId">{version_options}</select></label>
          <textarea name="payload">{esc(assign_sample)}</textarea>
          <button type="submit">Assign</button>
        </form>
      </div>
      <pre id="contentConsoleResult">{{"ok":true,"message":"ready"}}</pre>
    </section>
    <div class="grid">
      <section><div class="section-head"><h2>Versions</h2><span class="meta">latest 12</span></div>{table(["Status", "Label", "Source", "Courses", "Rooms", "Actor", "Updated"], version_rows, "No content versions found")}</section>
      <section><div class="section-head"><h2>Assignments</h2><span class="meta">latest 12</span></div>{table(["Status", "Assignee", "Priority", "Version", "Due", "Updated By"], assignment_rows, "No assignments found")}</section>
      <section><div class="section-head"><h2>Translation Memory</h2><span class="meta">latest samples</span></div>{table(["Source", "Target", "Ref", "Quality", "Tags"], translation_rows, "No translation memory entries found")}</section>
      <section><div class="section-head"><h2>Bulk QA Runs</h2><span class="meta">latest audit events</span></div>{table(["Status", "Source", "Issues", "Counts", "Actor", "Created"], qa_rows, "No bulk QA audit events found")}</section>
    </div>
    <section><div class="section-head"><h2>Current Quality Issues</h2><span class="meta">first 12 validation errors</span></div>{table(["Code", "Pointer", "Message"], issue_rows, "No current validation errors")}</section>
  </main>
  <script>
    const resultEl = document.getElementById("contentConsoleResult");
    const headerValue = (id) => document.getElementById(id).value.trim();
    const renderResult = (payload) => {{
      resultEl.textContent = JSON.stringify(payload, null, 2);
    }};
    const submitAction = async (event) => {{
      event.preventDefault();
      const form = event.currentTarget;
      const formData = new FormData(form);
      let path = form.dataset.path || "";
      let payload = {{}};
      const payloadText = form.querySelector("textarea[name='payload']")?.value.trim();
      if (payloadText) {{
        payload = JSON.parse(payloadText);
      }}
      for (const [key, value] of formData.entries()) {{
        if (key === "payload") {{
          continue;
        }}
        const token = `__${{key}}__`;
        if (path.includes(token)) {{
          path = path.replace(token, encodeURIComponent(String(value)));
        }} else if (String(value).trim()) {{
          payload[key] = value;
        }}
      }}
      try {{
        const response = await fetch(path, {{
          method: form.dataset.method || "POST",
          headers: {{
            "Content-Type": "application/json",
            "X-Admin-Key": headerValue("contentAdminKey"),
            "X-Admin-Role": headerValue("contentAdminRole"),
            "X-Admin-User": headerValue("contentAdminUser") || "content-console",
          }},
          body: JSON.stringify(payload),
        }});
        const text = await response.text();
        let body = text;
        try {{ body = JSON.parse(text); }} catch (error) {{}}
        renderResult({{status: response.status, ok: response.ok, body}});
      }} catch (error) {{
        renderResult({{ok: false, error: String(error)}});
      }}
    }};
    document.querySelectorAll(".action-panel").forEach((form) => form.addEventListener("submit", submitAction));
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_page)

    @api.get("/v1/admin/experiment-console", response_class=HTMLResponse)
    def admin_experiment_console(
        request: Request,
        experimentKey: Optional[str] = None,
        minimumExposedLearners: int = 30,
        store: ApiStore = Depends(get_store),
    ) -> HTMLResponse:
        context = require_admin_role(request, {"viewer", "editor", "reviewer", "publisher"})
        experiments = store.list_experiments(limit=100)
        selected_key = normalize_experiment_key(experimentKey) if experimentKey else (experiments[0]["key"] if experiments else None)
        analytics = store.experiment_analytics(selected_key, minimum_exposed_learners=minimumExposedLearners) if selected_key else None
        if selected_key and not analytics:
            raise HTTPException(status_code=404, detail="Experiment not found")
        decisions = store.list_experiment_decisions(selected_key, limit=20) if selected_key else []
        preview_plan: Optional[Dict[str, Any]] = None
        preview_guardrail: Optional[Dict[str, Any]] = None
        if analytics:
            preview_payload = {
                "action": "auto",
                "minimumExposedLearners": analytics["minimumExposedLearners"],
                "requireDecisionReady": True,
                "requireStatisticalSignificance": True,
            }
            preview_plan = _experiment_decision_plan(preview_payload, analytics)
            preview_guardrail = _experiment_decision_guardrail(
                preview_payload,
                analytics,
                preview_plan["action"],
                preview_plan["variantKey"],
            )
            store.audit_log(
                "experiment_console_viewed",
                actor=context["actor"],
                target_type="experiment",
                target_id=analytics["experiment"]["key"],
                payload={
                    "minimumExposedLearners": analytics["minimumExposedLearners"],
                    "decisionReady": analytics["decisionReady"],
                    "decisionRecommendation": analytics["decisionRecommendation"],
                    "winnerVariantKey": analytics["winnerVariantKey"],
                    "previewAction": preview_plan["action"],
                    "previewVariantKey": preview_plan["variantKey"],
                    "previewGuardrailOk": preview_guardrail["ok"],
                },
            )
        experiment_audit_logs = [
            entry
            for entry in store.list_audit_logs(limit=200)
            if str(entry.get("action") or "").startswith("experiment_")
            or entry.get("targetType") in {"experiment", "experiment_decision"}
        ]

        def esc(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            return html.escape(str(value), quote=True)

        def json_text(value: Any) -> str:
            return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)

        def status_badge(value: Any) -> str:
            status = str(value or "unknown")
            normalized = status.replace("_", "-").lower()
            tone = "neutral"
            if normalized in {"running", "applied", "eligible", "ready", "promote-winner", "ok"}:
                tone = "good"
            elif normalized in {"draft", "paused", "proposed", "collect-more-data", "no-statistically-significant-winner"}:
                tone = "watch"
            elif normalized in {"archived", "failed", "blocked", "not-ready"}:
                tone = "bad"
            return f'<span class="badge badge-{tone}">{esc(status)}</span>'

        def format_percent(value: Any) -> str:
            if value is None:
                return ""
            try:
                return f"{float(value) * 100:.1f}%"
            except (TypeError, ValueError):
                return esc(value)

        def format_number(value: Any, digits: int = 4) -> str:
            if value is None:
                return ""
            try:
                return f"{float(value):.{digits}f}"
            except (TypeError, ValueError):
                return esc(value)

        def table(headers: list[str], rows: list[list[str]], empty: str) -> str:
            header_html = "".join(f"<th>{esc(header)}</th>" for header in headers)
            if not rows:
                return f'<table><thead><tr>{header_html}</tr></thead><tbody><tr><td colspan="{len(headers)}" class="muted">{esc(empty)}</td></tr></tbody></table>'
            body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
            return f"<table><thead><tr>{header_html}</tr></thead><tbody>{body}</tbody></table>"

        experiment_rows = [
            [
                status_badge(experiment["status"]),
                esc(experiment["key"]),
                esc(experiment["name"]),
                esc(len(experiment.get("variants", []))),
                esc(experiment.get("allocation")),
                esc(experiment.get("updatedAt")),
            ]
            for experiment in experiments
        ]
        variant_rows = [
            [
                esc(variant["variantKey"]),
                esc(variant["assignmentCount"]),
                esc(variant["exposedLearnerCount"]),
                esc(variant["convertedLearnerCount"]),
                format_percent(variant["exposedConversionRate"]),
                format_percent(variant.get("absoluteLiftFromBaseline")),
                format_number(variant.get("pValue")),
                status_badge("eligible" if variant.get("decisionEligible") else "not_ready"),
            ]
            for variant in ((analytics or {}).get("variants") or [])
        ]
        decision_rows = [
            [
                esc(decision["id"]),
                status_badge(decision["status"]),
                esc(decision["action"]),
                esc(decision.get("variantKey")),
                status_badge("ok" if (decision.get("guardrail") or {}).get("ok") else "blocked"),
                esc(decision.get("createdBy")),
                esc(decision.get("createdAt") or decision.get("appliedAt")),
            ]
            for decision in decisions
        ]
        audit_rows = [
            [
                esc(entry["action"]),
                esc(entry.get("actor")),
                esc(entry.get("targetType")),
                esc(entry.get("targetId")),
                esc(entry.get("createdAt")),
            ]
            for entry in experiment_audit_logs[:40]
        ]
        totals = (analytics or {}).get("totals") or {}
        generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        selected_experiment = (analytics or {}).get("experiment") or {}
        preview_action = (preview_plan or {}).get("action")
        preview_variant = (preview_plan or {}).get("variantKey")
        preview_ok = bool((preview_guardrail or {}).get("ok"))
        preview_violations = (preview_guardrail or {}).get("violations") or []
        selected_variants = selected_experiment.get("variants") or [
            {"key": "control", "label": "Control", "weight": 1, "payload": {}},
            {"key": "test", "label": "Test", "weight": 1, "payload": {}},
        ]
        experiment_options = "".join(
            f'<option value="{esc(experiment["key"])}" {"selected" if experiment["key"] == selected_key else ""}>{esc(experiment["status"])} · {esc(experiment["key"])}</option>'
            for experiment in experiments
        ) or '<option value="">No experiments</option>'
        decision_options = "".join(
            f'<option value="{esc(decision["id"])}">{esc(decision["status"])} · {esc(decision["action"])} · {esc(decision.get("variantKey") or "")}</option>'
            for decision in decisions
        ) or '<option value="">No decisions</option>'
        selected_or_sample_key = selected_key or "new_experiment_v1"
        experiment_upsert_sample = json_text(
            {
                "key": selected_or_sample_key,
                "name": selected_experiment.get("name") or "New experiment",
                "status": selected_experiment.get("status") or "draft",
                "variants": selected_variants,
                "allocation": selected_experiment.get("allocation") or {"unit": "learner"},
            }
        )
        status_sample = json_text({"status": selected_experiment.get("status") or "paused"})
        decision_sample = json_text(
            {
                "action": "auto",
                "minimumExposedLearners": (analytics or {}).get("minimumExposedLearners", minimumExposedLearners),
                "requireDecisionReady": True,
                "requireStatisticalSignificance": True,
                "reason": "Experiment console decision proposal",
            }
        )
        decision_apply_sample = json_text({"confirmation": "apply-experiment-decision", "note": "Experiment console apply"})
        html_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Language Partner Experiment Console</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17201d;
      --muted: #60746d;
      --line: #d8dfdc;
      --paper: #fbfbf7;
      --panel: #ffffff;
      --green: #1f7a5d;
      --blue: #2f5f98;
      --amber: #b4661c;
      --red: #a33a32;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Aptos", "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 28px clamp(18px, 4vw, 44px) 20px;
    }}
    main {{
      padding: 22px clamp(18px, 4vw, 44px) 40px;
      display: grid;
      gap: 18px;
    }}
    h1, h2 {{ margin: 0; font-weight: 700; letter-spacing: 0; }}
    h1 {{ font-size: 30px; }}
    h2 {{ font-size: 16px; }}
    .topline {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      align-items: end;
      justify-content: space-between;
    }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }}
    .metric, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric {{ padding: 14px 16px; min-height: 76px; }}
    .metric b {{ display: block; font-size: 22px; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    section {{ overflow: hidden; }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #f7f9f8;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid #edf1ef;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: 0; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 18px;
    }}
    .badge {{
      display: inline-flex;
      min-width: 72px;
      justify-content: center;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid transparent;
    }}
    .badge-good {{ color: var(--green); background: #e8f4ee; border-color: #b7ddce; }}
    .badge-watch {{ color: var(--amber); background: #fff2df; border-color: #edc995; }}
    .badge-bad {{ color: var(--red); background: #fdeceb; border-color: #e5b6b1; }}
    .badge-neutral {{ color: var(--blue); background: #eaf1fa; border-color: #bed0e6; }}
    .muted {{ color: var(--muted); }}
    .mono {{ font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; }}
    .actions {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
      padding: 14px 16px 16px;
    }}
    .action-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      display: grid;
      gap: 8px;
      align-content: start;
      background: #fff;
    }}
    label {{ display: grid; gap: 4px; color: var(--muted); font-size: 12px; }}
    input, select, textarea, button {{
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      padding: 7px 9px;
    }}
    textarea {{
      min-height: 130px;
      resize: vertical;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 12px;
      line-height: 1.42;
      white-space: pre;
    }}
    button {{
      cursor: pointer;
      border-color: #1f5f55;
      background: #1f5f55;
      color: #fff;
      font-weight: 700;
    }}
    button.secondary {{ background: #2f5f98; border-color: #2f5f98; }}
    button.warning {{ background: #a33a32; border-color: #a33a32; }}
    .auth-strip {{
      display: grid;
      grid-template-columns: minmax(190px, 1fr) minmax(120px, .5fr) minmax(150px, .7fr);
      gap: 10px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfb;
    }}
    pre {{
      margin: 0;
      padding: 12px 16px 16px;
      max-height: 300px;
      overflow: auto;
      border-top: 1px solid var(--line);
      background: #101816;
      color: #d8f0e8;
      font-size: 12px;
      white-space: pre-wrap;
    }}
    @media (max-width: 760px) {{
      h1 {{ font-size: 24px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .auth-strip {{ grid-template-columns: 1fr; }}
      table {{ table-layout: auto; }}
      th, td {{ padding: 9px 10px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topline">
      <div>
        <h1>Experiment Console</h1>
        <div class="meta">{esc(PROJECT_ID)} / role {esc(context["role"])} / actor {esc(context["actor"])}</div>
      </div>
      <div class="meta">generated {esc(generated_at)}</div>
    </div>
  </header>
  <main>
    <div class="metrics">
      <div class="metric"><b>{esc(len(experiments))}</b><span>experiments</span></div>
      <div class="metric"><b class="mono">{esc(selected_key)}</b><span>selected experiment</span></div>
      <div class="metric"><b>{status_badge((analytics or {}).get("decisionRecommendation", "none"))}</b><span>recommendation</span></div>
      <div class="metric"><b>{status_badge("ready" if (analytics or {}).get("decisionReady") else "not_ready")}</b><span>decision readiness</span></div>
      <div class="metric"><b class="mono">{esc((analytics or {}).get("winnerVariantKey") or "")}</b><span>winner variant</span></div>
      <div class="metric"><b>{status_badge("ok" if preview_ok else "blocked")}</b><span>auto guardrail preview</span></div>
    </div>
    <section>
      <div class="section-head"><h2>Experiment Action Console</h2><span class="meta">existing experiment JSON APIs</span></div>
      <div class="auth-strip">
        <label>Admin key<input id="experimentAdminKey" type="password" autocomplete="off" value=""></label>
        <label>Role<select id="experimentAdminRole"><option value="editor">editor</option><option value="reviewer">reviewer</option><option value="publisher">publisher</option><option value="viewer">viewer</option></select></label>
        <label>Actor<input id="experimentAdminUser" value="{esc(context["actor"])}"></label>
      </div>
      <div class="actions">
        <form class="action-panel" data-method="POST" data-path="/v1/experiments">
          <h2>Upsert Experiment</h2>
          <textarea name="payload">{esc(experiment_upsert_sample)}</textarea>
          <button type="submit">Upsert</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/experiments/__experimentKey__/status">
          <h2>Update Status</h2>
          <label>Experiment<select name="experimentKey">{experiment_options}</select></label>
          <textarea name="payload">{esc(status_sample)}</textarea>
          <button class="secondary" type="submit">Update</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/experiments/__experimentKey__/decisions">
          <h2>Propose Decision</h2>
          <label>Experiment<select name="experimentKey">{experiment_options}</select></label>
          <textarea name="payload">{esc(decision_sample)}</textarea>
          <button type="submit">Propose</button>
        </form>
        <form class="action-panel" data-method="POST" data-path="/v1/experiments/__experimentKey__/decisions/__decisionId__/apply">
          <h2>Apply Decision</h2>
          <label>Experiment<select name="experimentKey">{experiment_options}</select></label>
          <label>Decision<select name="decisionId">{decision_options}</select></label>
          <textarea name="payload">{esc(decision_apply_sample)}</textarea>
          <button class="warning" type="submit">Apply</button>
        </form>
      </div>
      <pre id="experimentActionResult">{{"ok":true,"message":"ready"}}</pre>
    </section>
    <div class="grid">
      <section><div class="section-head"><h2>Experiments</h2><span class="meta">latest 100</span></div>{table(["Status", "Key", "Name", "Variants", "Allocation", "Updated"], experiment_rows, "No experiments found")}</section>
      <section><div class="section-head"><h2>Decision Readout</h2><span class="meta">{esc(selected_experiment.get("name") or selected_key or "none")}</span></div>{table(["Metric", "Value"], [
        ["Minimum exposed learners", esc((analytics or {}).get("minimumExposedLearners"))],
        ["Assignments", esc(totals.get("assignmentCount", 0))],
        ["Exposed learners", esc(totals.get("exposedLearnerCount", 0))],
        ["Converted learners", esc(totals.get("convertedLearnerCount", 0))],
        ["Best observed variant", esc((analytics or {}).get("bestObservedVariantKey"))],
        ["Auto action preview", esc(preview_action)],
        ["Auto variant preview", esc(preview_variant)],
        ["Guardrail violations", esc(preview_violations)],
      ], "No selected experiment")}</section>
    </div>
    <section><div class="section-head"><h2>Variant Analytics</h2><span class="meta">assignment, exposure, conversion, lift</span></div>{table(["Variant", "Assignments", "Exposed", "Converted", "Conversion", "Lift", "p-value", "Eligible"], variant_rows, "No analytics found")}</section>
    <section><div class="section-head"><h2>Decision History</h2><span class="meta">latest 20</span></div>{table(["Decision ID", "Status", "Action", "Variant", "Guardrail", "Created By", "Created"], decision_rows, "No decisions found")}</section>
    <section><div class="section-head"><h2>Experiment Audit Trail</h2><span class="meta">latest 40</span></div>{table(["Action", "Actor", "Target Type", "Target ID", "Created"], audit_rows, "No experiment audit events found")}</section>
  </main>
  <script>
    const resultEl = document.getElementById("experimentActionResult");
    const headerValue = (id) => document.getElementById(id).value.trim();
    const renderResult = (payload) => {{
      resultEl.textContent = JSON.stringify(payload, null, 2);
    }};
    const submitAction = async (event) => {{
      event.preventDefault();
      const form = event.currentTarget;
      const formData = new FormData(form);
      let path = form.dataset.path || "";
      let payload = {{}};
      const payloadText = form.querySelector("textarea[name='payload']")?.value.trim();
      if (payloadText) {{
        payload = JSON.parse(payloadText);
      }}
      for (const [key, value] of formData.entries()) {{
        if (key === "payload") {{
          continue;
        }}
        const token = `__${{key}}__`;
        if (path.includes(token)) {{
          path = path.replace(token, encodeURIComponent(String(value)));
        }} else if (String(value).trim()) {{
          payload[key] = value;
        }}
      }}
      try {{
        const response = await fetch(path, {{
          method: form.dataset.method || "POST",
          headers: {{
            "Content-Type": "application/json",
            "X-Admin-Key": headerValue("experimentAdminKey"),
            "X-Admin-Role": headerValue("experimentAdminRole"),
            "X-Admin-User": headerValue("experimentAdminUser") || "experiment-console",
          }},
          body: JSON.stringify(payload),
        }});
        const text = await response.text();
        let body = text;
        try {{ body = JSON.parse(text); }} catch (error) {{}}
        renderResult({{status: response.status, ok: response.ok, body}});
      }} catch (error) {{
        renderResult({{ok: false, error: String(error)}});
      }}
    }};
    document.querySelectorAll(".action-panel").forEach((form) => form.addEventListener("submit", submitAction));
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_page)

    @api.get("/v1/usage/summary")
    def usage_summary(
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        return {"usage": store.usage_summary(learner_id=learner_id)}

    @api.get("/v1/audit-log")
    def audit_log(request: Request, limit: int = 50, store: ApiStore = Depends(get_store)) -> Dict[str, Any]:
        require_admin_key(request)
        return {"auditLogs": store.list_audit_logs(limit=limit)}

    @api.delete("/v1/privacy/me")
    def delete_my_data(
        request: Request,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, Any]:
        actor = request.headers.get("X-User-Id") or "anonymous"
        return store.delete_learner_data(actor=actor, learner_id=learner_id)

    @api.post("/v1/events")
    def track_event(
        event: AnalyticsEvent,
        store: ApiStore = Depends(get_store),
        learner_id: str = Depends(get_learner_id),
    ) -> Dict[str, bool]:
        if event.eventName not in ALLOWED_EVENT_NAMES:
            raise HTTPException(status_code=400, detail=f"Unknown analytics event: {event.eventName}")
        store.track_event(event.eventName, learner_id=learner_id, user_id=event.userId, session_id=event.sessionId, payload=event.payload)
        return {"ok": True}

    return api


def synthesize_tts_internal(
    req: TtsRequest,
    store: ApiStore,
    tts: MockTTSProvider,
    conversation: Optional[Dict[str, Any]] = None,
    learner_id: str = "local-dev",
) -> Dict[str, Any]:
    persona = store.get_persona(req.personaId)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    cache_key = tts_cache_key(req.text, req.personaId, req.language, req.speed, req.emotion, provider=tts.provider)
    cached = store.get_tts_cache(cache_key, learner_id=learner_id)
    if cached:
        request_payload = dump_model(req)
        response = {
            "audioUrl": cached["audioUrl"],
            "audioBase64": cached["audioBase64"],
            "provider": tts.provider,
            "cacheHit": True,
            "spokenText": req.text,
            "durationMs": cached["durationMs"],
            "contentType": cached["contentType"],
            "voiceUsed": tts.voice_used_for(request_payload) if hasattr(tts, "voice_used_for") else req.personaId,
        }
    else:
        response = tts.synthesize(dump_model(req))
        content_type = response["audioUrl"].split(":", 1)[1].split(";", 1)[0] if response["audioUrl"].startswith("data:") else "audio/wav"
        store.save_tts_cache(
            cache_key,
            req.text,
            req.personaId,
            req.language,
            req.speed,
            req.emotion,
            response["audioBase64"],
            response["durationMs"],
            content_type=content_type,
            learner_id=learner_id,
        )

    store.record_usage(
        {
            "ttsCharacters": len(req.text),
            "ttsSeconds": round((response.get("durationMs") or 0) / 1000, 2),
            "cacheHit": response["cacheHit"],
        },
        conversation_id=conversation["id"] if conversation else None,
        practice_room_id=conversation["practiceRoomId"] if conversation else None,
        persona_id=req.personaId,
        provider={"tts": tts.provider},
        learner_id=learner_id,
    )
    return {
        "audioUrl": response["audioUrl"],
        "audioBase64": response["audioBase64"],
        "provider": response["provider"],
        "cacheHit": response["cacheHit"],
        "spokenText": response["spokenText"],
        "durationMs": response["durationMs"],
        "contentType": response.get("contentType") or (response["audioUrl"].split(":", 1)[1].split(";", 1)[0] if response["audioUrl"].startswith("data:") else "audio/wav"),
        "voiceUsed": response.get("voiceUsed") or req.personaId,
    }


def _session_from_authorization(request: Request, store: ApiStore, raise_on_invalid: bool = False) -> Optional[Dict[str, Any]]:
    authorization = request.headers.get("Authorization") or ""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        if raise_on_invalid:
            raise HTTPException(status_code=401, detail="Invalid Authorization header")
        return None
    stripped_token = token.strip()
    if "." in stripped_token and not _decode_account_access_jwt(stripped_token):
        if raise_on_invalid:
            raise HTTPException(status_code=401, detail="Invalid or expired account token")
        return None
    session = store.get_session_by_access_hash(
        _token_hash(stripped_token),
        device_id_hash=_device_id_hash(request.headers.get("X-Device-Id")),
    )
    if not session and raise_on_invalid:
        raise HTTPException(status_code=401, detail="Invalid or expired account token")
    return session


def _issue_account_tokens(
    store: ApiStore,
    account: Dict[str, Any],
    device_label: Optional[str],
    device_id: Optional[str] = None,
) -> Dict[str, Any]:
    device_id_hash = _device_id_hash(device_id)
    device_record = None
    if device_id_hash:
        existing_device = store.get_account_device_by_hash(account["id"], device_id_hash)
        if existing_device and existing_device.get("trustStatus") == "revoked":
            raise HTTPException(status_code=403, detail="Device has been revoked")
        device_record = store.upsert_account_device(account["id"], device_id_hash, label=device_label)
    access_expires_at = _future_iso(_access_token_ttl_seconds())
    access_expires_unix = int(time.time()) + _access_token_ttl_seconds()
    access_jti = "at_" + secrets.token_urlsafe(18)
    access_token = _create_account_access_jwt(account, access_expires_unix, access_jti, device_bound=bool(device_id_hash))
    refresh_token = "alp_rt_" + secrets.token_urlsafe(48)
    refresh_expires_at = _future_iso(_refresh_token_ttl_seconds())
    store.create_account_session(
        account_id=account["id"],
        access_token_hash=_token_hash(access_token),
        refresh_token_hash=_token_hash(refresh_token),
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
        device_label=device_label,
        device_id_hash=device_id_hash,
    )
    return {
        "tokenType": "Bearer",
        "accessTokenFormat": "jwt_hs256",
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "accessExpiresAt": access_expires_at,
        "refreshExpiresAt": refresh_expires_at,
        "deviceTrust": _public_device_trust(device_record, device_bound=bool(device_id_hash)),
    }


def _public_account(account: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": account["accountId"] if "accountId" in account else account["id"],
        "email": account["email"],
        "learnerId": account["learnerId"],
        "createdAt": account.get("createdAt"),
        "disabledAt": account.get("disabledAt"),
        "authProvider": account.get("authProvider") or ("oidc" if account.get("identityProvider") else "password"),
        "identityProvider": account.get("identityProvider"),
    }


def _public_session(session: Dict[str, Any], current_session_id: Optional[str] = None) -> Dict[str, Any]:
    public = {
        "id": session["id"],
        "deviceLabel": session.get("deviceLabel"),
        "deviceBound": bool(session.get("deviceBound")),
        "deviceTrust": _public_device_trust(session.get("deviceTrust"), device_bound=bool(session.get("deviceBound"))),
        "accessExpiresAt": session["accessExpiresAt"],
        "refreshExpiresAt": session["refreshExpiresAt"],
        "revokedAt": session.get("revokedAt"),
        "createdAt": session.get("createdAt"),
        "lastUsedAt": session.get("lastUsedAt"),
    }
    if current_session_id is not None:
        public["isCurrent"] = session["id"] == current_session_id
    return public


def _public_device_trust(device: Optional[Dict[str, Any]], device_bound: bool = False) -> Dict[str, Any]:
    if not device_bound:
        return {
            "deviceId": None,
            "status": "not_bound",
            "trusted": False,
            "attestationProvider": None,
            "attestationVerified": False,
            "verificationMode": "not_bound",
            "trustedAt": None,
            "revokedAt": None,
        }
    status = device.get("status") or device.get("trustStatus") if device else "untracked"
    evidence = device.get("evidence") if device else {}
    attestation_verified = bool(device.get("attestationVerified")) if device else False
    verification_mode = (evidence or {}).get("verificationMode") or device.get("verificationMode") if device else None
    if not verification_mode:
        verification_mode = "platform_verified" if attestation_verified else (
            "account_confirmed_not_platform_verified" if status == "trusted" else "not_verified"
        )
    return {
        "deviceId": device.get("deviceId") or device.get("id") if device else None,
        "status": status,
        "trusted": bool(device.get("trusted") or status == "trusted") if device else False,
        "attestationProvider": device.get("attestationProvider") if device else None,
        "attestationVerified": attestation_verified,
        "verificationMode": verification_mode,
        "trustedAt": device.get("trustedAt") if device else None,
        "revokedAt": device.get("revokedAt") if device else None,
    }


def _public_device(device: Dict[str, Any]) -> Dict[str, Any]:
    evidence = device.get("evidence") or {}
    return {
        "id": device["id"],
        "deviceLabel": device.get("deviceLabel"),
        "platform": device.get("platform"),
        "trustStatus": device.get("trustStatus"),
        "trusted": bool(device.get("trusted")),
        "attestationProvider": device.get("attestationProvider"),
        "attestationVerified": bool(device.get("attestationVerified")),
        "verificationMode": evidence.get("verificationMode") or "not_verified",
        "trustedAt": device.get("trustedAt"),
        "revokedAt": device.get("revokedAt"),
        "lastSeenAt": device.get("lastSeenAt"),
        "createdAt": device.get("createdAt"),
        "updatedAt": device.get("updatedAt"),
        "isCurrent": bool(device.get("isCurrent")),
    }


app = create_app()


def _rate_limit_learner_hint(request: Request) -> str:
    authorization = request.headers.get("Authorization") or ""
    if authorization.lower().startswith("bearer "):
        return "account_" + hashlib.sha256(authorization.encode("utf-8")).hexdigest()[:16]
    token = request.headers.get("X-Learner-Token")
    if token:
        return "token_" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    learner_id = (
        request.headers.get("X-Learner-Id")
        or request.headers.get("X-Anonymous-Id")
        or request.headers.get("X-User-Id")
        or "anonymous"
    )
    return normalize_learner_id(learner_id)


def _review_card_to_anki_note(card: Dict[str, Any], deck_name: str, model_name: str) -> Dict[str, Any]:
    tags = ["ai_language_partner"] + [_anki_tag(tag) for tag in card.get("tags") or []]
    fields = {"Front": card["front"], "Back": card["back"]}
    if model_name.lower() != "basic":
        fields["Example"] = card.get("example") or ""
    return {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "tags": tags,
        "options": {"allowDuplicate": False, "duplicateScope": "deck"},
    }


def _anki_tag(tag: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in tag.strip().lower())
    return cleaned or "tag"
