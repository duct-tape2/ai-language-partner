from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app import providers as provider_module
from app.learner_model import review_cards_to_examples, train_evaluate_memory_model
from app.main import create_app, create_oauth_authorization_code, create_oidc_rs256_id_token, _sign_es256_with_jwk, _sign_rs256_with_jwk
from app.providers import OpenAICompatibleLLMProvider
from app.reputation_model import reputation_profiles_to_examples, train_evaluate_reputation_model
from app.seed import COURSE_CATALOG, PRACTICE_ROOMS
from scripts.validate_openapi_contract import validate_contract
from scripts.verify_docker_smoke import verify_docker_smoke
from scripts.verify_external_provider_readiness import verify_external_provider_readiness
from scripts.verify_hosted_scheduler_readiness import verify_hosted_scheduler_readiness
from scripts.verify_redis_rate_limit_readiness import verify_redis_rate_limit_readiness


TEST_OIDC_RSA_JWK = {
    "kty": "RSA",
    "kid": "benchmark-rs256-key",
    "alg": "RS256",
    "use": "sig",
    "n": "u-iFLpDztQy_GLIMmxpUbdVvAm6ZaUbGjRrh0FH7-sWu78M79goEYr1rrfNf-KPEXUMl38AWwBpMzXi_tM8Q3kF2fRYcosR7hXbTFJcYuIJmD-NauRujY9USSSw-dOYR0LJa716zMJHu3uq2yhSv7o7yEHCARVKe_pqE3yktZ9E",
    "e": "AQAB",
    "d": "VNIV5Do8ODqjvDMK66yL9fRFItTn3RS8pY8_5XhMhRtc5w-67koBRsz4YVIdvS-3gN3Bp-mem2KDzrA14RkjJFndobjiRYrKDfkaWuE0g2ugdEcYvJ-JC2-OtBbqhK77cA1zY6e-V8gS0C-fc_mma2BeEy8Y3blQ2aKAluZ2wQ0",
}
TEST_OIDC_RSA_PUBLIC_JWK = {key: value for key, value in TEST_OIDC_RSA_JWK.items() if key != "d"}

TEST_WEBAUTHN_PRIVATE_JWK = {
    "kty": "EC",
    "crv": "P-256",
    "alg": "ES256",
    "use": "sig",
    "x": "axfR8uEsQkf4vOblY6RA8ncDfYEt6zOg9KE5RdiYwpY",
    "y": "T-NC4v4af5uO5-tKfA-eFivOM1drMV7Oy7ZAaDe_UfU",
    "d": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAE",
}
TEST_WEBAUTHN_PUBLIC_JWK = {key: value for key, value in TEST_WEBAUTHN_PRIVATE_JWK.items() if key != "d"}


def pkce_s256_challenge(verifier: str) -> str:
    # RFC 7636 section 4.2 requires BASE64URL-ENCODE(SHA256(ASCII(code_verifier))) for PKCE S256.
    # This is a protocol proof transform, not password storage; do not substitute a password hash.
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _webauthn_assertion(challenge: str, origin: str = "http://localhost:8000", rp_id: str = "localhost", flags: int = 0x01) -> dict:
    client_data = {
        "type": "webauthn.get",
        "challenge": _b64url(challenge.encode("utf-8")),
        "origin": origin,
        "crossOrigin": False,
    }
    client_data_json = json.dumps(client_data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    authenticator_data = hashlib.sha256(rp_id.encode("utf-8")).digest() + bytes([flags]) + (11).to_bytes(4, "big")
    signed_message = authenticator_data + hashlib.sha256(client_data_json).digest()
    return {
        "algorithm": "webauthn-es256",
        "clientDataJSON": _b64url(client_data_json),
        "authenticatorData": _b64url(authenticator_data),
        "signature": _sign_es256_with_jwk(signed_message, TEST_WEBAUTHN_PRIVATE_JWK),
    }


def run_benchmark() -> dict:
    os.environ.setdefault("AI_LANGUAGE_PARTNER_AUTH_REGISTER_MAX_ATTEMPTS", "3")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_AUTH_REGISTER_WINDOW_SECONDS", "3600")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_AUTH_RISK_MAX_DISTINCT_EMAILS", "2")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_AUTH_RISK_WINDOW_SECONDS", "900")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_XP_DAILY_SOFT_LIMIT", "25")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_XP_BOOSTED_DAILY_SOFT_LIMIT", "10")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET", "benchmark-device-attestation-secret")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_WEBAUTHN_RP_ID", "localhost")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_WEBAUTHN_ALLOWED_ORIGINS", "http://localhost:8000")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_OIDC_LOCAL_OIDC_JWKS_JSON", json.dumps({"keys": [TEST_OIDC_RSA_PUBLIC_JWK]}))
    os.environ.setdefault("AI_LANGUAGE_PARTNER_OAUTH_LOCAL_OIDC_REDIRECT_URIS", "http://localhost:8000/auth/callback")
    os.environ.setdefault("AI_LANGUAGE_PARTNER_OAUTH_ALLOW_LOCAL_SIGNED_CODE", "true")
    with tempfile.TemporaryDirectory() as tmpdir:
        client = TestClient(create_app(Path(tmpdir) / "benchmark.sqlite3"))
        learner_headers = {"X-Learner-Id": "benchmark", "X-User-Id": "benchmark"}
        evidence = {}
        evidence["health"] = client.get("/health").json()
        evidence["providers"] = client.get("/v1/providers/status", headers=learner_headers).json()
        evidence["externalProviderReadiness"] = verify_external_provider_readiness(
            {"AI_LANGUAGE_PARTNER_EXTERNAL_SMOKE_REAL_CALLS": "0"}
        )
        evidence["redisRateLimitReadiness"] = verify_redis_rate_limit_readiness(
            {"AI_LANGUAGE_PARTNER_REDIS_SMOKE_REAL_CALLS": "0"}
        )
        evidence["hostedSchedulerReadiness"] = verify_hosted_scheduler_readiness(
            {"AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_REAL_CALLS": "0"}
        )
        oidc_token = create_oidc_rs256_id_token(
            provider="local-oidc",
            subject="benchmark-oidc-subject",
            email="benchmark-oidc@example.com",
            private_jwk=TEST_OIDC_RSA_JWK,
            nonce="benchmark-nonce",
            kid="benchmark-rs256-key",
        )
        oidc_bad_nonce = client.post(
            "/v1/auth/oidc",
            json={"provider": "local-oidc", "idToken": oidc_token, "nonce": "wrong-nonce"},
        )
        oidc_login = client.post(
            "/v1/auth/oidc",
            json={
                "provider": "local-oidc",
                "idToken": oidc_token,
                "nonce": "benchmark-nonce",
                "learnerId": "benchmark-oidc",
                "deviceLabel": "benchmark-oidc-device",
            },
        ).json()
        oidc_me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {oidc_login['accessToken']}"}).json()
        oauth_redirect_uri = "http://localhost:8000/auth/callback"
        oauth_verifier = "benchmark-verifier-" + ("a" * 60)
        oauth_bad_verifier = "benchmark-verifier-" + ("b" * 60)
        oauth_start = client.post(
            "/v1/auth/oauth/pkce/start",
            json={
                "provider": "local-oidc",
                "redirectUri": oauth_redirect_uri,
                "codeChallenge": pkce_s256_challenge(oauth_verifier),
                "learnerId": "benchmark-oauth-pkce",
                "deviceLabel": "benchmark-oauth-start",
            },
        ).json()
        oauth_bad_code = create_oauth_authorization_code(
            provider="local-oidc",
            subject="benchmark-oauth-subject",
            email="benchmark-oauth@example.com",
            nonce=oauth_start["nonce"],
            state=oauth_start["state"],
        )
        oauth_bad_callback = client.post(
            "/v1/auth/oauth/pkce/callback",
            json={
                "provider": "local-oidc",
                "state": oauth_start["state"],
                "code": oauth_bad_code,
                "codeVerifier": oauth_bad_verifier,
                "redirectUri": oauth_redirect_uri,
            },
        )
        oauth_consumed_after_bad_callback = client.post(
            "/v1/auth/oauth/pkce/callback",
            json={
                "provider": "local-oidc",
                "state": oauth_start["state"],
                "code": oauth_bad_code,
                "codeVerifier": oauth_verifier,
                "redirectUri": oauth_redirect_uri,
            },
        )
        oauth_start_success = client.post(
            "/v1/auth/oauth/pkce/start",
            json={
                "provider": "local-oidc",
                "redirectUri": oauth_redirect_uri,
                "codeChallenge": pkce_s256_challenge(oauth_verifier),
                "learnerId": "benchmark-oauth-pkce",
                "deviceLabel": "benchmark-oauth-start",
            },
        ).json()
        oauth_code = create_oauth_authorization_code(
            provider="local-oidc",
            subject="benchmark-oauth-subject",
            email="benchmark-oauth@example.com",
            nonce=oauth_start_success["nonce"],
            state=oauth_start_success["state"],
        )
        oauth_callback = client.post(
            "/v1/auth/oauth/pkce/callback",
            json={
                "provider": "local-oidc",
                "state": oauth_start_success["state"],
                "code": oauth_code,
                "codeVerifier": oauth_verifier,
                "redirectUri": oauth_redirect_uri,
                "deviceLabel": "benchmark-oauth-device",
            },
        ).json()
        oauth_replay = client.post(
            "/v1/auth/oauth/pkce/callback",
            json={
                "provider": "local-oidc",
                "state": oauth_start_success["state"],
                "code": oauth_code,
                "codeVerifier": oauth_verifier,
                "redirectUri": oauth_redirect_uri,
            },
        )
        oauth_me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {oauth_callback['accessToken']}"}).json()
        sso_redirect_uri = "http://localhost:8000/auth/sso/callback"
        sso_verifier = "benchmark-sso-verifier-" + ("a" * 60)
        sso_admin_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "editor", "X-Admin-User": "benchmark-sso-admin"}
        sso_connection = client.put(
            "/v1/admin/auth/sso-connections/benchmark-sso",
            headers=sso_admin_headers,
            json={
                "provider": "local-oidc",
                "organizationName": "Benchmark Enterprise",
                "domains": ["benchmark.example"],
                "redirectUris": [sso_redirect_uri],
                "requiredEmailDomain": "benchmark.example",
            },
        ).json()
        sso_unmatched = client.get("/v1/auth/sso/discovery", params={"email": "learner@other.example"}).json()
        sso_discovery = client.get("/v1/auth/sso/discovery", params={"email": "Learner@Benchmark.Example"}).json()
        sso_bad_domain_start = client.post(
            "/v1/auth/sso/pkce/start",
            json={
                "email": "learner@benchmark.example",
                "redirectUri": sso_redirect_uri,
                "codeChallenge": pkce_s256_challenge(sso_verifier),
                "learnerId": "benchmark-sso",
                "deviceLabel": "benchmark-sso-start",
            },
        ).json()
        sso_bad_domain_code = create_oauth_authorization_code(
            provider="local-oidc",
            subject="benchmark-sso-bad-domain-subject",
            email="learner@evil.example",
            nonce=sso_bad_domain_start["nonce"],
            state=sso_bad_domain_start["state"],
        )
        sso_bad_domain_callback = client.post(
            "/v1/auth/sso/pkce/callback",
            json={
                "connectionId": "benchmark-sso",
                "state": sso_bad_domain_start["state"],
                "code": sso_bad_domain_code,
                "codeVerifier": sso_verifier,
                "redirectUri": sso_redirect_uri,
            },
        )
        sso_start = client.post(
            "/v1/auth/sso/pkce/start",
            json={
                "email": "learner@benchmark.example",
                "redirectUri": sso_redirect_uri,
                "codeChallenge": pkce_s256_challenge(sso_verifier),
                "learnerId": "benchmark-sso",
                "deviceLabel": "benchmark-sso-start",
            },
        ).json()
        sso_code = create_oauth_authorization_code(
            provider="local-oidc",
            subject="benchmark-sso-subject",
            email="Learner@Benchmark.Example",
            nonce=sso_start["nonce"],
            state=sso_start["state"],
        )
        sso_callback = client.post(
            "/v1/auth/sso/pkce/callback",
            json={
                "connectionId": "benchmark-sso",
                "state": sso_start["state"],
                "code": sso_code,
                "codeVerifier": sso_verifier,
                "redirectUri": sso_redirect_uri,
                "deviceLabel": "benchmark-sso-device",
            },
        ).json()
        sso_replay = client.post(
            "/v1/auth/sso/pkce/callback",
            json={
                "connectionId": "benchmark-sso",
                "state": sso_start["state"],
                "code": sso_code,
                "codeVerifier": sso_verifier,
                "redirectUri": sso_redirect_uri,
            },
        )
        sso_me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {sso_callback['accessToken']}"}).json()
        evidence["providers"] = client.get("/v1/providers/status", headers={"Authorization": f"Bearer {sso_callback['accessToken']}"}).json()
        account = client.post(
            "/v1/auth/register",
            json={"email": "benchmark@example.com", "password": "benchmark-password", "learnerId": "benchmark-account"},
        ).json()
        account_headers = {"Authorization": f"Bearer {account['accessToken']}"}
        account_me = client.get("/v1/auth/me", headers=account_headers).json()
        second_session = client.post(
            "/v1/auth/login",
            json={"email": "benchmark@example.com", "password": "benchmark-password", "deviceLabel": "benchmark-second"},
        ).json()
        sessions_before_revoke = client.get("/v1/auth/sessions", headers=account_headers).json()
        second_session_id = next(
            session["id"] for session in sessions_before_revoke["sessions"] if session.get("deviceLabel") == "benchmark-second"
        )
        remote_revoke = client.request("DELETE", f"/v1/auth/sessions/{second_session_id}", headers=account_headers)
        second_session_after_revoke = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {second_session['accessToken']}"},
        )
        device_trust_login = client.post(
            "/v1/auth/login",
            json={
                "email": "benchmark@example.com",
                "password": "benchmark-password",
                "deviceLabel": "benchmark-phone",
                "deviceId": "benchmark-device-a",
            },
        ).json()
        device_trust_headers = {
            "Authorization": f"Bearer {device_trust_login['accessToken']}",
            "X-Device-Id": "benchmark-device-a",
        }
        device_trust_me_before = client.get("/v1/auth/me", headers=device_trust_headers).json()
        device_trust_list_before = client.get("/v1/auth/devices", headers=device_trust_headers).json()
        device_trust_current_id = device_trust_list_before["currentDeviceId"]
        device_trust_bad_challenge = client.post(
            "/v1/auth/devices/attestation/challenge",
            headers=device_trust_headers,
            json={"attestationProvider": "signed_challenge", "attestationSubject": "benchmark-device-public-key"},
        ).json()
        device_trust_bad_signature = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "signed_challenge",
                "attestationSubject": "benchmark-device-public-key",
                "evidence": {
                    "challengeId": device_trust_bad_challenge["challengeId"],
                    "challenge": device_trust_bad_challenge["challenge"],
                    "signature": "0" * 64,
                },
            },
        )
        device_trust_replay_after_bad_signature = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "signed_challenge",
                "attestationSubject": "benchmark-device-public-key",
                "evidence": {
                    "challengeId": device_trust_bad_challenge["challengeId"],
                    "challenge": device_trust_bad_challenge["challenge"],
                    "signature": hmac.new(
                        os.environ["AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET"].encode("utf-8"),
                        device_trust_bad_challenge["message"].encode("utf-8"),
                        hashlib.sha256,
                    ).hexdigest(),
                },
            },
        )
        device_trust_challenge = client.post(
            "/v1/auth/devices/attestation/challenge",
            headers=device_trust_headers,
            json={"attestationProvider": "signed_challenge", "attestationSubject": "benchmark-device-public-key"},
        ).json()
        device_trust_signature = hmac.new(
            os.environ["AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET"].encode("utf-8"),
            device_trust_challenge["message"].encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        device_trust_marked = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "signed_challenge",
                "attestationSubject": "benchmark-device-public-key",
                "evidence": {
                    "benchmark": True,
                    "challengeId": device_trust_challenge["challengeId"],
                    "challenge": device_trust_challenge["challenge"],
                    "signature": device_trust_signature,
                },
            },
        ).json()
        device_trust_replay_after_success = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "signed_challenge",
                "attestationSubject": "benchmark-device-public-key",
                "evidence": {
                    "challengeId": device_trust_challenge["challengeId"],
                    "challenge": device_trust_challenge["challenge"],
                    "signature": device_trust_signature,
                },
            },
        )
        device_trust_me_after = client.get("/v1/auth/me", headers=device_trust_headers).json()
        public_jwk_subject = json.dumps(TEST_OIDC_RSA_PUBLIC_JWK, separators=(",", ":"), sort_keys=True)
        device_public_key_challenge = client.post(
            "/v1/auth/devices/attestation/challenge",
            headers=device_trust_headers,
            json={"attestationProvider": "public_key_challenge", "attestationSubject": public_jwk_subject},
        ).json()
        device_public_key_signature = _sign_rs256_with_jwk(device_public_key_challenge["message"], TEST_OIDC_RSA_JWK)
        device_public_key_marked = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "public_key_challenge",
                "attestationSubject": public_jwk_subject,
                "evidence": {
                    "benchmark": True,
                    "algorithm": "rs256",
                    "challengeId": device_public_key_challenge["challengeId"],
                    "challenge": device_public_key_challenge["challenge"],
                    "signature": device_public_key_signature,
                },
            },
        ).json()
        device_public_key_me_after = client.get("/v1/auth/me", headers=device_trust_headers).json()
        device_public_key_replay_after_success = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "public_key_challenge",
                "attestationSubject": public_jwk_subject,
                "evidence": {
                    "algorithm": "rs256",
                    "challengeId": device_public_key_challenge["challengeId"],
                    "challenge": device_public_key_challenge["challenge"],
                    "signature": device_public_key_signature,
                },
            },
        )
        webauthn_jwk_subject = json.dumps(TEST_WEBAUTHN_PUBLIC_JWK, separators=(",", ":"), sort_keys=True)
        device_webauthn_bad_challenge = client.post(
            "/v1/auth/devices/attestation/challenge",
            headers=device_trust_headers,
            json={"attestationProvider": "webauthn_public_key", "attestationSubject": webauthn_jwk_subject},
        ).json()
        device_webauthn_bad_evidence = _webauthn_assertion(
            device_webauthn_bad_challenge["challenge"],
            origin="https://evil.example",
        )
        device_webauthn_bad_evidence.update(
            {
                "challengeId": device_webauthn_bad_challenge["challengeId"],
                "challenge": device_webauthn_bad_challenge["challenge"],
            }
        )
        device_webauthn_bad_origin = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "webauthn_public_key",
                "attestationSubject": webauthn_jwk_subject,
                "evidence": device_webauthn_bad_evidence,
            },
        )
        device_webauthn_replay_after_bad_origin = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "webauthn_public_key",
                "attestationSubject": webauthn_jwk_subject,
                "evidence": device_webauthn_bad_evidence,
            },
        )
        device_webauthn_challenge = client.post(
            "/v1/auth/devices/attestation/challenge",
            headers=device_trust_headers,
            json={"attestationProvider": "webauthn_public_key", "attestationSubject": webauthn_jwk_subject},
        ).json()
        device_webauthn_evidence = _webauthn_assertion(device_webauthn_challenge["challenge"])
        device_webauthn_evidence.update(
            {
                "benchmark": True,
                "challengeId": device_webauthn_challenge["challengeId"],
                "challenge": device_webauthn_challenge["challenge"],
            }
        )
        device_webauthn_marked = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "webauthn_public_key",
                "attestationSubject": webauthn_jwk_subject,
                "evidence": device_webauthn_evidence,
            },
        ).json()
        device_webauthn_me_after = client.get("/v1/auth/me", headers=device_trust_headers).json()
        device_webauthn_replay_after_success = client.post(
            "/v1/auth/devices/trust",
            headers=device_trust_headers,
            json={
                "confirmation": "trust-this-device",
                "deviceLabel": "benchmark-phone",
                "platform": "ios",
                "attestationProvider": "webauthn_public_key",
                "attestationSubject": webauthn_jwk_subject,
                "evidence": device_webauthn_evidence,
            },
        )
        device_trust_revoked = client.request("DELETE", f"/v1/auth/devices/{device_trust_current_id}", headers=device_trust_headers)
        device_trust_after_revoke = client.get("/v1/auth/me", headers=device_trust_headers)
        device_trust_reuse_login = client.post(
            "/v1/auth/login",
            json={
                "email": "benchmark@example.com",
                "password": "benchmark-password",
                "deviceLabel": "benchmark-phone-reuse",
                "deviceId": "benchmark-device-a",
            },
        )
        device_trust_new_login = client.post(
            "/v1/auth/login",
            json={
                "email": "benchmark@example.com",
                "password": "benchmark-password",
                "deviceLabel": "benchmark-tablet",
                "deviceId": "benchmark-device-b",
            },
        ).json()
        device_trust_devices_after = client.get(
            "/v1/auth/devices?includeRevoked=true",
            headers={"Authorization": f"Bearer {device_trust_new_login['accessToken']}", "X-Device-Id": "benchmark-device-b"},
        ).json()
        reuse_account = client.post(
            "/v1/auth/register",
            json={
                "email": "benchmark-reuse@example.com",
                "password": "benchmark-password",
                "learnerId": "benchmark-reuse-account",
                "deviceLabel": "benchmark-reuse-a",
            },
        ).json()
        reuse_rotated = client.post(
            "/v1/auth/refresh",
            json={"refreshToken": reuse_account["refreshToken"], "deviceLabel": "benchmark-reuse-rotated"},
        ).json()
        reuse_rotated_headers = {"Authorization": f"Bearer {reuse_rotated['accessToken']}"}
        reuse_rotated_before_replay = client.get("/v1/auth/me", headers=reuse_rotated_headers)
        reuse_replay = client.post("/v1/auth/refresh", json={"refreshToken": reuse_account["refreshToken"]})
        reuse_rotated_after_replay = client.get("/v1/auth/me", headers=reuse_rotated_headers)
        reuse_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
        ]
        registration_abuse_statuses = []
        for index in range(2):
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": f"benchmark-abuse-{index}@example.com",
                    "password": "benchmark-password",
                    "learnerId": f"benchmark-abuse-{index}",
                },
            )
            registration_abuse_statuses.append(response.status_code)
        registration_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
        ]
        evidence["accountAuth"] = {
            "registered": account["account"]["learnerId"] == "benchmark-account",
            "tokenType": account["tokenType"],
            "accessTokenFormat": account["accessTokenFormat"],
            "meLearnerId": account_me["account"]["learnerId"],
            "jwtAccessTokenReturned": account["accessToken"].count(".") == 2,
            "refreshTokenReturned": account["refreshToken"].startswith("alp_rt_"),
            "activeSessionCountBeforeRevoke": sessions_before_revoke["activeSessionCount"],
            "remoteRevokeStatus": remote_revoke.status_code,
            "revokedSessionRejectedStatus": second_session_after_revoke.status_code,
        }
        auth_status = evidence["providers"]["operations"]["auth"]
        device_trust_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
        ]
        evidence["accountDeviceTrustLifecycle"] = {
            "providerDeviceRegistry": auth_status["deviceRegistry"],
            "providerDeviceTrustLifecycle": auth_status["deviceTrustLifecycle"],
            "providerTrustedDeviceEnrollment": auth_status["trustedDeviceEnrollment"],
            "providerDeviceRevokeRevokesSessions": auth_status["deviceRevokeRevokesSessions"],
            "platformAttestationVerification": auth_status["platformAttestationVerification"],
            "providerDeviceAttestationChallenge": auth_status["deviceAttestationChallenge"],
            "providerDeviceAttestationProviders": auth_status["deviceAttestationProviders"],
            "providerPublicKeyDeviceAttestationChallenge": auth_status["publicKeyDeviceAttestationChallenge"],
            "providerPublicKeyDeviceAttestationVerification": auth_status["publicKeyDeviceAttestationVerification"],
            "providerWebAuthnDeviceAttestationChallenge": auth_status["webauthnDeviceAttestationChallenge"],
            "providerWebAuthnDeviceAttestationVerification": auth_status["webauthnDeviceAttestationVerification"],
            "providerWebAuthnRpId": auth_status["webauthnRpId"],
            "providerWebAuthnAllowedOrigins": auth_status["webauthnAllowedOrigins"],
            "providerWebAuthnUserPresenceRequired": auth_status["webauthnUserPresenceRequired"],
            "deviceAttestationChallengeTtlSeconds": auth_status["deviceAttestationChallengeTtlSeconds"],
            "initialTrustStatus": device_trust_login["deviceTrust"]["status"],
            "meTrustBefore": device_trust_me_before["session"]["deviceTrust"]["status"],
            "listedDeviceCountBefore": len(device_trust_list_before["devices"]),
            "currentDeviceIdPresent": bool(device_trust_current_id),
            "challengeIssued": bool(device_trust_challenge.get("challengeId") and device_trust_challenge.get("challenge")),
            "challengeSignatureAlgorithm": device_trust_challenge.get("signatureAlgorithm"),
            "badSignatureStatus": device_trust_bad_signature.status_code,
            "replayAfterBadSignatureStatus": device_trust_replay_after_bad_signature.status_code,
            "trustedStatus": device_trust_marked["device"]["trustStatus"],
            "trustedVerificationMode": device_trust_marked["device"]["verificationMode"],
            "attestationVerified": device_trust_marked["device"]["attestationVerified"],
            "meTrustAfter": device_trust_me_after["session"]["deviceTrust"]["status"],
            "meTrustVerificationModeAfter": device_trust_me_after["session"]["deviceTrust"]["verificationMode"],
            "meTrustAttestationVerifiedAfter": device_trust_me_after["session"]["deviceTrust"]["attestationVerified"],
            "replayAfterSuccessStatus": device_trust_replay_after_success.status_code,
            "publicKeyChallengeIssued": bool(device_public_key_challenge.get("challengeId") and device_public_key_challenge.get("challenge")),
            "publicKeyChallengeSignatureAlgorithm": device_public_key_challenge.get("signatureAlgorithm"),
            "publicKeyTrustedVerificationMode": device_public_key_marked["device"]["verificationMode"],
            "publicKeyAttestationVerified": device_public_key_marked["device"]["attestationVerified"],
            "publicKeyMeTrustVerificationModeAfter": device_public_key_me_after["session"]["deviceTrust"]["verificationMode"],
            "publicKeyReplayAfterSuccessStatus": device_public_key_replay_after_success.status_code,
            "webAuthnChallengeIssued": bool(device_webauthn_challenge.get("challengeId") and device_webauthn_challenge.get("challenge")),
            "webAuthnChallengeSignatureAlgorithm": device_webauthn_challenge.get("signatureAlgorithm"),
            "webAuthnBadOriginStatus": device_webauthn_bad_origin.status_code,
            "webAuthnReplayAfterBadOriginStatus": device_webauthn_replay_after_bad_origin.status_code,
            "webAuthnTrustedVerificationMode": device_webauthn_marked["device"]["verificationMode"],
            "webAuthnAttestationVerified": device_webauthn_marked["device"]["attestationVerified"],
            "webAuthnAllowedOriginMatched": "http://localhost:8000" in auth_status["webauthnAllowedOrigins"],
            "webAuthnRpIdMatched": auth_status["webauthnRpId"] == "localhost",
            "webAuthnUserPresenceRequired": auth_status["webauthnUserPresenceRequired"],
            "webAuthnMeTrustVerificationModeAfter": device_webauthn_me_after["session"]["deviceTrust"]["verificationMode"],
            "webAuthnMeTrustAttestationVerifiedAfter": device_webauthn_me_after["session"]["deviceTrust"]["attestationVerified"],
            "webAuthnReplayAfterSuccessStatus": device_webauthn_replay_after_success.status_code,
            "revokeStatus": device_trust_revoked.status_code,
            "revokedSessionCount": device_trust_revoked.json()["revokedSessionCount"],
            "sessionRejectedAfterRevokeStatus": device_trust_after_revoke.status_code,
            "revokedDeviceLoginRejectedStatus": device_trust_reuse_login.status_code,
            "newDeviceLoginStatus": 200 if device_trust_new_login.get("accessToken") else 0,
            "revokedDeviceListed": any(
                item["id"] == device_trust_current_id and item["trustStatus"] == "revoked"
                for item in device_trust_devices_after["devices"]
            ),
            "auditLogged": "auth_device_trusted" in device_trust_audit_actions
            and "auth_device_revoked" in device_trust_audit_actions,
        }
        evidence["accountOidcFederation"] = {
            "providerStatus": auth_status["oidcFederation"],
            "allowedProviders": auth_status["oidcAllowedProviders"],
            "idTokenVerification": auth_status["oidcIdTokenVerification"],
            "jwksVerification": auth_status["oidcJwksVerification"],
            "jwksConfiguredProviders": auth_status["oidcJwksConfiguredProviders"],
            "authorizationCodePkce": auth_status["oauthAuthorizationCodePkce"],
            "badNonceStatus": oidc_bad_nonce.status_code,
            "loginAuthProvider": oidc_login["account"]["authProvider"],
            "identityProvider": oidc_login["account"]["identityProvider"],
            "meLearnerId": oidc_me["account"]["learnerId"],
            "jwtAccessTokenReturned": oidc_login["accessToken"].count(".") == 2,
        }
        evidence["accountOauthAuthorizationCodePkce"] = {
            "providerStatus": auth_status["oauthAuthorizationCodePkce"],
            "oauthStatus": auth_status["oauth"],
            "s256Only": auth_status["oauthPkceS256Only"],
            "stateStoredHashed": auth_status["oauthPkceStateStoredHashed"],
            "oneTimeState": auth_status["oauthPkceOneTimeState"],
            "configuredProviders": auth_status["oauthPkceConfiguredProviders"],
            "tokenExchangeConfiguredProviders": auth_status["oauthPkceTokenExchangeConfiguredProviders"],
            "localSignedCodeAllowed": auth_status["oauthPkceLocalSignedCodeAllowed"],
            "authorizationUrlHasChallenge": "code_challenge_method=S256" in oauth_start_success["authorizationUrl"],
            "badVerifierStatus": oauth_bad_callback.status_code,
            "stateConsumedAfterBadVerifierStatus": oauth_consumed_after_bad_callback.status_code,
            "loginAuthProvider": oauth_callback["account"]["authProvider"],
            "identityProvider": oauth_callback["account"]["identityProvider"],
            "meLearnerId": oauth_me["account"]["learnerId"],
            "jwtAccessTokenReturned": oauth_callback["accessToken"].count(".") == 2,
            "codeExchangeMode": oauth_callback["oauth"]["codeExchangeMode"],
            "replayStatus": oauth_replay.status_code,
        }
        evidence["accountEnterpriseSso"] = {
            "providerStatus": auth_status["enterpriseSso"],
            "domainDiscoveryStatus": auth_status["enterpriseSsoDomainDiscovery"],
            "authorizationCodePkce": auth_status["enterpriseSsoAuthorizationCodePkce"],
            "connectionCount": auth_status["enterpriseSsoConnectionCount"],
            "configuredProviders": auth_status["enterpriseSsoConfiguredProviders"],
            "connectionId": sso_connection["connection"]["id"],
            "connectionDomain": sso_connection["connection"]["domains"][0],
            "unmatchedDiscovery": sso_unmatched["matched"],
            "matchedDiscovery": sso_discovery["matched"],
            "matchedConnectionId": sso_discovery["connection"]["id"],
            "authorizationUrlHasChallenge": "code_challenge_method=S256" in sso_start["authorizationUrl"],
            "badDomainCallbackStatus": sso_bad_domain_callback.status_code,
            "loginAuthProvider": sso_callback["account"]["authProvider"],
            "identityProvider": sso_callback["account"]["identityProvider"],
            "meLearnerId": sso_me["account"]["learnerId"],
            "ssoConnectionId": sso_callback["sso"]["connectionId"],
            "ssoEmailDomain": sso_callback["sso"]["emailDomain"],
            "codeExchangeMode": sso_callback["oauth"]["codeExchangeMode"],
            "replayStatus": sso_replay.status_code,
            "jwtAccessTokenReturned": sso_callback["accessToken"].count(".") == 2,
        }
        evidence["accountRefreshReuseDetection"] = {
            "providerStatus": auth_status["refreshReuseDetection"],
            "rotatedSessionAcceptedBeforeReplayStatus": reuse_rotated_before_replay.status_code,
            "replayStatus": reuse_replay.status_code,
            "rotatedSessionRejectedAfterReplayStatus": reuse_rotated_after_replay.status_code,
            "auditLogged": "auth_refresh_reuse_detected" in reuse_audit_actions,
        }
        evidence["accountRegistrationThrottle"] = {
            "providerStatus": auth_status["registrationThrottle"],
            "maxAttempts": int(os.environ["AI_LANGUAGE_PARTNER_AUTH_REGISTER_MAX_ATTEMPTS"]),
            "windowSeconds": int(os.environ["AI_LANGUAGE_PARTNER_AUTH_REGISTER_WINDOW_SECONDS"]),
            "statuses": registration_abuse_statuses,
            "auditLogged": "auth_registration_throttled" in registration_audit_actions,
        }
        password_spray_statuses = [
            client.post("/v1/auth/login", json={"email": "benchmark-spray-a@example.com", "password": "bad"}).status_code,
            client.post("/v1/auth/login", json={"email": "benchmark-spray-b@example.com", "password": "bad"}).status_code,
        ]
        password_spray_block = client.post(
            "/v1/auth/login",
            json={"email": "benchmark@example.com", "password": "benchmark-password"},
        )
        password_spray_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
        ]
        evidence["accountPasswordSprayRiskControl"] = {
            "providerStatus": auth_status["passwordSprayRiskControl"],
            "riskBasedProviderStatus": auth_status["riskBasedAbuseControls"],
            "maxDistinctEmails": int(os.environ["AI_LANGUAGE_PARTNER_AUTH_RISK_MAX_DISTINCT_EMAILS"]),
            "windowSeconds": int(os.environ["AI_LANGUAGE_PARTNER_AUTH_RISK_WINDOW_SECONDS"]),
            "failedStatuses": password_spray_statuses,
            "blockedStatus": password_spray_block.status_code,
            "auditLogged": "auth_login_risk_blocked" in password_spray_audit_actions,
        }
        evidence["accountAuthHardening"] = {
            "passwordChange": auth_status["passwordChange"],
            "accountDeletionRequiresPassword": auth_status["accountDeletionRequiresPassword"],
            "optionalDeviceBinding": auth_status["optionalDeviceBinding"],
            "loginFailureThrottle": auth_status["loginFailureThrottle"],
            "passwordSprayRiskControl": auth_status["passwordSprayRiskControl"],
            "jwtAccessTokens": auth_status["jwtAccessTokens"],
            "sessionInventory": auth_status["sessionInventory"],
            "remoteSessionRevoke": auth_status["remoteSessionRevoke"],
            "logoutAllSessions": auth_status["logoutAllSessions"],
            "deviceRegistry": auth_status["deviceRegistry"],
            "deviceTrustLifecycle": auth_status["deviceTrustLifecycle"],
            "trustedDeviceEnrollment": auth_status["trustedDeviceEnrollment"],
            "deviceRevokeRevokesSessions": auth_status["deviceRevokeRevokesSessions"],
        }
        courses = client.get("/v1/courses").json()["courses"]
        evidence["courses"] = {
            "count": len(courses),
            "unitCount": sum(len(course.get("units") or []) for course in courses),
            "lessonCount": sum(len(unit.get("lessons") or []) for course in courses for unit in course.get("units") or []),
            "practiceRoomRefs": sum(
                len(lesson.get("practiceRoomIds") or [])
                for course in courses
                for unit in course.get("units") or []
                for lesson in unit.get("lessons") or []
            ),
        }
        admin_headers = {"X-Admin-Key": "local-dev-admin"}
        editor_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "editor", "X-Admin-User": "benchmark-editor"}
        reviewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "reviewer", "X-Admin-User": "benchmark-reviewer"}
        publisher_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "publisher", "X-Admin-User": "benchmark-publisher"}
        viewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "viewer", "X-Admin-User": "benchmark-viewer"}
        experiment_operations_status = evidence["providers"]["operations"]["experiments"]
        seeded_experiments = client.get("/v1/experiments", headers=viewer_headers).json()["experiments"]
        experiment_assignments_first = client.get("/v1/experiments/assignments", headers=learner_headers).json()
        experiment_assignments_second = client.get("/v1/experiments/assignments", headers=learner_headers).json()
        first_variants = {
            item["experimentKey"]: item["variantKey"]
            for item in experiment_assignments_first["assignments"]
        }
        second_variants = {
            item["experimentKey"]: item["variantKey"]
            for item in experiment_assignments_second["assignments"]
        }
        experiment_conversion = client.post(
            "/v1/experiments/daily_recommendation_copy_v1/events",
            headers=learner_headers,
            json={"eventName": "conversion", "payload": {"benchmark": True}},
        ).json()
        experiment_analytics_forbidden = client.get("/v1/experiments/daily_recommendation_copy_v1/analytics")
        experiment_analytics = client.get(
            "/v1/experiments/daily_recommendation_copy_v1/analytics?minimumExposedLearners=1",
            headers=viewer_headers,
        ).json()["analytics"]
        experiment_conversion_variant_analytics = next(
            item for item in experiment_analytics["variants"] if item["variantKey"] == experiment_conversion["event"]["variantKey"]
        )
        experiment_viewer_create_rejected = client.post(
            "/v1/experiments",
            headers=viewer_headers,
            json={
                "key": "benchmark_experiment_v1",
                "name": "Benchmark experiment",
                "status": "running",
                "variants": [
                    {"key": "control", "label": "Control", "weight": 1},
                    {"key": "test", "label": "Test", "weight": 1},
                ],
            },
        )
        experiment_created = client.post(
            "/v1/experiments",
            headers=editor_headers,
            json={
                "key": "Benchmark Experiment V1",
                "name": "Benchmark experiment",
                "status": "running",
                "variants": [
                    {"key": "control", "label": "Control", "weight": 1, "payload": {"copy": "current"}},
                    {"key": "test", "label": "Test", "weight": 1, "payload": {"copy": "new"}},
                ],
                "allocation": {"unit": "learner"},
            },
        ).json()
        experiment_created_assignment = client.get(
            "/v1/experiments/assignments",
            headers={"X-Learner-Id": "benchmark-experiment-created"},
        ).json()["assignments"]
        experiment_stat_observed_variants = {}
        experiment_stat_converted_trial = False
        for index in range(40):
            stat_headers = {"X-Learner-Id": f"benchmark-experiment-stat-{index}"}
            stat_assignment = next(
                item
                for item in client.get("/v1/experiments/assignments", headers=stat_headers).json()["assignments"]
                if item["experimentKey"] == "benchmark_experiment_v1"
            )
            experiment_stat_observed_variants[stat_assignment["variantKey"]] = (
                experiment_stat_observed_variants.get(stat_assignment["variantKey"], 0) + 1
            )
            if stat_assignment["variantKey"] == "test" and not experiment_stat_converted_trial:
                experiment_stat_converted_trial = True
                client.post(
                    "/v1/experiments/benchmark_experiment_v1/events",
                    headers=stat_headers,
                    json={"eventName": "conversion", "payload": {"benchmark": "statistical_test"}},
                )
            if {"control", "test"} <= set(experiment_stat_observed_variants):
                break
        experiment_statistical_analytics = client.get(
            "/v1/experiments/benchmark_experiment_v1/analytics?minimumExposedLearners=1",
            headers=viewer_headers,
        ).json()["analytics"]
        experiment_statistical_test_variant = next(
            item for item in experiment_statistical_analytics["variants"] if item["variantKey"] == "test"
        )
        experiment_statistical_control_variant = next(
            item for item in experiment_statistical_analytics["variants"] if item["variantKey"] == "control"
        )
        experiment_decision_rejected = client.post(
            "/v1/experiments/benchmark_experiment_v1/decisions",
            headers=editor_headers,
            json={"action": "promote_variant", "variantKey": "missing", "minimumExposedLearners": 1},
        )
        experiment_decision_proposed = client.post(
            "/v1/experiments/benchmark_experiment_v1/decisions",
            headers=editor_headers,
            json={
                "action": "promote_variant",
                "variantKey": "test",
                "minimumExposedLearners": 1,
                "requireStatisticalSignificance": False,
                "reason": "Benchmark smoke rollout decision.",
            },
        ).json()
        experiment_decision_listed = client.get(
            "/v1/experiments/benchmark_experiment_v1/decisions",
            headers=viewer_headers,
        ).json()
        experiment_decision_apply_editor_rejected = client.post(
            f"/v1/experiments/benchmark_experiment_v1/decisions/{experiment_decision_proposed['decision']['id']}/apply",
            headers=editor_headers,
            json={"confirmation": "apply-experiment-decision"},
        )
        experiment_decision_applied = client.post(
            f"/v1/experiments/benchmark_experiment_v1/decisions/{experiment_decision_proposed['decision']['id']}/apply",
            headers=publisher_headers,
            json={"confirmation": "apply-experiment-decision", "note": "Benchmark winner rollout."},
        ).json()
        experiment_post_decision_assignment = client.get(
            "/v1/experiments/assignments",
            headers={"X-Learner-Id": "benchmark-experiment-post-decision"},
        ).json()["assignments"]
        experiment_decision_apply_replay = client.post(
            f"/v1/experiments/benchmark_experiment_v1/decisions/{experiment_decision_proposed['decision']['id']}/apply",
            headers=publisher_headers,
            json={"confirmation": "apply-experiment-decision"},
        )
        experiment_status_updated = client.post(
            "/v1/experiments/benchmark_experiment_v1/status",
            headers=editor_headers,
            json={"status": "paused"},
        ).json()
        experiment_console_forbidden = client.get("/v1/admin/experiment-console")
        experiment_decision_console = client.get(
            "/v1/admin/experiment-console",
            headers=viewer_headers,
            params={"experimentKey": "benchmark_experiment_v1", "minimumExposedLearners": 1},
        )
        experiment_decision_console_missing = client.get(
            "/v1/admin/experiment-console",
            headers=viewer_headers,
            params={"experimentKey": "missing_experiment_v1"},
        )
        experiment_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]
        ]
        evidence["experimentStableAssignmentAndExposure"] = {
            "providerStableAssignments": experiment_operations_status["stableAssignments"],
            "providerWeightedVariants": experiment_operations_status["weightedVariants"],
            "providerExposureLogging": experiment_operations_status["exposureLogging"],
            "providerConversionEventLogging": experiment_operations_status["conversionEventLogging"],
            "providerAdminControls": experiment_operations_status["adminExperimentControls"],
            "providerAnalyticsDashboard": experiment_operations_status["analyticsDashboard"],
            "providerVariantAnalytics": experiment_operations_status["variantAnalytics"],
            "providerDecisionConsole": experiment_operations_status["decisionConsole"],
            "providerDecisionActionConsole": experiment_operations_status["decisionActionConsole"],
            "providerDecisionReadinessGuard": experiment_operations_status["decisionReadinessGuard"],
            "providerStatisticalTesting": experiment_operations_status["statisticalTesting"],
            "providerDecisionWorkflow": experiment_operations_status["decisionWorkflow"],
            "providerDecisionGuardrails": experiment_operations_status["decisionGuardrails"],
            "providerWinnerRolloutApplication": experiment_operations_status["winnerRolloutApplication"],
            "seededExperimentKeys": [item["key"] for item in seeded_experiments],
            "assignmentCount": experiment_assignments_first["assignmentCount"],
            "firstVariants": first_variants,
            "secondVariants": second_variants,
            "stableRepeat": first_variants == second_variants,
            "exposureEventIdPresent": all(bool(item.get("exposureEventId")) for item in experiment_assignments_first["assignments"]),
            "conversionOk": experiment_conversion["ok"],
            "conversionVariant": experiment_conversion["event"]["variantKey"],
            "analyticsForbiddenStatus": experiment_analytics_forbidden.status_code,
            "analyticsExperimentKey": experiment_analytics["experiment"]["key"],
            "analyticsAssignmentCount": experiment_analytics["totals"]["assignmentCount"],
            "analyticsExposureEventCount": experiment_analytics["totals"]["exposureEventCount"],
            "analyticsConversionEventCount": experiment_analytics["totals"]["conversionEventCount"],
            "analyticsBestObservedVariantKey": experiment_analytics["bestObservedVariantKey"],
            "analyticsDecisionReady": experiment_analytics["decisionReady"],
            "analyticsWinnerVariantKey": experiment_analytics["winnerVariantKey"],
            "analyticsConvertedVariantExposedLearners": experiment_conversion_variant_analytics["exposedLearnerCount"],
            "analyticsConvertedVariantConversions": experiment_conversion_variant_analytics["convertedLearnerCount"],
            "analyticsConvertedVariantRate": experiment_conversion_variant_analytics["exposedConversionRate"],
            "viewerCreateRejectedStatus": experiment_viewer_create_rejected.status_code,
            "createdExperimentKey": experiment_created["experiment"]["key"],
            "createdExperimentStatus": experiment_created["experiment"]["status"],
            "createdExperimentAssigned": any(item["experimentKey"] == "benchmark_experiment_v1" for item in experiment_created_assignment),
            "statisticalObservedVariants": experiment_stat_observed_variants,
            "statisticalControlVariantKey": experiment_statistical_analytics["controlVariantKey"],
            "statisticalDecisionReady": experiment_statistical_analytics["decisionReady"],
            "statisticalDecisionRecommendation": experiment_statistical_analytics["decisionRecommendation"],
            "statisticalAlpha": experiment_statistical_analytics["statisticalSignificanceAlpha"],
            "statisticalTestVariantPValue": experiment_statistical_test_variant["pValue"],
            "statisticalTestVariantLift": experiment_statistical_test_variant["absoluteLiftFromBaseline"],
            "statisticalTestVariantConfidenceInterval": experiment_statistical_test_variant["confidenceInterval95"],
            "statisticalControlLift": experiment_statistical_control_variant["absoluteLiftFromBaseline"],
            "statisticalNotesContainZTest": any(
                "two-proportion z-test" in note for note in experiment_statistical_analytics["analysisNotes"]
            ),
            "decisionRejectedStatus": experiment_decision_rejected.status_code,
            "decisionProposalOk": experiment_decision_proposed["ok"],
            "decisionProposalAction": experiment_decision_proposed["decision"]["action"],
            "decisionProposalVariant": experiment_decision_proposed["decision"]["variantKey"],
            "decisionGuardrailOk": experiment_decision_proposed["guardrail"]["ok"],
            "decisionListed": any(
                item["id"] == experiment_decision_proposed["decision"]["id"]
                for item in experiment_decision_listed["decisions"]
            ),
            "decisionApplyEditorRejectedStatus": experiment_decision_apply_editor_rejected.status_code,
            "decisionAppliedStatus": experiment_decision_applied["decision"]["status"],
            "decisionAppliedExperimentStatus": experiment_decision_applied["experiment"]["status"],
            "decisionAppliedWeights": {
                item["key"]: item["weight"] for item in experiment_decision_applied["experiment"]["variants"]
            },
            "decisionAppliedRolloutVariant": experiment_decision_applied["experiment"]["allocation"]["decision"]["rolloutVariantKey"],
            "decisionPostApplyAssignedVariant": next(
                item for item in experiment_post_decision_assignment if item["experimentKey"] == "benchmark_experiment_v1"
            )["variantKey"],
            "decisionApplyReplayStatus": experiment_decision_apply_replay.status_code,
            "pausedStatus": experiment_status_updated["experiment"]["status"],
            "decisionConsoleForbiddenStatus": experiment_console_forbidden.status_code,
            "decisionConsoleStatus": experiment_decision_console.status_code,
            "decisionConsoleMissingStatus": experiment_decision_console_missing.status_code,
            "decisionConsoleContentType": experiment_decision_console.headers.get("content-type", ""),
            "decisionConsoleHasTitle": "Experiment Console" in experiment_decision_console.text,
            "decisionConsoleHasActionConsole": "Experiment Action Console" in experiment_decision_console.text,
            "decisionConsoleHasUpsertAction": "/v1/experiments" in experiment_decision_console.text,
            "decisionConsoleHasStatusAction": "/v1/experiments/__experimentKey__/status" in experiment_decision_console.text,
            "decisionConsoleHasProposeAction": "/v1/experiments/__experimentKey__/decisions" in experiment_decision_console.text,
            "decisionConsoleHasApplyAction": "/v1/experiments/__experimentKey__/decisions/__decisionId__/apply"
            in experiment_decision_console.text,
            "decisionConsoleHasActionResultPanel": "experimentActionResult" in experiment_decision_console.text,
            "decisionConsoleHasExperimentKey": "benchmark_experiment_v1" in experiment_decision_console.text,
            "decisionConsoleHasVariant": "test" in experiment_decision_console.text,
            "decisionConsoleHasDecisionId": experiment_decision_proposed["decision"]["id"] in experiment_decision_console.text,
            "decisionConsoleHasDecisionAction": "promote_variant" in experiment_decision_console.text,
            "decisionConsoleHasAppliedAudit": "experiment_decision_applied" in experiment_decision_console.text,
            "auditLogged": "experiment_upserted" in experiment_audit_actions
            and "experiment_status_updated" in experiment_audit_actions
            and "experiment_analytics_viewed" in experiment_audit_actions
            and "experiment_console_viewed" in experiment_audit_actions,
            "decisionAuditLogged": "experiment_decision_rejected" in experiment_audit_actions
            and "experiment_decision_proposed" in experiment_audit_actions
            and "experiment_decision_applied" in experiment_audit_actions,
        }
        seed_content_payload = {"courses": copy.deepcopy(COURSE_CATALOG), "practiceRooms": copy.deepcopy(PRACTICE_ROOMS)}
        content_quality = client.get("/v1/content/quality-report", headers=viewer_headers).json()["report"]
        content_validation = client.post("/v1/content/validate", headers=editor_headers, json=seed_content_payload).json()["report"]
        content_import_dry_run = client.post("/v1/content/import", headers=editor_headers, json=seed_content_payload).json()
        content_version_id = content_import_dry_run["version"]["id"]
        content_versions = client.get("/v1/content/versions", headers=viewer_headers).json()["versions"]
        content_version_detail = client.get(f"/v1/content/versions/{content_version_id}", headers=viewer_headers).json()["version"]
        content_version_direct_publish_rejected = client.post(
            f"/v1/content/versions/{content_version_id}/publish",
            headers=publisher_headers,
        )
        content_version_viewer_approve_rejected = client.post(
            f"/v1/content/versions/{content_version_id}/approve",
            headers=viewer_headers,
            json={},
        )
        content_version_submit = client.post(
            f"/v1/content/versions/{content_version_id}/submit-review",
            headers=editor_headers,
            json={"note": "benchmark review request"},
        ).json()
        content_version_approve = client.post(
            f"/v1/content/versions/{content_version_id}/approve",
            headers=reviewer_headers,
            json={"note": "benchmark approved"},
        ).json()
        content_version_publish = client.post(f"/v1/content/versions/{content_version_id}/publish", headers=publisher_headers).json()
        release_candidate_payload = copy.deepcopy(seed_content_payload)
        release_course_id = release_candidate_payload["courses"][0]["id"]
        original_release_course_title = release_candidate_payload["courses"][0]["title"]
        release_candidate_payload["courses"][0]["title"] = f"{original_release_course_title} - release candidate"
        content_release_dry_run = client.post("/v1/content/import", headers=editor_headers, json=release_candidate_payload).json()
        content_release_version_id = content_release_dry_run["version"]["id"]
        content_release_unapproved = client.post(
            "/v1/content/releases",
            headers=editor_headers,
            json={"versionId": content_release_version_id, "title": "Benchmark unapproved release"},
        )
        client.post(
            f"/v1/content/versions/{content_release_version_id}/submit-review",
            headers=editor_headers,
            json={"note": "benchmark release candidate"},
        )
        client.post(
            f"/v1/content/versions/{content_release_version_id}/approve",
            headers=reviewer_headers,
            json={"note": "benchmark release approved"},
        )
        content_release_viewer_rejected = client.post(
            "/v1/content/releases",
            headers=viewer_headers,
            json={"versionId": content_release_version_id, "title": "Viewer release attempt"},
        )
        content_release_plan = client.post(
            "/v1/content/releases",
            headers=editor_headers,
            json={
                "versionId": content_release_version_id,
                "title": "Benchmark release canary",
                "releaseStrategy": "canary",
                "rolloutPercent": 25,
                "scheduledAt": "2999-01-01T00:00:00Z",
                "guardrails": {"benchmarkQa": "passed"},
            },
        ).json()
        content_release_editor_apply_rejected = client.post(
            f"/v1/content/releases/{content_release_plan['release']['id']}/apply",
            headers=editor_headers,
            json={"confirmation": "apply-content-release", "force": True},
        )
        content_release_future_apply_rejected = client.post(
            f"/v1/content/releases/{content_release_plan['release']['id']}/apply",
            headers=publisher_headers,
            json={"confirmation": "apply-content-release"},
        )
        content_release_apply = client.post(
            f"/v1/content/releases/{content_release_plan['release']['id']}/apply",
            headers=publisher_headers,
            json={"confirmation": "apply-content-release", "force": True, "note": "benchmark release window"},
        ).json()
        content_release_live_title = client.get(f"/v1/courses/{release_course_id}").json()["course"]["title"]
        content_release_rollback = client.post(
            f"/v1/content/releases/{content_release_plan['release']['id']}/rollback",
            headers=publisher_headers,
            json={"confirmation": "rollback-content-release", "note": "benchmark rollback"},
        ).json()
        content_release_rollback_title = client.get(f"/v1/courses/{release_course_id}").json()["course"]["title"]
        content_worker_payload = copy.deepcopy(seed_content_payload)
        content_worker_payload["courses"][0]["title"] = f"{original_release_course_title} - worker release"
        content_worker_dry_run = client.post("/v1/content/import", headers=editor_headers, json=content_worker_payload).json()
        content_worker_version_id = content_worker_dry_run["version"]["id"]
        client.post(
            f"/v1/content/versions/{content_worker_version_id}/submit-review",
            headers=editor_headers,
            json={"note": "benchmark worker release candidate"},
        )
        client.post(
            f"/v1/content/versions/{content_worker_version_id}/approve",
            headers=reviewer_headers,
            json={"note": "benchmark worker approved"},
        )
        content_worker_release = client.post(
            "/v1/content/releases",
            headers=editor_headers,
            json={
                "versionId": content_worker_version_id,
                "title": "Benchmark scheduled worker release",
                "releaseStrategy": "scheduled",
                "rolloutPercent": 100,
                "scheduledAt": "2000-01-01T00:00:00Z",
            },
        ).json()
        content_worker_editor_rejected = client.post(
            "/v1/content/releases/run-due",
            headers=editor_headers,
            json={"confirmation": "run-due-content-releases"},
        )
        content_worker_run = client.post(
            "/v1/content/releases/run-due",
            headers=publisher_headers,
            json={"confirmation": "run-due-content-releases", "limit": 10},
        ).json()
        content_worker_live_title = client.get(f"/v1/courses/{release_course_id}").json()["course"]["title"]
        content_release_list = client.get("/v1/content/releases", headers=viewer_headers).json()["releases"]
        content_operation_cancelable = client.post(
            "/v1/content/operations/jobs",
            headers=editor_headers,
            json={
                "jobType": "validate_bundle",
                "priority": "normal",
                "payload": {"bundle": seed_content_payload},
            },
        ).json()["job"]
        content_operation_import = client.post(
            "/v1/content/operations/jobs",
            headers=editor_headers,
            json={
                "jobType": "import_bundle",
                "priority": "urgent",
                "payload": {"bundle": seed_content_payload, "dryRun": True, "replaceExisting": True},
            },
        ).json()["job"]
        content_operation_queued = client.get(
            "/v1/content/operations/jobs",
            headers=viewer_headers,
            params={"status": "queued"},
        ).json()["jobs"]
        content_operation_viewer_run_rejected = client.post(
            "/v1/content/operations/jobs/run-next",
            headers=viewer_headers,
            json={"confirmation": "run-next-content-operation-job"},
        )
        content_operation_run = client.post(
            "/v1/content/operations/jobs/run-next",
            headers=publisher_headers,
            json={"confirmation": "run-next-content-operation-job"},
        ).json()
        content_operation_detail = client.get(
            f"/v1/content/operations/jobs/{content_operation_import['id']}",
            headers=viewer_headers,
        ).json()["job"]
        content_operation_cancel = client.post(
            f"/v1/content/operations/jobs/{content_operation_cancelable['id']}/cancel",
            headers=editor_headers,
            json={"confirmation": "cancel-content-operation-job"},
        ).json()["job"]
        content_scheduler_payload = copy.deepcopy(seed_content_payload)
        content_scheduler_payload["courses"][0]["title"] = f"{original_release_course_title} - managed scheduler"
        content_scheduler_dry_run = client.post("/v1/content/import", headers=editor_headers, json=content_scheduler_payload).json()
        content_scheduler_version_id = content_scheduler_dry_run["version"]["id"]
        client.post(
            f"/v1/content/versions/{content_scheduler_version_id}/submit-review",
            headers=editor_headers,
            json={"note": "benchmark managed scheduler candidate"},
        )
        client.post(
            f"/v1/content/versions/{content_scheduler_version_id}/approve",
            headers=reviewer_headers,
            json={"note": "benchmark managed scheduler approved"},
        )
        content_scheduler_release = client.post(
            "/v1/content/releases",
            headers=editor_headers,
            json={
                "versionId": content_scheduler_version_id,
                "title": "Benchmark managed scheduler release",
                "releaseStrategy": "scheduled",
                "rolloutPercent": 100,
                "scheduledAt": "2000-01-02T00:00:00Z",
            },
        ).json()["release"]
        content_scheduler_job = client.post(
            "/v1/content/operations/jobs",
            headers=editor_headers,
            json={
                "jobType": "validate_bundle",
                "priority": "high",
                "payload": {"bundle": content_scheduler_payload},
            },
        ).json()["job"]
        content_scheduler_viewer_rejected = client.post(
            "/v1/content/scheduler/run-once",
            headers=viewer_headers,
            json={"confirmation": "run-content-scheduler-once"},
        )
        content_scheduler_run = client.post(
            "/v1/content/scheduler/run-once",
            headers=publisher_headers,
            json={
                "confirmation": "run-content-scheduler-once",
                "leaseOwner": "benchmark-content-scheduler",
                "maxOperationJobs": 1,
                "releaseLimit": 10,
            },
        ).json()
        content_scheduler_runs = client.get(
            "/v1/content/scheduler/runs",
            headers=viewer_headers,
            params={"status": "succeeded"},
        ).json()["runs"]
        content_scheduler_live_title = client.get(f"/v1/courses/{release_course_id}").json()["course"]["title"]
        content_scheduler_release_list = client.get("/v1/content/releases", headers=viewer_headers).json()["releases"]
        content_ops_console_forbidden = client.get("/v1/admin/ops-console")
        content_ops_console = client.get("/v1/admin/ops-console", headers=viewer_headers)
        content_authoring_console_forbidden = client.get("/v1/admin/content-console")
        content_authoring_console = client.get("/v1/admin/content-console", headers=viewer_headers)
        content_version_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers=admin_headers, params={"limit": 300}).json()["auditLogs"]
        ]
        evidence["contentAuthoring"] = {
            "qualityReportValid": content_quality["valid"],
            "validationValid": content_validation["valid"],
            "dryRun": content_import_dry_run["dryRun"],
            "applied": content_import_dry_run["applied"],
            "dryRunVersionStatus": content_import_dry_run["version"]["status"],
            "errorCount": len(content_validation["errors"]),
            "practiceRoomRefs": content_validation["counts"]["practiceRoomRefs"],
            "roomsWithCoursePlacement": content_validation["counts"]["roomsWithCoursePlacement"],
        }
        evidence["contentVersionedPublishing"] = {
            "providerStatus": evidence["providers"]["operations"]["content"]["versionedPublishing"],
            "roleBasedReviewProviderStatus": evidence["providers"]["operations"]["content"]["roleBasedReview"],
            "approvalRequiredProviderStatus": evidence["providers"]["operations"]["content"]["approvalRequiredForPublish"],
            "versionId": content_version_id,
            "listContainsVersion": any(version["id"] == content_version_id for version in content_versions),
            "detailSnapshotCounts": content_version_detail["snapshotCounts"],
            "detailHasCourseSnapshot": bool(content_version_detail.get("courses")),
            "directPublishRejectedStatus": content_version_direct_publish_rejected.status_code,
            "viewerApproveRejectedStatus": content_version_viewer_approve_rejected.status_code,
            "submittedStatus": content_version_submit["version"]["status"],
            "submittedBy": content_version_submit["version"]["submittedBy"],
            "approvedStatus": content_version_approve["version"]["status"],
            "reviewedBy": content_version_approve["version"]["reviewedBy"],
            "publishOk": content_version_publish["ok"],
            "publishImportedCounts": content_version_publish["importedCounts"],
            "publishedStatus": content_version_publish["version"]["status"],
            "publishedAtPresent": bool(content_version_publish["version"]["publishedAt"]),
            "auditLogged": "content_version_published" in content_version_audit_actions,
            "reviewAuditLogged": "content_version_submitted_for_review" in content_version_audit_actions
            and "content_version_approved" in content_version_audit_actions,
        }
        evidence["contentReleaseAutomation"] = {
            "releasePlansProviderStatus": evidence["providers"]["operations"]["content"]["releasePlans"],
            "releaseSchedulingProviderStatus": evidence["providers"]["operations"]["content"]["releaseScheduling"],
            "canaryMetadataProviderStatus": evidence["providers"]["operations"]["content"]["canaryReleaseMetadata"],
            "releaseWorkerProviderStatus": evidence["providers"]["operations"]["content"]["releaseWorker"],
            "releaseRollbackProviderStatus": evidence["providers"]["operations"]["content"]["releaseRollback"],
            "unapprovedReleaseRejectedStatus": content_release_unapproved.status_code,
            "viewerCreateRejectedStatus": content_release_viewer_rejected.status_code,
            "releaseId": content_release_plan["release"]["id"],
            "releaseStrategy": content_release_plan["release"]["releaseStrategy"],
            "rolloutPercent": content_release_plan["release"]["rolloutPercent"],
            "qualityGuardrailValid": content_release_plan["release"]["guardrails"]["qualityReportValid"],
            "editorApplyRejectedStatus": content_release_editor_apply_rejected.status_code,
            "futureApplyRejectedStatus": content_release_future_apply_rejected.status_code,
            "appliedStatus": content_release_apply["release"]["status"],
            "previousPublishedVersionId": content_release_apply["release"]["previousPublishedVersionId"],
            "liveTitleAfterApply": content_release_live_title,
            "rolledBackStatus": content_release_rollback["release"]["status"],
            "rollbackNote": content_release_rollback["release"]["rollbackNote"],
            "liveTitleAfterRollback": content_release_rollback_title,
            "workerReleaseId": content_worker_release["release"]["id"],
            "workerReleaseStatusBeforeRun": content_worker_release["release"]["status"],
            "workerEditorRejectedStatus": content_worker_editor_rejected.status_code,
            "workerAppliedCount": content_worker_run["appliedCount"],
            "workerSkippedCount": content_worker_run["skippedCount"],
            "workerAppliedReleaseStatus": content_worker_run["appliedReleases"][0]["status"] if content_worker_run["appliedReleases"] else None,
            "liveTitleAfterWorkerRun": content_worker_live_title,
            "listContainsRelease": any(item["id"] == content_release_plan["release"]["id"] for item in content_release_list),
            "listContainsWorkerRelease": any(item["id"] == content_worker_release["release"]["id"] for item in content_release_list),
            "auditLogged": "content_release_planned" in content_version_audit_actions
            and "content_release_applied" in content_version_audit_actions
            and "content_release_worker_run" in content_version_audit_actions
            and "content_release_rolled_back" in content_version_audit_actions,
        }
        evidence["contentOperationJobs"] = {
            "operationJobsProviderStatus": evidence["providers"]["operations"]["content"]["operationJobs"],
            "operationJobRunnerProviderStatus": evidence["providers"]["operations"]["content"]["operationJobRunner"],
            "queuedImportJobId": content_operation_import["id"],
            "cancelableJobId": content_operation_cancelable["id"],
            "urgentJobFirst": bool(content_operation_queued) and content_operation_queued[0]["id"] == content_operation_import["id"],
            "viewerRunRejectedStatus": content_operation_viewer_run_rejected.status_code,
            "runOk": content_operation_run["ok"],
            "runJobStatus": content_operation_run["job"]["status"],
            "runJobType": content_operation_run["job"]["jobType"],
            "runResultOk": content_operation_run["result"]["ok"],
            "runResultVersionSource": content_operation_run["result"]["version"]["source"],
            "detailStatus": content_operation_detail["status"],
            "canceledStatus": content_operation_cancel["status"],
            "auditLogged": "content_operation_job_queued" in content_version_audit_actions
            and "content_operation_job_succeeded" in content_version_audit_actions
            and "content_operation_job_canceled" in content_version_audit_actions,
        }
        evidence["contentManagedScheduler"] = {
            "managedSchedulerProviderStatus": evidence["providers"]["operations"]["content"]["managedScheduler"],
            "schedulerRunHistoryProviderStatus": evidence["providers"]["operations"]["content"]["schedulerRunHistory"],
            "viewerRunRejectedStatus": content_scheduler_viewer_rejected.status_code,
            "runOk": content_scheduler_run["ok"],
            "runStatus": content_scheduler_run["run"]["status"],
            "leaseOwner": content_scheduler_run["run"]["leaseOwner"],
            "releaseAppliedCount": content_scheduler_run["releaseWorker"]["appliedCount"],
            "releaseAppliedId": content_scheduler_run["releaseWorker"]["appliedReleases"][0]["id"]
            if content_scheduler_run["releaseWorker"]["appliedReleases"]
            else None,
            "operationJobsRunCount": content_scheduler_run["run"]["result"]["operationJobsRunCount"],
            "operationJobId": content_scheduler_run["operationJobs"][0]["job"]["id"]
            if content_scheduler_run["operationJobs"]
            else None,
            "operationJobStatus": content_scheduler_run["operationJobs"][0]["job"]["status"]
            if content_scheduler_run["operationJobs"]
            else None,
            "runHistoryContainsRun": bool(content_scheduler_runs)
            and content_scheduler_runs[0]["id"] == content_scheduler_run["run"]["id"],
            "liveTitleAfterSchedulerRun": content_scheduler_live_title,
            "listContainsSchedulerRelease": any(item["id"] == content_scheduler_release["id"] for item in content_scheduler_release_list),
            "auditLogged": "content_scheduler_run_succeeded" in content_version_audit_actions
            and "content_release_worker_run" in content_version_audit_actions
            and "content_operation_job_succeeded" in content_version_audit_actions,
            "queuedJobId": content_scheduler_job["id"],
            "scheduledReleaseId": content_scheduler_release["id"],
        }
        evidence["contentOpsConsole"] = {
            "providerStatus": evidence["providers"]["operations"]["content"]["adminOpsConsole"],
            "actionConsoleProviderStatus": evidence["providers"]["operations"]["content"]["adminActionConsole"],
            "forbiddenStatus": content_ops_console_forbidden.status_code,
            "status": content_ops_console.status_code,
            "contentType": content_ops_console.headers.get("content-type", ""),
            "hasOpsTitle": "Ops Console" in content_ops_console.text,
            "hasActionConsole": "Action Console" in content_ops_console.text,
            "hasRunDueReleaseAction": "/v1/content/releases/run-due" in content_ops_console.text,
            "hasSchedulerAction": "/v1/content/scheduler/run-once" in content_ops_console.text,
            "hasRunNextJobAction": "/v1/content/operations/jobs/run-next" in content_ops_console.text,
            "hasActionResultPanel": "opsActionResult" in content_ops_console.text,
            "hasSchedulerLeaseOwner": "benchmark-content-scheduler" in content_ops_console.text,
            "hasManagedSchedulerRelease": "Benchmark managed scheduler release" in content_ops_console.text,
            "hasSchedulerAuditEvent": "content_scheduler_run_succeeded" in content_ops_console.text,
        }
        evidence["contentAuthoringConsole"] = {
            "providerStatus": evidence["providers"]["operations"]["content"]["adminContentConsole"],
            "forbiddenStatus": content_authoring_console_forbidden.status_code,
            "status": content_authoring_console.status_code,
            "contentType": content_authoring_console.headers.get("content-type", ""),
            "hasContentTitle": "Content Console" in content_authoring_console.text,
            "hasAuthoringActionConsole": "Authoring Action Console" in content_authoring_console.text,
            "hasValidateAction": "/v1/content/validate" in content_authoring_console.text,
            "hasImportAction": "/v1/content/import" in content_authoring_console.text,
            "hasBulkQaAction": "/v1/content/bulk-qa" in content_authoring_console.text,
            "hasTranslationMemorySuggestAction": "/v1/content/translation-memory/suggest" in content_authoring_console.text,
            "hasTranslationMemoryUpsertAction": "/v1/content/translation-memory" in content_authoring_console.text,
            "hasBranchAction": "/v1/content/versions/__versionId__/branch" in content_authoring_console.text,
            "hasAssignAction": "/v1/content/versions/__versionId__/assign" in content_authoring_console.text,
            "hasActionResultPanel": "contentConsoleResult" in content_authoring_console.text,
            "hasCurrentVersionId": content_scheduler_version_id in content_authoring_console.text,
        }
        tired_room = next(room for room in PRACTICE_ROOMS if room["id"] == "tired_today")
        translation_memory_entries = client.get(
            "/v1/content/translation-memory",
            headers=viewer_headers,
            params={"limit": 200},
        ).json()["entries"]
        translation_memory_suggestions = client.post(
            "/v1/content/translation-memory/suggest",
            headers=viewer_headers,
            json={"sourceText": tired_room["primaryPhraseKo"], "limit": 10},
        ).json()["suggestions"]
        translation_memory_custom_upsert = client.post(
            "/v1/content/translation-memory",
            headers=editor_headers,
            json={
                "entries": [
                    {
                        "sourceText": "벤치마크 번역 메모리",
                        "targetText": "ベンチマーク翻訳メモリ",
                        "tags": ["benchmark"],
                        "sourceRef": "benchmark:manual",
                    }
                ]
            },
        ).json()
        content_bulk_qa_current = client.post("/v1/content/bulk-qa", headers=viewer_headers, json={}).json()
        conflict_rooms = copy.deepcopy(PRACTICE_ROOMS)
        conflict_rooms[0]["primaryPhraseJa"] = "意図的に違う翻訳です。"
        content_bulk_qa_conflict = client.post(
            "/v1/content/bulk-qa",
            headers=viewer_headers,
            json={"courses": copy.deepcopy(COURSE_CATALOG), "practiceRooms": conflict_rooms},
        ).json()
        translation_memory_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]
        ]
        content_operations_status = evidence["providers"]["operations"]["content"]
        evidence["contentTranslationMemoryBulkQa"] = {
            "translationMemoryProviderStatus": content_operations_status["translationMemory"],
            "bulkQaProviderStatus": content_operations_status["bulkQa"],
            "translationMemoryEntryCount": len(translation_memory_entries),
            "seedExactSuggestionFound": any(
                item["targetText"] == tired_room["primaryPhraseJa"] and item["matchType"] == "exact"
                for item in translation_memory_suggestions
            ),
            "customUpsertOk": translation_memory_custom_upsert["ok"],
            "customUpsertCount": translation_memory_custom_upsert["upsertedCounts"]["entries"],
            "currentBulkQaOk": content_bulk_qa_current["ok"],
            "currentBulkQaSource": content_bulk_qa_current["source"],
            "currentExactMatches": content_bulk_qa_current["report"]["counts"]["translationMemoryExactMatches"],
            "currentConflictCount": content_bulk_qa_current["report"]["counts"]["translationMemoryConflicts"],
            "conflictBulkQaOk": content_bulk_qa_conflict["ok"],
            "conflictCount": content_bulk_qa_conflict["report"]["counts"]["translationMemoryConflicts"],
            "conflictIssueCodes": [issue["code"] for issue in content_bulk_qa_conflict["report"]["issues"]],
            "auditLogged": "content_translation_memory_upserted" in translation_memory_audit_actions
            and "content_bulk_qa_completed" in translation_memory_audit_actions,
        }
        content_branch = client.post(
            f"/v1/content/versions/{content_version_id}/branch",
            headers=editor_headers,
            json={
                "label": "Benchmark branch",
                "branchName": "benchmark-copy-branch",
                "assignee": "benchmark-writer",
                "priority": "high",
                "dueAt": "2026-07-05T00:00:00Z",
            },
        ).json()
        content_branch_assignment = content_branch["assignment"]
        content_branch_assignments = client.get(
            "/v1/content/assignments",
            headers=viewer_headers,
            params={"assignee": "benchmark-writer"},
        ).json()["assignments"]
        content_branch_viewer_assign_rejected = client.post(
            f"/v1/content/versions/{content_branch['version']['id']}/assign",
            headers=viewer_headers,
            json={"assignee": "benchmark-viewer"},
        )
        content_branch_reassign = client.post(
            f"/v1/content/versions/{content_branch['version']['id']}/assign",
            headers=editor_headers,
            json={"assignee": "benchmark-writer-2", "priority": "urgent", "status": "in_progress"},
        ).json()
        content_branch_assignment_done = client.post(
            f"/v1/content/assignments/{content_branch_assignment['id']}/status",
            headers=reviewer_headers,
            json={"status": "done", "note": "benchmark assignment complete"},
        ).json()
        content_branch_audit_actions = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]
        ]
        evidence["contentBranchingAssignments"] = {
            "providerStatus": content_operations_status["branchingAssignments"],
            "branchOk": content_branch["ok"],
            "branchStatus": content_branch["version"]["status"],
            "branchSource": content_branch["version"]["source"],
            "parentVersionId": content_branch["version"]["parentVersionId"],
            "branchName": content_branch["version"]["branchName"],
            "assignmentAssignee": content_branch_assignment["assignee"],
            "assignmentPriority": content_branch_assignment["priority"],
            "listContainsAssignment": any(item["id"] == content_branch_assignment["id"] for item in content_branch_assignments),
            "viewerAssignRejectedStatus": content_branch_viewer_assign_rejected.status_code,
            "reassignedAssignee": content_branch_reassign["assignment"]["assignee"],
            "reassignedPriority": content_branch_reassign["assignment"]["priority"],
            "doneStatus": content_branch_assignment_done["assignment"]["status"],
            "doneCompletedAtPresent": bool(content_branch_assignment_done["assignment"]["completedAt"]),
            "auditLogged": "content_version_branched" in content_branch_audit_actions
            and "content_assignment_upserted" in content_branch_audit_actions
            and "content_assignment_status_updated" in content_branch_audit_actions,
        }
        conversation = client.post(
            "/v1/conversations",
            headers=learner_headers,
            json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
        ).json()
        turn = client.post(
            f"/v1/conversations/{conversation['conversationId']}/turns",
            headers=learner_headers,
            json={"inputType": "mock_audio", "text": "今日めっちゃ疲れた", "requestTts": True},
        ).json()
        evidence["spokenText"] = turn["spokenText"]
        evidence["pronunciationScore"] = turn["pronunciation"]["score"]
        evidence["conversationPronunciationMode"] = turn["pronunciation"].get("scoringMode")
        evidence["dueCards"] = len(client.get("/v1/review-cards/due", headers=learner_headers).json()["reviewCards"])
        due_cards = client.get("/v1/review-cards/due", headers=learner_headers).json()["reviewCards"]
        if due_cards:
            graded = client.post(
                f"/v1/review-cards/{due_cards[0]['id']}/grade",
                headers=learner_headers,
                json={"quality": 5},
            ).json()["reviewCard"]
        else:
            graded = {}
        evidence["memorySummary"] = client.get("/v1/memory/summary", headers=learner_headers).json()
        evidence["memoryCard"] = {
            "memoryStrengthDays": graded.get("memoryStrengthDays"),
            "recallProbability": graded.get("recallProbability"),
            "recallRisk": graded.get("recallRisk"),
        }
        model_cards = client.get("/v1/review-cards", headers=learner_headers).json()["reviewCards"]
        model_examples = review_cards_to_examples(model_cards, source="benchmark_review_cards")
        model_evaluation = train_evaluate_memory_model(db_examples=model_examples, include_fixture=True)
        learner_model_status = evidence["providers"]["operations"]["learnerModel"]
        evidence["learnerModelEvaluation"] = {
            "providerOfflinePipeline": learner_model_status["offlineTrainEvaluatePipeline"],
            "providerOfflineModelName": learner_model_status["offlineModelName"],
            "providerProductionTrainedModel": learner_model_status["productionTrainedModel"],
            "status": model_evaluation["status"],
            "modelName": model_evaluation["modelName"],
            "dbExampleCount": model_evaluation["dbExampleCount"],
            "fixtureExampleCount": model_evaluation["fixtureExampleCount"],
            "trainCount": model_evaluation["trainCount"],
            "evaluationExampleCount": model_evaluation["evaluation"]["exampleCount"],
            "accuracy": model_evaluation["evaluation"]["accuracy"],
            "brierScore": model_evaluation["evaluation"]["brierScore"],
            "auc": model_evaluation["evaluation"]["auc"],
            "productionTrained": model_evaluation["productionTrained"],
        }
        friend_headers = {"X-Learner-Id": "benchmark-friend", "X-User-Id": "benchmark-friend"}
        friend_conversation = client.post(
            "/v1/conversations",
            headers=friend_headers,
            json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
        ).json()
        client.post(
            f"/v1/conversations/{friend_conversation['conversationId']}/turns",
            headers=friend_headers,
            json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
        )
        friend_invite = client.post(
            "/v1/friends/invites",
            headers=learner_headers,
            json={"friendLearnerId": "benchmark-friend", "message": "benchmark friend quest"},
        ).json()
        friend_summary_before_accept = client.get("/v1/friends", headers=learner_headers).json()
        friend_invite_accept = client.post(
            f"/v1/friends/invites/{friend_invite['invite']['id']}/accept",
            headers=friend_headers,
        ).json()
        friend_summary_after_accept = client.get("/v1/friends", headers=learner_headers).json()
        recommended_friend_headers = {"X-Learner-Id": "benchmark-recommended-friend", "X-User-Id": "benchmark-recommended-friend"}
        recommended_friend_conversation = client.post(
            "/v1/conversations",
            headers=recommended_friend_headers,
            json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
        ).json()
        client.post(
            f"/v1/conversations/{recommended_friend_conversation['conversationId']}/turns",
            headers=recommended_friend_headers,
            json={"inputType": "text", "text": "오늘은 친구 추천 테스트야", "requestTts": False},
        )
        pending_friend_headers = {"X-Learner-Id": "benchmark-pending-friend", "X-User-Id": "benchmark-pending-friend"}
        pending_friend_conversation = client.post(
            "/v1/conversations",
            headers=pending_friend_headers,
            json={"personaId": "yui", "practiceRoomId": "cant_go_today", "mode": "practice"},
        ).json()
        client.post(
            f"/v1/conversations/{pending_friend_conversation['conversationId']}/turns",
            headers=pending_friend_headers,
            json={"inputType": "text", "text": "오늘은 못 갈 수도 있어", "requestTts": False},
        )
        pending_friend_invite = client.post(
            "/v1/friends/invites",
            headers=learner_headers,
            json={"friendLearnerId": "benchmark-pending-friend", "message": "benchmark pending exclusion"},
        ).json()
        private_friend_headers = {"X-Learner-Id": "benchmark-private-friend", "X-User-Id": "benchmark-private-friend"}
        private_friend_conversation = client.post(
            "/v1/conversations",
            headers=private_friend_headers,
            json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
        ).json()
        client.post(
            f"/v1/conversations/{private_friend_conversation['conversationId']}/turns",
            headers=private_friend_headers,
            json={"inputType": "text", "text": "오늘은 비공개 친구 추천 테스트야", "requestTts": False},
        )
        private_settings = client.put(
            "/v1/social/settings",
            headers=private_friend_headers,
            json={"discoverable": False, "allowFriendInvites": False, "showWeeklyXp": False},
        ).json()
        blocked_friend_headers = {"X-Learner-Id": "benchmark-blocked-friend", "X-User-Id": "benchmark-blocked-friend"}
        blocked_friend_conversation = client.post(
            "/v1/conversations",
            headers=blocked_friend_headers,
            json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
        ).json()
        client.post(
            f"/v1/conversations/{blocked_friend_conversation['conversationId']}/turns",
            headers=blocked_friend_headers,
            json={"inputType": "text", "text": "오늘은 차단 친구 추천 테스트야", "requestTts": False},
        )
        social_settings = client.get("/v1/social/settings", headers=learner_headers).json()
        social_block = client.post("/v1/social/blocks/benchmark-blocked-friend", headers=learner_headers).json()
        social_blocks = client.get("/v1/social/blocks", headers=learner_headers).json()
        blocked_invite = client.post(
            "/v1/friends/invites",
            headers=learner_headers,
            json={"friendLearnerId": "benchmark-blocked-friend", "message": "benchmark blocked invite"},
        )
        social_discovery = client.get(
            "/v1/social/discovery",
            headers=learner_headers,
            params={"limit": 10, "targetLanguage": "ja"},
        ).json()
        friend_recommendations = client.get("/v1/friends/recommendations", headers=learner_headers).json()
        reward_shop_admin_before = client.get("/v1/admin/rewards/shop", headers=viewer_headers).json()
        reward_shop_viewer_update = client.put(
            "/v1/admin/rewards/shop/streak_freeze_1",
            headers=viewer_headers,
            json={
                "priceCurrency": "gems",
                "priceAmount": 2,
                "available": True,
                "dailyPurchaseLimit": 1,
                "inventoryLimit": 1,
                "sortOrder": 5,
            },
        )
        reward_shop_admin_update = client.put(
            "/v1/admin/rewards/shop/streak_freeze_1",
            headers=editor_headers,
            json={
                "priceCurrency": "gems",
                "priceAmount": 2,
                "available": True,
                "dailyPurchaseLimit": 1,
                "inventoryLimit": 1,
                "sortOrder": 5,
            },
        ).json()
        reward_shop_before_purchase = client.get("/v1/rewards/shop", headers=learner_headers).json()
        reward_shop_purchase = client.post("/v1/rewards/shop/streak_freeze_1/purchase", headers=learner_headers).json()
        reward_shop_second_purchase = client.post("/v1/rewards/shop/streak_freeze_1/purchase", headers=learner_headers)
        friend_quests = client.get(
            "/v1/friends/quests",
            headers=learner_headers,
            params={"partnerLearnerId": "benchmark-friend"},
        ).json()
        friend_quest = friend_quests["friendQuests"][0]
        friend_claim = client.post(f"/v1/friends/quests/{friend_quest['id']}/claim", headers=learner_headers).json()
        friend_claim_again = client.post(f"/v1/friends/quests/{friend_quest['id']}/claim", headers=learner_headers).json()
        boost_activation = client.post("/v1/rewards/boosts/xp_boost_2x_15m/activate", headers=learner_headers).json()
        before_boost_xp = client.get("/v1/gamification/me", headers=learner_headers).json()["xp"]["todayXp"]
        boosted_conversation = client.post(
            "/v1/conversations",
            headers=learner_headers,
            json={"personaId": "yui", "practiceRoomId": "cant_go_today", "mode": "practice"},
        ).json()
        client.post(
            f"/v1/conversations/{boosted_conversation['conversationId']}/turns",
            headers=learner_headers,
            json={"inputType": "text", "text": "오늘은 못 갈 것 같아", "requestTts": False},
        )
        reward_inventory = client.get("/v1/rewards/inventory", headers=learner_headers).json()
        gamification = client.get("/v1/gamification/me", headers=learner_headers).json()
        leaderboard = client.get("/v1/leaderboards/weekly", headers=learner_headers).json()
        boosted_abuse_flag = next(
            (flag for flag in gamification["xpAbuseFlags"] if flag["reason"] == "boosted_xp_soft_limit_exceeded"),
            None,
        )
        admin_xp_flags = client.get(
            "/v1/admin/xp-abuse-flags",
            headers=viewer_headers,
            params={"learnerId": "benchmark", "status": "open"},
        ).json()
        reputation = client.get("/v1/reputation/me", headers=learner_headers).json()
        admin_reputation_queue = client.get(
            "/v1/admin/reputation/learners",
            headers=viewer_headers,
            params={"band": reputation["riskBand"]},
        ).json()
        admin_reputation_detail = client.get(
            "/v1/admin/reputation/learners/benchmark",
            headers=viewer_headers,
        ).json()
        reputation_model_evaluation = train_evaluate_reputation_model(
            db_examples=reputation_profiles_to_examples([reputation, admin_reputation_detail], source="benchmark_reputation_profiles"),
            include_fixture=True,
        )
        reviewed_xp_flag = (
            client.post(
                f"/v1/admin/xp-abuse-flags/{boosted_abuse_flag['id']}/status",
                headers=reviewer_headers,
                json={"status": "resolved", "note": "benchmark boosted XP review"},
            ).json()
            if boosted_abuse_flag
            else {"ok": False, "flag": {}}
        )
        restored_leaderboard = client.get("/v1/leaderboards/weekly", headers=learner_headers).json()
        gamification_status = evidence["providers"]["operations"]["gamification"]
        xp_boost_inventory_item = next(
            (item for item in reward_inventory["items"] if item["rewardKey"] == "xp_boost_2x_15m"),
            None,
        )
        leaderboard_entry = next((item for item in leaderboard["entries"] if item["learnerId"] == "benchmark"), {})
        restored_leaderboard_entry = next(
            (item for item in restored_leaderboard["entries"] if item["learnerId"] == "benchmark"),
            {},
        )
        friend_recommendation_ids = {item["learnerId"] for item in friend_recommendations["recommendations"]}
        recommended_friend = next(
            (item for item in friend_recommendations["recommendations"] if item["learnerId"] == "benchmark-recommended-friend"),
            {},
        )
        social_discovery_candidate_ids = {item["learnerId"] for item in social_discovery["candidates"]}
        discovered_friend = next(
            (item for item in social_discovery["candidates"] if item["learnerId"] == "benchmark-recommended-friend"),
            {},
        )
        achievement_items = gamification["achievements"]["achievements"]
        xp_rookie_levels = [item for item in achievement_items if item["key"] == "xp_rookie"]
        awarded_achievement_keys = [
            achievement["key"]
            for achievement in achievement_items
            if achievement["awarded"]
        ]
        evidence["gamifiedProgress"] = {
            "providerXpLedger": gamification_status["xpLedger"],
            "providerStreaks": gamification_status["streaks"],
            "providerDailyQuests": gamification_status["dailyQuests"],
            "providerWeeklyLeaderboard": gamification_status["weeklyLeaderboard"],
            "providerAntiDuplicateXpEvents": gamification_status["antiDuplicateXpEvents"],
            "providerAchievements": gamification_status["achievements"],
            "providerAchievementLevels": gamification_status["achievementLevels"],
            "providerAchievementRewardCurrency": gamification_status["achievementRewardCurrency"],
            "providerLeagueTiers": gamification_status["leagueTiers"],
            "providerXpAnomalyFlags": gamification_status["xpAnomalyFlags"],
            "providerFriendQuests": gamification_status["friendQuests"],
            "providerFriendGraph": gamification_status["friendGraph"],
            "providerFriendInvites": gamification_status["friendInvites"],
            "providerFriendRecommendations": gamification_status["friendRecommendations"],
            "providerSocialDiscovery": gamification_status["socialDiscovery"],
            "providerSocialPrivacySettings": gamification_status["socialPrivacySettings"],
            "providerSocialBlocking": gamification_status["socialBlocking"],
            "providerRewardCurrencyLedger": gamification_status["rewardCurrencyLedger"],
            "providerRewardShop": gamification_status["rewardShop"],
            "providerRewardShopOperations": gamification_status["rewardShopOperations"],
            "providerRewardShopPurchaseLimits": gamification_status["rewardShopPurchaseLimits"],
            "providerRewardInventory": gamification_status["rewardInventory"],
            "providerXpBoosts": gamification_status["xpBoosts"],
            "providerBoostedXpLedger": gamification_status["boostedXpLedger"],
            "providerSingleSourceAnomalyFlags": gamification_status["singleSourceAnomalyFlags"],
            "providerBoostAbuseFlags": gamification_status["boostAbuseFlags"],
            "providerDuplicatePayloadAbuseFlags": gamification_status["duplicatePayloadAbuseFlags"],
            "providerLeaderboardExclusionFlags": gamification_status["leaderboardExclusionFlags"],
            "providerXpAbuseReviewQueue": gamification_status["xpAbuseReviewQueue"],
            "providerMultiSignalReputation": gamification_status["multiSignalReputation"],
            "providerReputationReviewQueue": gamification_status["reputationReviewQueue"],
            "providerOfflineReputationModelEvaluation": gamification_status["offlineReputationModelEvaluation"],
            "providerProductionLearnedAntiCheatModel": gamification_status["productionLearnedAntiCheatModel"],
            "todayXp": gamification["xp"]["todayXp"],
            "totalXp": gamification["xp"]["totalXp"],
            "beforeBoostTodayXp": before_boost_xp,
            "currentStreak": gamification["streak"]["currentStreak"],
            "isActiveToday": gamification["streak"]["isActiveToday"],
            "completedQuestKeys": [quest["key"] for quest in gamification["dailyQuests"] if quest["completed"]],
            "friendInviteCreated": friend_invite["created"],
            "friendInviteOutgoingCountBeforeAccept": len(friend_summary_before_accept["outgoingInvites"]),
            "friendInviteAccepted": friend_invite_accept["accepted"],
            "friendCountAfterAccept": friend_summary_after_accept["friendCount"],
            "friendGraphContainsPartner": any(item["friendLearnerId"] == "benchmark-friend" for item in friend_summary_after_accept["friends"]),
            "pendingFriendInviteCreated": pending_friend_invite["created"],
            "friendRecommendationContainsCandidate": "benchmark-recommended-friend" in friend_recommendation_ids,
            "friendRecommendationExcludesAcceptedFriend": "benchmark-friend" not in friend_recommendation_ids,
            "friendRecommendationExcludesPendingInvite": "benchmark-pending-friend" not in friend_recommendation_ids,
            "friendRecommendationExcludedFriendCount": friend_recommendations["excludedFriendCount"],
            "friendRecommendationExcludedPendingInviteCount": friend_recommendations["excludedPendingInviteCount"],
            "friendRecommendationReasonCodes": recommended_friend.get("reasonCodes", []),
            "friendRecommendationScore": recommended_friend.get("score", 0),
            "socialSettingsDiscoverable": social_settings["discoverable"],
            "privateSocialSettingsDiscoverable": private_settings["discoverable"],
            "privateSocialSettingsAllowsInvites": private_settings["allowFriendInvites"],
            "socialBlockCreated": social_block["blocked"],
            "socialBlockCount": social_blocks["count"],
            "blockedInviteStatus": blocked_invite.status_code,
            "blockedInviteReason": blocked_invite.json()["detail"]["reason"],
            "socialDiscoveryContainsCandidate": "benchmark-recommended-friend" in social_discovery_candidate_ids,
            "socialDiscoveryExcludesAcceptedFriend": "benchmark-friend" not in social_discovery_candidate_ids,
            "socialDiscoveryExcludesPendingInvite": "benchmark-pending-friend" not in social_discovery_candidate_ids,
            "socialDiscoveryExcludesPrivate": "benchmark-private-friend" not in social_discovery_candidate_ids,
            "socialDiscoveryExcludesBlocked": "benchmark-blocked-friend" not in social_discovery_candidate_ids,
            "socialDiscoveryExcludedPrivateCount": social_discovery["excludedPrivateCount"],
            "socialDiscoveryExcludedBlockedCount": social_discovery["excludedBlockedCount"],
            "socialDiscoveryExcludedFriendOrPendingCount": social_discovery["excludedFriendOrPendingCount"],
            "socialDiscoveryReasonCodes": discovered_friend.get("reasonCodes", []),
            "socialDiscoveryCanInvite": discovered_friend.get("canInvite", False),
            "friendRecommendationExcludesPrivate": "benchmark-private-friend" not in friend_recommendation_ids,
            "friendRecommendationExcludesBlocked": "benchmark-blocked-friend" not in friend_recommendation_ids,
            "friendRecommendationExcludedPrivateCount": friend_recommendations["excludedPrivateCount"],
            "friendRecommendationExcludedBlockedCount": friend_recommendations["excludedBlockedCount"],
            "rewardShopAdminCount": reward_shop_admin_before["count"],
            "rewardShopViewerUpdateStatus": reward_shop_viewer_update.status_code,
            "rewardShopAdminUpdated": reward_shop_admin_update["updated"],
            "rewardShopUpdatedBy": reward_shop_admin_update["item"]["updatedBy"],
            "rewardShopDailyPurchaseLimit": reward_shop_admin_update["item"]["dailyPurchaseLimit"],
            "rewardShopInventoryLimit": reward_shop_admin_update["item"]["inventoryLimit"],
            "shopGemBalanceBeforePurchase": next(
                item["balance"] for item in reward_shop_before_purchase["balances"] if item["currencyKey"] == "gems"
            ),
            "shopStreakFreezeRemainingBeforePurchase": next(
                item["remainingDailyPurchases"] for item in reward_shop_before_purchase["items"] if item["rewardKey"] == "streak_freeze_1"
            ),
            "shopPurchaseSucceeded": reward_shop_purchase["purchased"],
            "shopPurchaseRewardKey": reward_shop_purchase["inventoryItem"]["rewardKey"],
            "shopGemBalanceAfterPurchase": next(
                item["balance"] for item in reward_shop_purchase["shop"]["balances"] if item["currencyKey"] == "gems"
            ),
            "shopStreakFreezeRemainingAfterPurchase": next(
                item["remainingDailyPurchases"] for item in reward_shop_purchase["shop"]["items"] if item["rewardKey"] == "streak_freeze_1"
            ),
            "shopSecondPurchaseStatus": reward_shop_second_purchase.status_code,
            "shopSecondPurchaseReason": reward_shop_second_purchase.json()["detail"]["reason"],
            "friendQuestCompleted": friend_quest["completed"],
            "friendQuestCombinedXp": friend_quest["combinedXp"],
            "friendQuestClaimed": friend_claim["claimed"],
            "friendQuestClaimIdempotent": friend_claim_again["alreadyClaimed"] is True
            and friend_claim_again["rewardItem"]["quantity"] == friend_claim["rewardItem"]["quantity"],
            "rewardKey": friend_claim["rewardItem"]["rewardKey"],
            "boostActivated": boost_activation["activated"],
            "boostMultiplier": boost_activation["activeBoost"]["multiplier"],
            "activeBoostCount": len(reward_inventory["activeXpBoosts"]),
            "inventoryQuantityAfterActivation": xp_boost_inventory_item["quantity"] if xp_boost_inventory_item else None,
            "inventoryHasStreakFreeze": any(item["rewardKey"] == "streak_freeze_1" for item in reward_inventory["items"]),
            "leagueTier": gamification["league"]["currentTier"]["key"],
            "achievementAwardedCount": gamification["achievements"]["awardedCount"],
            "achievementTotalCount": gamification["achievements"]["totalCount"],
            "achievementTrackCount": gamification["achievements"]["trackCount"],
            "achievementCompletedTrackCount": gamification["achievements"]["completedTrackCount"],
            "achievementXpRookieLevels": [item["level"] for item in xp_rookie_levels],
            "achievementXpRookieMaxLevel": max((item["maxLevel"] for item in xp_rookie_levels), default=0),
            "achievementRewardGemsAvailable": sum(int(item["rewardGems"]) for item in achievement_items),
            "awardedAchievementKeys": awarded_achievement_keys,
            "xpAbuseFlagReasons": [flag["reason"] for flag in gamification["xpAbuseFlags"]],
            "boostedXpFlagStatus": boosted_abuse_flag["status"] if boosted_abuse_flag else None,
            "boostedXpFlagLeaderboardExcluded": boosted_abuse_flag["leaderboardExcluded"] if boosted_abuse_flag else False,
            "adminXpFlagsCount": admin_xp_flags["count"],
            "adminXpFlagsContainsBoostedFlag": bool(
                boosted_abuse_flag and any(flag["id"] == boosted_abuse_flag["id"] for flag in admin_xp_flags["flags"])
            ),
            "reputationRiskScore": reputation["riskScore"],
            "reputationRiskBand": reputation["riskBand"],
            "reputationReviewRecommended": reputation["reviewRecommended"],
            "reputationLeaderboardEligible": reputation["leaderboardEligible"],
            "reputationSignalKeys": [signal["key"] for signal in reputation["signals"]],
            "reputationOpenXpAbuseFlagCount": reputation["summary"]["openXpAbuseFlagCount"],
            "reputationBlockingXpAbuseFlagCount": reputation["summary"]["blockingXpAbuseFlagCount"],
            "reputationWeekXp": reputation["summary"]["weekXp"],
            "adminReputationQueueCount": admin_reputation_queue["count"],
            "adminReputationQueueContainsLearner": any(
                profile["learnerId"] == "benchmark" for profile in admin_reputation_queue["profiles"]
            ),
            "adminReputationDetailMatchesScore": admin_reputation_detail["riskScore"] == reputation["riskScore"],
            "reputationModelStatus": reputation_model_evaluation["status"],
            "reputationModelName": reputation_model_evaluation["modelName"],
            "reputationModelDbExampleCount": reputation_model_evaluation["dbExampleCount"],
            "reputationModelFixtureExampleCount": reputation_model_evaluation["fixtureExampleCount"],
            "reputationModelTrainCount": reputation_model_evaluation["trainCount"],
            "reputationModelEvaluation": reputation_model_evaluation["evaluation"],
            "reputationModelProductionTrained": reputation_model_evaluation["productionTrained"],
            "reviewedBoostedXpFlag": reviewed_xp_flag["ok"],
            "reviewedBoostedXpFlagStatus": reviewed_xp_flag["flag"].get("status"),
            "leaderboardExcludedBeforeReview": bool(leaderboard_entry.get("leaderboardExcluded")),
            "leaderboardExclusionReasonsBeforeReview": leaderboard_entry.get("exclusionReasons", []),
            "leaderboardExcludedAfterReview": bool(restored_leaderboard_entry.get("leaderboardExcluded")),
            "leaderboardRestoredRankAfterReview": restored_leaderboard["currentLearnerRank"],
            "leaderboardCurrentRank": leaderboard["currentLearnerRank"],
            "leaderboardTopLearner": leaderboard["entries"][0]["learnerId"] if leaderboard["entries"] else None,
        }
        evidence["grammarN5"] = len(client.get("/v1/grammar/jlpt?level=N5").json()["grammarPoints"])
        evidence["grammarTotal"] = len(client.get("/v1/grammar/jlpt").json()["grammarPoints"])
        evidence["mistakePatterns"] = len(client.get("/v1/mistakes/korean-patterns").json()["mistakePatterns"])
        evidence["ankiCsv"] = client.get("/v1/export/anki", headers=learner_headers).json()["format"]
        evidence["ankiApkgBytes"] = len(client.get("/v1/export/anki-apkg", headers=learner_headers).json()["contentBase64"])
        evidence["recommendations"] = len(client.get("/v1/recommendations/today", headers=learner_headers).json()["recommendedPracticeRooms"])
        evidence["usage"] = client.get("/v1/usage/summary", headers=learner_headers).json()["usage"]
        tts_audio = client.post(
            "/v1/tts/synthesize",
            headers=learner_headers,
            json={"text": "今日めっちゃ疲れた。", "personaId": "yui", "language": "ja"},
        ).json()["audioBase64"]
        acoustic = client.post(
            "/v1/pronunciation/score",
            json={"expectedText": "今日めっちゃ疲れた。", "actualText": "今日めっちゃ疲れた。", "audioBase64": tts_audio},
        ).json()
        original_post_json = provider_module._post_json
        llm_repair_calls = {"count": 0}

        def fake_llm_post_json(url, payload, api_key, timeout):
            llm_repair_calls["count"] += 1
            if llm_repair_calls["count"] == 1:
                return {"choices": [{"message": {"content": '{"assistantTextKo":"schema 없음"}'}}]}
            if llm_repair_calls["count"] == 2:
                return {"choices": [{"message": {"content": '{"schemaVersion":"turn_payload_v1","assistantTextKo":"아직 부족"}'}}]}
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"schemaVersion":"turn_payload_v1",'
                                '"assistantTextKo":"다중 repair로 정상화했어.",'
                                '"spokenTextJa":"今日はかなり疲れた",'
                                '"suggestedUserReplyJa":"今日はかなり疲れた",'
                                '"corrections":[],'
                                '"reviewCards":[{"front":"오늘 꽤 피곤했어","back":"今日はかなり疲れた","tags":["감정표현"]}]}'
                            )
                        }
                    }
                ]
            }

        try:
            provider_module._post_json = fake_llm_post_json
            multi_repair_provider = OpenAICompatibleLLMProvider(
                api_key="benchmark-secret",
                base_url="https://llm.example/v1",
                model="benchmark-model",
                repair_attempts=2,
            )
            multi_repair_turn = multi_repair_provider.generate_turn(
                {"id": "yui", "displayName": "유이"},
                {"id": "tired_today", "primaryPhraseKo": "오늘 너무 피곤했어", "primaryPhraseJa": "今日めっちゃ疲れた"},
                "오늘 꽤 피곤했어",
            )
        finally:
            provider_module._post_json = original_post_json
        evidence["acousticPronunciation"] = {
            "provider": acoustic["provider"],
            "scoringMode": acoustic["scoringMode"],
            "acousticEvidencePresent": acoustic["acousticEvidencePresent"],
            "durationMs": acoustic["acousticFeatures"]["durationMs"],
            "score": acoustic["score"],
        }
        evidence["llmMultiRepairPolicy"] = {
            "repairAttempts": multi_repair_provider.describe()["structuredOutputRepairAttempts"],
            "postCalls": llm_repair_calls["count"],
            "providerWarning": multi_repair_turn.get("providerWarning"),
            "spokenText": multi_repair_turn.get("spokenText"),
        }
        privacy = client.delete("/v1/privacy/me", headers=learner_headers).json()
        evidence["privacyDeletion"] = privacy
        evidence["auditLogActions"] = [
            entry["action"]
            for entry in client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
        ]
        evidence["openapiValidation"] = validate_contract()
        evidence["dockerArtifactVerification"] = verify_docker_smoke(
            {"AI_LANGUAGE_PARTNER_DOCKER_SMOKE_REAL_RUNS": "0"}
        )

        checks = {
            "contract_health": evidence["health"]["ok"] is True,
            "openapi_contract_validation": evidence["openapiValidation"]["allContractOperationsImplemented"] is True,
            "account_auth_session": evidence["accountAuth"]["meLearnerId"] == "benchmark-account",
            "account_auth_jwt_access_tokens": evidence["accountAuth"]["accessTokenFormat"] == "jwt_hs256"
            and evidence["accountAuth"]["jwtAccessTokenReturned"] is True,
            "account_oidc_federation": evidence["accountOidcFederation"]["providerStatus"] is True
            and "local-oidc" in evidence["accountOidcFederation"]["allowedProviders"]
            and evidence["accountOidcFederation"]["idTokenVerification"] == "hs256_rs256_jwks"
            and evidence["accountOidcFederation"]["badNonceStatus"] == 401
            and evidence["accountOidcFederation"]["loginAuthProvider"] == "oidc"
            and evidence["accountOidcFederation"]["identityProvider"] == "local-oidc"
            and evidence["accountOidcFederation"]["meLearnerId"] == "benchmark-oidc"
            and evidence["accountOidcFederation"]["jwtAccessTokenReturned"] is True
            and evidence["accountOidcFederation"]["jwksVerification"] is True
            and "local-oidc" in evidence["accountOidcFederation"]["jwksConfiguredProviders"]
            and evidence["accountOidcFederation"]["authorizationCodePkce"] is True,
            "account_oauth_authorization_code_pkce": evidence["accountOauthAuthorizationCodePkce"]["providerStatus"] is True
            and evidence["accountOauthAuthorizationCodePkce"]["oauthStatus"] is True
            and evidence["accountOauthAuthorizationCodePkce"]["s256Only"] is True
            and evidence["accountOauthAuthorizationCodePkce"]["stateStoredHashed"] is True
            and evidence["accountOauthAuthorizationCodePkce"]["oneTimeState"] is True
            and "local-oidc" in evidence["accountOauthAuthorizationCodePkce"]["configuredProviders"]
            and evidence["accountOauthAuthorizationCodePkce"]["localSignedCodeAllowed"] is True
            and evidence["accountOauthAuthorizationCodePkce"]["authorizationUrlHasChallenge"] is True
            and evidence["accountOauthAuthorizationCodePkce"]["badVerifierStatus"] == 401
            and evidence["accountOauthAuthorizationCodePkce"]["stateConsumedAfterBadVerifierStatus"] == 401
            and evidence["accountOauthAuthorizationCodePkce"]["loginAuthProvider"] == "oidc"
            and evidence["accountOauthAuthorizationCodePkce"]["identityProvider"] == "local-oidc"
            and evidence["accountOauthAuthorizationCodePkce"]["meLearnerId"] == "benchmark-oauth-pkce"
            and evidence["accountOauthAuthorizationCodePkce"]["jwtAccessTokenReturned"] is True
            and evidence["accountOauthAuthorizationCodePkce"]["codeExchangeMode"] == "local_signed_code"
            and evidence["accountOauthAuthorizationCodePkce"]["replayStatus"] == 401,
            "account_enterprise_sso": evidence["accountEnterpriseSso"]["providerStatus"] is True
            and evidence["accountEnterpriseSso"]["domainDiscoveryStatus"] is True
            and evidence["accountEnterpriseSso"]["authorizationCodePkce"] is True
            and evidence["accountEnterpriseSso"]["connectionCount"] >= 1
            and "local-oidc" in evidence["accountEnterpriseSso"]["configuredProviders"]
            and evidence["accountEnterpriseSso"]["connectionId"] == "benchmark-sso"
            and evidence["accountEnterpriseSso"]["connectionDomain"] == "benchmark.example"
            and evidence["accountEnterpriseSso"]["unmatchedDiscovery"] is False
            and evidence["accountEnterpriseSso"]["matchedDiscovery"] is True
            and evidence["accountEnterpriseSso"]["matchedConnectionId"] == "benchmark-sso"
            and evidence["accountEnterpriseSso"]["authorizationUrlHasChallenge"] is True
            and evidence["accountEnterpriseSso"]["badDomainCallbackStatus"] == 401
            and evidence["accountEnterpriseSso"]["loginAuthProvider"] == "oidc"
            and evidence["accountEnterpriseSso"]["identityProvider"] == "sso:benchmark-sso"
            and evidence["accountEnterpriseSso"]["meLearnerId"] == "benchmark-sso"
            and evidence["accountEnterpriseSso"]["ssoConnectionId"] == "benchmark-sso"
            and evidence["accountEnterpriseSso"]["ssoEmailDomain"] == "benchmark.example"
            and evidence["accountEnterpriseSso"]["codeExchangeMode"] == "local_signed_code"
            and evidence["accountEnterpriseSso"]["replayStatus"] == 401
            and evidence["accountEnterpriseSso"]["jwtAccessTokenReturned"] is True,
            "account_session_management": evidence["accountAuth"]["activeSessionCountBeforeRevoke"] >= 2
            and evidence["accountAuth"]["remoteRevokeStatus"] == 200
            and evidence["accountAuth"]["revokedSessionRejectedStatus"] == 401,
            "account_device_trust_lifecycle": evidence["accountDeviceTrustLifecycle"]["providerDeviceRegistry"] is True
            and evidence["accountDeviceTrustLifecycle"]["providerDeviceTrustLifecycle"] is True
            and evidence["accountDeviceTrustLifecycle"]["providerTrustedDeviceEnrollment"] is True
            and evidence["accountDeviceTrustLifecycle"]["providerDeviceRevokeRevokesSessions"] is True
            and evidence["accountDeviceTrustLifecycle"]["platformAttestationVerification"] == "signed_challenge_hmac"
            and evidence["accountDeviceTrustLifecycle"]["providerDeviceAttestationChallenge"] is True
            and "public_key_challenge" in evidence["accountDeviceTrustLifecycle"]["providerDeviceAttestationProviders"]
            and "webauthn_public_key" in evidence["accountDeviceTrustLifecycle"]["providerDeviceAttestationProviders"]
            and evidence["accountDeviceTrustLifecycle"]["providerPublicKeyDeviceAttestationChallenge"] is True
            and evidence["accountDeviceTrustLifecycle"]["providerPublicKeyDeviceAttestationVerification"] == "public_key_challenge_rs256"
            and evidence["accountDeviceTrustLifecycle"]["providerWebAuthnDeviceAttestationChallenge"] is True
            and evidence["accountDeviceTrustLifecycle"]["providerWebAuthnDeviceAttestationVerification"] == "webauthn_assertion_es256"
            and evidence["accountDeviceTrustLifecycle"]["providerWebAuthnRpId"] == "localhost"
            and "http://localhost:8000" in evidence["accountDeviceTrustLifecycle"]["providerWebAuthnAllowedOrigins"]
            and evidence["accountDeviceTrustLifecycle"]["providerWebAuthnUserPresenceRequired"] is True
            and evidence["accountDeviceTrustLifecycle"]["deviceAttestationChallengeTtlSeconds"] > 0
            and evidence["accountDeviceTrustLifecycle"]["initialTrustStatus"] == "untrusted"
            and evidence["accountDeviceTrustLifecycle"]["meTrustBefore"] == "untrusted"
            and evidence["accountDeviceTrustLifecycle"]["currentDeviceIdPresent"] is True
            and evidence["accountDeviceTrustLifecycle"]["challengeIssued"] is True
            and evidence["accountDeviceTrustLifecycle"]["challengeSignatureAlgorithm"] == "hmac-sha256"
            and evidence["accountDeviceTrustLifecycle"]["badSignatureStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["replayAfterBadSignatureStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["trustedStatus"] == "trusted"
            and evidence["accountDeviceTrustLifecycle"]["trustedVerificationMode"] == "signed_challenge_hmac"
            and evidence["accountDeviceTrustLifecycle"]["attestationVerified"] is True
            and evidence["accountDeviceTrustLifecycle"]["meTrustAfter"] == "trusted"
            and evidence["accountDeviceTrustLifecycle"]["meTrustVerificationModeAfter"] == "signed_challenge_hmac"
            and evidence["accountDeviceTrustLifecycle"]["meTrustAttestationVerifiedAfter"] is True
            and evidence["accountDeviceTrustLifecycle"]["replayAfterSuccessStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["publicKeyChallengeIssued"] is True
            and evidence["accountDeviceTrustLifecycle"]["publicKeyChallengeSignatureAlgorithm"] == "rs256"
            and evidence["accountDeviceTrustLifecycle"]["publicKeyTrustedVerificationMode"] == "public_key_challenge_rs256"
            and evidence["accountDeviceTrustLifecycle"]["publicKeyAttestationVerified"] is True
            and evidence["accountDeviceTrustLifecycle"]["publicKeyMeTrustVerificationModeAfter"] == "public_key_challenge_rs256"
            and evidence["accountDeviceTrustLifecycle"]["publicKeyReplayAfterSuccessStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["webAuthnChallengeIssued"] is True
            and evidence["accountDeviceTrustLifecycle"]["webAuthnChallengeSignatureAlgorithm"] == "webauthn-es256"
            and evidence["accountDeviceTrustLifecycle"]["webAuthnBadOriginStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["webAuthnReplayAfterBadOriginStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["webAuthnTrustedVerificationMode"] == "webauthn_assertion_es256"
            and evidence["accountDeviceTrustLifecycle"]["webAuthnAttestationVerified"] is True
            and evidence["accountDeviceTrustLifecycle"]["webAuthnAllowedOriginMatched"] is True
            and evidence["accountDeviceTrustLifecycle"]["webAuthnRpIdMatched"] is True
            and evidence["accountDeviceTrustLifecycle"]["webAuthnUserPresenceRequired"] is True
            and evidence["accountDeviceTrustLifecycle"]["webAuthnMeTrustVerificationModeAfter"] == "webauthn_assertion_es256"
            and evidence["accountDeviceTrustLifecycle"]["webAuthnMeTrustAttestationVerifiedAfter"] is True
            and evidence["accountDeviceTrustLifecycle"]["webAuthnReplayAfterSuccessStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["revokeStatus"] == 200
            and evidence["accountDeviceTrustLifecycle"]["revokedSessionCount"] >= 1
            and evidence["accountDeviceTrustLifecycle"]["sessionRejectedAfterRevokeStatus"] == 401
            and evidence["accountDeviceTrustLifecycle"]["revokedDeviceLoginRejectedStatus"] == 403
            and evidence["accountDeviceTrustLifecycle"]["newDeviceLoginStatus"] == 200
            and evidence["accountDeviceTrustLifecycle"]["revokedDeviceListed"] is True
            and evidence["accountDeviceTrustLifecycle"]["auditLogged"] is True,
            "account_refresh_reuse_detection": evidence["accountRefreshReuseDetection"]["providerStatus"] is True
            and evidence["accountRefreshReuseDetection"]["rotatedSessionAcceptedBeforeReplayStatus"] == 200
            and evidence["accountRefreshReuseDetection"]["replayStatus"] == 401
            and evidence["accountRefreshReuseDetection"]["rotatedSessionRejectedAfterReplayStatus"] == 401
            and evidence["accountRefreshReuseDetection"]["auditLogged"] is True,
            "account_registration_throttle": evidence["accountRegistrationThrottle"]["providerStatus"] is True
            and evidence["accountRegistrationThrottle"]["statuses"] == [200, 429]
            and evidence["accountRegistrationThrottle"]["auditLogged"] is True,
            "account_password_spray_risk_control": evidence["accountPasswordSprayRiskControl"]["providerStatus"] is True
            and evidence["accountPasswordSprayRiskControl"]["riskBasedProviderStatus"] is True
            and evidence["accountPasswordSprayRiskControl"]["failedStatuses"] == [401, 401]
            and evidence["accountPasswordSprayRiskControl"]["blockedStatus"] == 429
            and evidence["accountPasswordSprayRiskControl"]["auditLogged"] is True,
            "account_auth_hardening": all(evidence["accountAuthHardening"].values()),
            "mock_no_key_mode": evidence["providers"]["externalApiKeysRequired"] is False,
            "external_provider_readiness_harness": evidence["externalProviderReadiness"]["passed"] is True
            and evidence["externalProviderReadiness"]["realCallsEnabled"] is False
            and evidence["externalProviderReadiness"]["realProviderEvidenceComplete"] is False
            and evidence["externalProviderReadiness"]["secretsReturned"] is False
            and set(evidence["externalProviderReadiness"]["checks"].keys())
            == {
                "oidc_discovery",
                "llm_strict_json_schema",
                "tts_media_compatibility",
                "stt_media_compatibility",
                "production_pronunciation_provider",
            },
            "redis_rate_limit_readiness_harness": evidence["redisRateLimitReadiness"]["passed"] is True
            and evidence["redisRateLimitReadiness"]["realCallsEnabled"] is False
            and evidence["redisRateLimitReadiness"]["redisUrlConfigured"] is False
            and evidence["redisRateLimitReadiness"]["redisUrlReturned"] is False
            and evidence["redisRateLimitReadiness"]["secretsReturned"] is False
            and evidence["redisRateLimitReadiness"]["realRedisEvidenceComplete"] is False
            and evidence["redisRateLimitReadiness"]["checks"]["redis_fallback_secret_redaction"]["status"] in {"passed", "skipped"}
            and evidence["redisRateLimitReadiness"]["checks"]["redis_live_ping"]["status"] == "skipped"
            and evidence["redisRateLimitReadiness"]["checks"]["redis_distributed_counter"]["status"] == "skipped"
            and evidence["redisRateLimitReadiness"]["checks"]["redis_light_load"]["status"] == "skipped",
            "hosted_scheduler_readiness_harness": evidence["hostedSchedulerReadiness"]["passed"] is True
            and evidence["hostedSchedulerReadiness"]["realCallsEnabled"] is False
            and evidence["hostedSchedulerReadiness"]["localSchedulerEvidenceComplete"] is True
            and evidence["hostedSchedulerReadiness"]["realHostedSchedulerEvidenceComplete"] is False
            and evidence["hostedSchedulerReadiness"]["hostedSchedulerValuesReturned"] is False
            and evidence["hostedSchedulerReadiness"]["secretsReturned"] is False
            and evidence["hostedSchedulerReadiness"]["checks"]["local_api_scheduler_tick"]["status"] == "passed"
            and evidence["hostedSchedulerReadiness"]["checks"]["local_api_scheduler_tick"]["releaseAppliedCount"] == 1
            and evidence["hostedSchedulerReadiness"]["checks"]["local_api_scheduler_tick"]["operationJobsRunCount"] == 1
            and evidence["hostedSchedulerReadiness"]["checks"]["local_api_scheduler_tick"]["runHistoryContainsRun"] is True
            and evidence["hostedSchedulerReadiness"]["checks"]["hosted_scheduler_env_redaction"]["status"] == "passed"
            and evidence["hostedSchedulerReadiness"]["checks"]["hosted_scheduler_health"]["status"] == "skipped"
            and evidence["hostedSchedulerReadiness"]["checks"]["hosted_scheduler_run_once"]["status"] == "skipped",
            "conversation_vertical_slice": evidence["spokenText"] == "今日めっちゃ疲れた。",
            "course_unit_lesson_catalog": evidence["courses"]["count"] >= 2 and evidence["courses"]["practiceRoomRefs"] >= 50,
            "content_authoring_validation": evidence["contentAuthoring"]["qualityReportValid"] is True
            and evidence["contentAuthoring"]["validationValid"] is True
            and evidence["contentAuthoring"]["dryRun"] is True
            and evidence["contentAuthoring"]["applied"] is False
            and evidence["contentAuthoring"]["dryRunVersionStatus"] == "draft"
            and evidence["contentAuthoring"]["roomsWithCoursePlacement"] >= 50,
            "content_versioned_publishing": evidence["contentVersionedPublishing"]["providerStatus"] is True
            and evidence["contentVersionedPublishing"]["roleBasedReviewProviderStatus"] is True
            and evidence["contentVersionedPublishing"]["approvalRequiredProviderStatus"] is True
            and evidence["contentVersionedPublishing"]["listContainsVersion"] is True
            and evidence["contentVersionedPublishing"]["detailHasCourseSnapshot"] is True
            and evidence["contentVersionedPublishing"]["directPublishRejectedStatus"] == 409
            and evidence["contentVersionedPublishing"]["viewerApproveRejectedStatus"] == 403
            and evidence["contentVersionedPublishing"]["submittedStatus"] == "in_review"
            and evidence["contentVersionedPublishing"]["submittedBy"] == "benchmark-editor"
            and evidence["contentVersionedPublishing"]["approvedStatus"] == "approved"
            and evidence["contentVersionedPublishing"]["reviewedBy"] == "benchmark-reviewer"
            and evidence["contentVersionedPublishing"]["publishOk"] is True
            and evidence["contentVersionedPublishing"]["publishedStatus"] == "published"
            and evidence["contentVersionedPublishing"]["publishedAtPresent"] is True
            and evidence["contentVersionedPublishing"]["auditLogged"] is True
            and evidence["contentVersionedPublishing"]["reviewAuditLogged"] is True,
            "content_release_automation": evidence["contentReleaseAutomation"]["releasePlansProviderStatus"] is True
            and evidence["contentReleaseAutomation"]["releaseSchedulingProviderStatus"] is True
            and evidence["contentReleaseAutomation"]["canaryMetadataProviderStatus"] is True
            and evidence["contentReleaseAutomation"]["releaseWorkerProviderStatus"] is True
            and evidence["contentReleaseAutomation"]["releaseRollbackProviderStatus"] is True
            and evidence["contentReleaseAutomation"]["unapprovedReleaseRejectedStatus"] == 409
            and evidence["contentReleaseAutomation"]["viewerCreateRejectedStatus"] == 403
            and evidence["contentReleaseAutomation"]["releaseStrategy"] == "canary"
            and evidence["contentReleaseAutomation"]["rolloutPercent"] == 25
            and evidence["contentReleaseAutomation"]["qualityGuardrailValid"] is True
            and evidence["contentReleaseAutomation"]["editorApplyRejectedStatus"] == 403
            and evidence["contentReleaseAutomation"]["futureApplyRejectedStatus"] == 409
            and evidence["contentReleaseAutomation"]["appliedStatus"] == "applied"
            and evidence["contentReleaseAutomation"]["previousPublishedVersionId"] == content_version_id
            and evidence["contentReleaseAutomation"]["liveTitleAfterApply"].endswith("release candidate")
            and evidence["contentReleaseAutomation"]["rolledBackStatus"] == "rolled_back"
            and evidence["contentReleaseAutomation"]["rollbackNote"] == "benchmark rollback"
            and evidence["contentReleaseAutomation"]["liveTitleAfterRollback"] == original_release_course_title
            and evidence["contentReleaseAutomation"]["workerReleaseStatusBeforeRun"] == "scheduled"
            and evidence["contentReleaseAutomation"]["workerEditorRejectedStatus"] == 403
            and evidence["contentReleaseAutomation"]["workerAppliedCount"] == 1
            and evidence["contentReleaseAutomation"]["workerSkippedCount"] == 0
            and evidence["contentReleaseAutomation"]["workerAppliedReleaseStatus"] == "applied"
            and evidence["contentReleaseAutomation"]["liveTitleAfterWorkerRun"].endswith("worker release")
            and evidence["contentReleaseAutomation"]["listContainsRelease"] is True
            and evidence["contentReleaseAutomation"]["listContainsWorkerRelease"] is True
            and evidence["contentReleaseAutomation"]["auditLogged"] is True,
            "content_operation_jobs": evidence["contentOperationJobs"]["operationJobsProviderStatus"] is True
            and evidence["contentOperationJobs"]["operationJobRunnerProviderStatus"] is True
            and evidence["contentOperationJobs"]["urgentJobFirst"] is True
            and evidence["contentOperationJobs"]["viewerRunRejectedStatus"] == 403
            and evidence["contentOperationJobs"]["runOk"] is True
            and evidence["contentOperationJobs"]["runJobStatus"] == "succeeded"
            and evidence["contentOperationJobs"]["runJobType"] == "import_bundle"
            and evidence["contentOperationJobs"]["runResultOk"] is True
            and evidence["contentOperationJobs"]["runResultVersionSource"] == "content_operation_import_dry_run"
            and evidence["contentOperationJobs"]["detailStatus"] == "succeeded"
            and evidence["contentOperationJobs"]["canceledStatus"] == "canceled"
            and evidence["contentOperationJobs"]["auditLogged"] is True,
            "content_managed_scheduler": evidence["contentManagedScheduler"]["managedSchedulerProviderStatus"] is True
            and evidence["contentManagedScheduler"]["schedulerRunHistoryProviderStatus"] is True
            and evidence["contentManagedScheduler"]["viewerRunRejectedStatus"] == 403
            and evidence["contentManagedScheduler"]["runOk"] is True
            and evidence["contentManagedScheduler"]["runStatus"] == "succeeded"
            and evidence["contentManagedScheduler"]["leaseOwner"] == "benchmark-content-scheduler"
            and evidence["contentManagedScheduler"]["releaseAppliedCount"] == 1
            and evidence["contentManagedScheduler"]["releaseAppliedId"] == evidence["contentManagedScheduler"]["scheduledReleaseId"]
            and evidence["contentManagedScheduler"]["operationJobsRunCount"] == 1
            and evidence["contentManagedScheduler"]["operationJobId"] == evidence["contentManagedScheduler"]["queuedJobId"]
            and evidence["contentManagedScheduler"]["operationJobStatus"] == "succeeded"
            and evidence["contentManagedScheduler"]["runHistoryContainsRun"] is True
            and evidence["contentManagedScheduler"]["liveTitleAfterSchedulerRun"].endswith("managed scheduler")
            and evidence["contentManagedScheduler"]["listContainsSchedulerRelease"] is True
            and evidence["contentManagedScheduler"]["auditLogged"] is True,
            "content_ops_console": evidence["contentOpsConsole"]["providerStatus"] is True
            and evidence["contentOpsConsole"]["actionConsoleProviderStatus"] is True
            and evidence["contentOpsConsole"]["forbiddenStatus"] == 403
            and evidence["contentOpsConsole"]["status"] == 200
            and "text/html" in evidence["contentOpsConsole"]["contentType"]
            and evidence["contentOpsConsole"]["hasOpsTitle"] is True
            and evidence["contentOpsConsole"]["hasActionConsole"] is True
            and evidence["contentOpsConsole"]["hasRunDueReleaseAction"] is True
            and evidence["contentOpsConsole"]["hasSchedulerAction"] is True
            and evidence["contentOpsConsole"]["hasRunNextJobAction"] is True
            and evidence["contentOpsConsole"]["hasActionResultPanel"] is True
            and evidence["contentOpsConsole"]["hasSchedulerLeaseOwner"] is True
            and evidence["contentOpsConsole"]["hasManagedSchedulerRelease"] is True
            and evidence["contentOpsConsole"]["hasSchedulerAuditEvent"] is True,
            "content_authoring_console": evidence["contentAuthoringConsole"]["providerStatus"] is True
            and evidence["contentAuthoringConsole"]["forbiddenStatus"] == 403
            and evidence["contentAuthoringConsole"]["status"] == 200
            and "text/html" in evidence["contentAuthoringConsole"]["contentType"]
            and evidence["contentAuthoringConsole"]["hasContentTitle"] is True
            and evidence["contentAuthoringConsole"]["hasAuthoringActionConsole"] is True
            and evidence["contentAuthoringConsole"]["hasValidateAction"] is True
            and evidence["contentAuthoringConsole"]["hasImportAction"] is True
            and evidence["contentAuthoringConsole"]["hasBulkQaAction"] is True
            and evidence["contentAuthoringConsole"]["hasTranslationMemorySuggestAction"] is True
            and evidence["contentAuthoringConsole"]["hasTranslationMemoryUpsertAction"] is True
            and evidence["contentAuthoringConsole"]["hasBranchAction"] is True
            and evidence["contentAuthoringConsole"]["hasAssignAction"] is True
            and evidence["contentAuthoringConsole"]["hasActionResultPanel"] is True
            and evidence["contentAuthoringConsole"]["hasCurrentVersionId"] is True,
            "content_translation_memory_bulk_qa": evidence["contentTranslationMemoryBulkQa"]["translationMemoryProviderStatus"] is True
            and evidence["contentTranslationMemoryBulkQa"]["bulkQaProviderStatus"] is True
            and evidence["contentTranslationMemoryBulkQa"]["translationMemoryEntryCount"] >= len(PRACTICE_ROOMS)
            and evidence["contentTranslationMemoryBulkQa"]["seedExactSuggestionFound"] is True
            and evidence["contentTranslationMemoryBulkQa"]["customUpsertOk"] is True
            and evidence["contentTranslationMemoryBulkQa"]["customUpsertCount"] == 1
            and evidence["contentTranslationMemoryBulkQa"]["currentBulkQaOk"] is True
            and evidence["contentTranslationMemoryBulkQa"]["currentBulkQaSource"] == "current"
            and evidence["contentTranslationMemoryBulkQa"]["currentExactMatches"] >= 50
            and evidence["contentTranslationMemoryBulkQa"]["currentConflictCount"] == 0
            and evidence["contentTranslationMemoryBulkQa"]["conflictBulkQaOk"] is True
            and evidence["contentTranslationMemoryBulkQa"]["conflictCount"] >= 1
            and "translation_memory_target_conflict" in evidence["contentTranslationMemoryBulkQa"]["conflictIssueCodes"]
            and evidence["contentTranslationMemoryBulkQa"]["auditLogged"] is True,
            "content_branching_assignments": evidence["contentBranchingAssignments"]["providerStatus"] is True
            and evidence["contentBranchingAssignments"]["branchOk"] is True
            and evidence["contentBranchingAssignments"]["branchStatus"] == "draft"
            and evidence["contentBranchingAssignments"]["branchSource"] == "content_branch"
            and evidence["contentBranchingAssignments"]["parentVersionId"] == content_version_id
            and evidence["contentBranchingAssignments"]["branchName"] == "benchmark-copy-branch"
            and evidence["contentBranchingAssignments"]["assignmentAssignee"] == "benchmark-writer"
            and evidence["contentBranchingAssignments"]["assignmentPriority"] == "high"
            and evidence["contentBranchingAssignments"]["listContainsAssignment"] is True
            and evidence["contentBranchingAssignments"]["viewerAssignRejectedStatus"] == 403
            and evidence["contentBranchingAssignments"]["reassignedAssignee"] == "benchmark-writer-2"
            and evidence["contentBranchingAssignments"]["reassignedPriority"] == "urgent"
            and evidence["contentBranchingAssignments"]["doneStatus"] == "done"
            and evidence["contentBranchingAssignments"]["doneCompletedAtPresent"] is True
            and evidence["contentBranchingAssignments"]["auditLogged"] is True,
            "experiment_stable_assignment_and_exposure": evidence["experimentStableAssignmentAndExposure"]["providerStableAssignments"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerWeightedVariants"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerExposureLogging"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerConversionEventLogging"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerAdminControls"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerAnalyticsDashboard"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerVariantAnalytics"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerDecisionConsole"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerDecisionActionConsole"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerDecisionReadinessGuard"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerStatisticalTesting"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerDecisionWorkflow"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerDecisionGuardrails"] is True
            and evidence["experimentStableAssignmentAndExposure"]["providerWinnerRolloutApplication"] is True
            and {"daily_recommendation_copy_v1", "practice_room_order_v1"}
            <= set(evidence["experimentStableAssignmentAndExposure"]["seededExperimentKeys"])
            and evidence["experimentStableAssignmentAndExposure"]["assignmentCount"] >= 2
            and evidence["experimentStableAssignmentAndExposure"]["stableRepeat"] is True
            and evidence["experimentStableAssignmentAndExposure"]["exposureEventIdPresent"] is True
            and evidence["experimentStableAssignmentAndExposure"]["conversionOk"] is True
            and evidence["experimentStableAssignmentAndExposure"]["analyticsForbiddenStatus"] == 403
            and evidence["experimentStableAssignmentAndExposure"]["analyticsExperimentKey"] == "daily_recommendation_copy_v1"
            and evidence["experimentStableAssignmentAndExposure"]["analyticsAssignmentCount"] >= 1
            and evidence["experimentStableAssignmentAndExposure"]["analyticsExposureEventCount"] >= 2
            and evidence["experimentStableAssignmentAndExposure"]["analyticsConversionEventCount"] == 1
            and evidence["experimentStableAssignmentAndExposure"]["analyticsBestObservedVariantKey"]
            == evidence["experimentStableAssignmentAndExposure"]["conversionVariant"]
            and evidence["experimentStableAssignmentAndExposure"]["analyticsDecisionReady"] is False
            and evidence["experimentStableAssignmentAndExposure"]["analyticsWinnerVariantKey"] is None
            and evidence["experimentStableAssignmentAndExposure"]["analyticsConvertedVariantExposedLearners"] >= 1
            and evidence["experimentStableAssignmentAndExposure"]["analyticsConvertedVariantConversions"] == 1
            and evidence["experimentStableAssignmentAndExposure"]["analyticsConvertedVariantRate"] >= 1.0
            and evidence["experimentStableAssignmentAndExposure"]["viewerCreateRejectedStatus"] == 403
            and evidence["experimentStableAssignmentAndExposure"]["createdExperimentKey"] == "benchmark_experiment_v1"
            and evidence["experimentStableAssignmentAndExposure"]["createdExperimentStatus"] == "running"
            and evidence["experimentStableAssignmentAndExposure"]["createdExperimentAssigned"] is True
            and {"control", "test"} <= set(evidence["experimentStableAssignmentAndExposure"]["statisticalObservedVariants"])
            and evidence["experimentStableAssignmentAndExposure"]["statisticalControlVariantKey"] == "control"
            and evidence["experimentStableAssignmentAndExposure"]["statisticalDecisionReady"] is True
            and evidence["experimentStableAssignmentAndExposure"]["statisticalDecisionRecommendation"]
            in {"no_statistically_significant_winner", "promote_winner"}
            and evidence["experimentStableAssignmentAndExposure"]["statisticalAlpha"] == 0.05
            and (
                evidence["experimentStableAssignmentAndExposure"]["statisticalTestVariantPValue"] is None
                or 0 <= evidence["experimentStableAssignmentAndExposure"]["statisticalTestVariantPValue"] <= 1
            )
            and evidence["experimentStableAssignmentAndExposure"]["statisticalTestVariantLift"] is not None
            and set(evidence["experimentStableAssignmentAndExposure"]["statisticalTestVariantConfidenceInterval"].keys())
            == {"lower", "upper"}
            and evidence["experimentStableAssignmentAndExposure"]["statisticalControlLift"] == 0.0
            and evidence["experimentStableAssignmentAndExposure"]["statisticalNotesContainZTest"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionRejectedStatus"] == 409
            and evidence["experimentStableAssignmentAndExposure"]["decisionProposalOk"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionProposalAction"] == "promote_variant"
            and evidence["experimentStableAssignmentAndExposure"]["decisionProposalVariant"] == "test"
            and evidence["experimentStableAssignmentAndExposure"]["decisionGuardrailOk"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionListed"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionApplyEditorRejectedStatus"] == 403
            and evidence["experimentStableAssignmentAndExposure"]["decisionAppliedStatus"] == "applied"
            and evidence["experimentStableAssignmentAndExposure"]["decisionAppliedExperimentStatus"] == "running"
            and evidence["experimentStableAssignmentAndExposure"]["decisionAppliedWeights"] == {"control": 0, "test": 1000}
            and evidence["experimentStableAssignmentAndExposure"]["decisionAppliedRolloutVariant"] == "test"
            and evidence["experimentStableAssignmentAndExposure"]["decisionPostApplyAssignedVariant"] == "test"
            and evidence["experimentStableAssignmentAndExposure"]["decisionApplyReplayStatus"] == 409
            and evidence["experimentStableAssignmentAndExposure"]["pausedStatus"] == "paused"
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleForbiddenStatus"] == 403
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleStatus"] == 200
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleMissingStatus"] == 404
            and "text/html" in evidence["experimentStableAssignmentAndExposure"]["decisionConsoleContentType"]
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasTitle"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasActionConsole"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasUpsertAction"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasStatusAction"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasProposeAction"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasApplyAction"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasActionResultPanel"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasExperimentKey"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasVariant"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasDecisionId"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasDecisionAction"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionConsoleHasAppliedAudit"] is True
            and evidence["experimentStableAssignmentAndExposure"]["auditLogged"] is True
            and evidence["experimentStableAssignmentAndExposure"]["decisionAuditLogged"] is True,
            "pronunciation_feedback": evidence["pronunciationScore"] >= 90,
            "acoustic_pronunciation_adapter": evidence["acousticPronunciation"]["acousticEvidencePresent"] is True,
            "llm_multi_repair_policy": evidence["llmMultiRepairPolicy"]["repairAttempts"] == 2
            and evidence["llmMultiRepairPolicy"]["postCalls"] == 3
            and evidence["llmMultiRepairPolicy"]["providerWarning"] == "openai_compatible_repaired_structured_output"
            and evidence["llmMultiRepairPolicy"]["spokenText"] == "今日はかなり疲れた。",
            "srs_due_queue": evidence["dueCards"] >= 1,
            "memory_summary": evidence["memorySummary"]["cardCount"] >= 1
            and evidence["memorySummary"]["model"] == "hlr_inspired_local_estimator_v1"
            and evidence["memoryCard"]["memoryStrengthDays"] is not None,
            "offline_learner_model_evaluation": evidence["learnerModelEvaluation"]["providerOfflinePipeline"] is True
            and evidence["learnerModelEvaluation"]["providerOfflineModelName"] == "offline_logistic_memory_model_v1"
            and evidence["learnerModelEvaluation"]["providerProductionTrainedModel"] is False
            and evidence["learnerModelEvaluation"]["status"] == "evaluated"
            and evidence["learnerModelEvaluation"]["dbExampleCount"] >= 1
            and evidence["learnerModelEvaluation"]["fixtureExampleCount"] > 0
            and evidence["learnerModelEvaluation"]["trainCount"] > 0
            and evidence["learnerModelEvaluation"]["evaluationExampleCount"] > 0
            and evidence["learnerModelEvaluation"]["accuracy"] is not None
            and evidence["learnerModelEvaluation"]["productionTrained"] is False,
            "gamified_progress_streak_quests": evidence["gamifiedProgress"]["providerXpLedger"] is True
            and evidence["gamifiedProgress"]["providerStreaks"] is True
            and evidence["gamifiedProgress"]["providerDailyQuests"] is True
            and evidence["gamifiedProgress"]["providerWeeklyLeaderboard"] is True
            and evidence["gamifiedProgress"]["providerAntiDuplicateXpEvents"] is True
            and evidence["gamifiedProgress"]["providerAchievements"] is True
            and evidence["gamifiedProgress"]["providerAchievementLevels"] is True
            and evidence["gamifiedProgress"]["providerAchievementRewardCurrency"] is True
            and evidence["gamifiedProgress"]["providerLeagueTiers"] is True
            and evidence["gamifiedProgress"]["providerXpAnomalyFlags"] is True
            and evidence["gamifiedProgress"]["providerFriendQuests"] is True
            and evidence["gamifiedProgress"]["providerFriendGraph"] is True
            and evidence["gamifiedProgress"]["providerFriendInvites"] is True
            and evidence["gamifiedProgress"]["providerFriendRecommendations"] is True
            and evidence["gamifiedProgress"]["providerSocialDiscovery"] is True
            and evidence["gamifiedProgress"]["providerSocialPrivacySettings"] is True
            and evidence["gamifiedProgress"]["providerSocialBlocking"] is True
            and evidence["gamifiedProgress"]["providerRewardCurrencyLedger"] is True
            and evidence["gamifiedProgress"]["providerRewardShop"] is True
            and evidence["gamifiedProgress"]["providerRewardShopOperations"] is True
            and evidence["gamifiedProgress"]["providerRewardShopPurchaseLimits"] is True
            and evidence["gamifiedProgress"]["providerRewardInventory"] is True
            and evidence["gamifiedProgress"]["providerXpBoosts"] is True
            and evidence["gamifiedProgress"]["providerBoostedXpLedger"] is True
            and evidence["gamifiedProgress"]["providerSingleSourceAnomalyFlags"] is True
            and evidence["gamifiedProgress"]["providerBoostAbuseFlags"] is True
            and evidence["gamifiedProgress"]["providerDuplicatePayloadAbuseFlags"] is True
            and evidence["gamifiedProgress"]["providerLeaderboardExclusionFlags"] is True
            and evidence["gamifiedProgress"]["providerXpAbuseReviewQueue"] is True
            and evidence["gamifiedProgress"]["providerMultiSignalReputation"] is True
            and evidence["gamifiedProgress"]["providerReputationReviewQueue"] is True
            and evidence["gamifiedProgress"]["providerOfflineReputationModelEvaluation"] is True
            and evidence["gamifiedProgress"]["providerProductionLearnedAntiCheatModel"] is False
            and evidence["gamifiedProgress"]["todayXp"] >= evidence["gamifiedProgress"]["beforeBoostTodayXp"] + 30
            and evidence["gamifiedProgress"]["totalXp"] >= evidence["gamifiedProgress"]["todayXp"]
            and evidence["gamifiedProgress"]["currentStreak"] >= 1
            and evidence["gamifiedProgress"]["isActiveToday"] is True
            and {"complete_practice_turn", "review_one_card", "earn_30_xp"}
            <= set(evidence["gamifiedProgress"]["completedQuestKeys"])
            and evidence["gamifiedProgress"]["friendInviteCreated"] is True
            and evidence["gamifiedProgress"]["friendInviteOutgoingCountBeforeAccept"] == 1
            and evidence["gamifiedProgress"]["friendInviteAccepted"] is True
            and evidence["gamifiedProgress"]["friendCountAfterAccept"] == 1
            and evidence["gamifiedProgress"]["friendGraphContainsPartner"] is True
            and evidence["gamifiedProgress"]["pendingFriendInviteCreated"] is True
            and evidence["gamifiedProgress"]["friendRecommendationContainsCandidate"] is True
            and evidence["gamifiedProgress"]["friendRecommendationExcludesAcceptedFriend"] is True
            and evidence["gamifiedProgress"]["friendRecommendationExcludesPendingInvite"] is True
            and evidence["gamifiedProgress"]["friendRecommendationExcludedFriendCount"] >= 1
            and evidence["gamifiedProgress"]["friendRecommendationExcludedPendingInviteCount"] >= 1
            and "target_language_match" in evidence["gamifiedProgress"]["friendRecommendationReasonCodes"]
            and evidence["gamifiedProgress"]["friendRecommendationScore"] > 0
            and evidence["gamifiedProgress"]["socialSettingsDiscoverable"] is True
            and evidence["gamifiedProgress"]["privateSocialSettingsDiscoverable"] is False
            and evidence["gamifiedProgress"]["privateSocialSettingsAllowsInvites"] is False
            and evidence["gamifiedProgress"]["socialBlockCreated"] is True
            and evidence["gamifiedProgress"]["socialBlockCount"] >= 1
            and evidence["gamifiedProgress"]["blockedInviteStatus"] == 409
            and evidence["gamifiedProgress"]["blockedInviteReason"] == "blocked"
            and evidence["gamifiedProgress"]["socialDiscoveryContainsCandidate"] is True
            and evidence["gamifiedProgress"]["socialDiscoveryExcludesAcceptedFriend"] is True
            and evidence["gamifiedProgress"]["socialDiscoveryExcludesPendingInvite"] is True
            and evidence["gamifiedProgress"]["socialDiscoveryExcludesPrivate"] is True
            and evidence["gamifiedProgress"]["socialDiscoveryExcludesBlocked"] is True
            and evidence["gamifiedProgress"]["socialDiscoveryExcludedPrivateCount"] >= 1
            and evidence["gamifiedProgress"]["socialDiscoveryExcludedBlockedCount"] >= 1
            and evidence["gamifiedProgress"]["socialDiscoveryExcludedFriendOrPendingCount"] >= 2
            and "target_language_match" in evidence["gamifiedProgress"]["socialDiscoveryReasonCodes"]
            and evidence["gamifiedProgress"]["socialDiscoveryCanInvite"] is True
            and evidence["gamifiedProgress"]["friendRecommendationExcludesPrivate"] is True
            and evidence["gamifiedProgress"]["friendRecommendationExcludesBlocked"] is True
            and evidence["gamifiedProgress"]["friendRecommendationExcludedPrivateCount"] >= 1
            and evidence["gamifiedProgress"]["friendRecommendationExcludedBlockedCount"] >= 1
            and evidence["gamifiedProgress"]["rewardShopAdminCount"] >= 2
            and evidence["gamifiedProgress"]["rewardShopViewerUpdateStatus"] == 403
            and evidence["gamifiedProgress"]["rewardShopAdminUpdated"] is True
            and evidence["gamifiedProgress"]["rewardShopUpdatedBy"] == "benchmark-editor"
            and evidence["gamifiedProgress"]["rewardShopDailyPurchaseLimit"] == 1
            and evidence["gamifiedProgress"]["rewardShopInventoryLimit"] == 1
            and evidence["gamifiedProgress"]["shopGemBalanceBeforePurchase"] >= 2
            and evidence["gamifiedProgress"]["shopStreakFreezeRemainingBeforePurchase"] == 1
            and evidence["gamifiedProgress"]["shopPurchaseSucceeded"] is True
            and evidence["gamifiedProgress"]["shopPurchaseRewardKey"] == "streak_freeze_1"
            and evidence["gamifiedProgress"]["shopGemBalanceAfterPurchase"] == evidence["gamifiedProgress"]["shopGemBalanceBeforePurchase"] - 2
            and evidence["gamifiedProgress"]["shopStreakFreezeRemainingAfterPurchase"] == 0
            and evidence["gamifiedProgress"]["shopSecondPurchaseStatus"] == 409
            and evidence["gamifiedProgress"]["shopSecondPurchaseReason"] == "daily_purchase_limit_reached"
            and evidence["gamifiedProgress"]["friendQuestCompleted"] is True
            and evidence["gamifiedProgress"]["friendQuestCombinedXp"] >= 40
            and evidence["gamifiedProgress"]["friendQuestClaimed"] is True
            and evidence["gamifiedProgress"]["friendQuestClaimIdempotent"] is True
            and evidence["gamifiedProgress"]["rewardKey"] == "xp_boost_2x_15m"
            and evidence["gamifiedProgress"]["boostActivated"] is True
            and evidence["gamifiedProgress"]["boostMultiplier"] == 2.0
            and evidence["gamifiedProgress"]["activeBoostCount"] >= 1
            and evidence["gamifiedProgress"]["inventoryQuantityAfterActivation"] == 0
            and evidence["gamifiedProgress"]["inventoryHasStreakFreeze"] is True
            and evidence["gamifiedProgress"]["leagueTier"] in {"silver", "gold", "sapphire", "ruby"}
            and evidence["gamifiedProgress"]["achievementAwardedCount"] >= 7
            and evidence["gamifiedProgress"]["achievementTotalCount"] >= 12
            and evidence["gamifiedProgress"]["achievementTrackCount"] >= 7
            and evidence["gamifiedProgress"]["achievementXpRookieMaxLevel"] >= 3
            and {1, 2, 3} <= set(evidence["gamifiedProgress"]["achievementXpRookieLevels"])
            and evidence["gamifiedProgress"]["achievementRewardGemsAvailable"] >= 18
            and {"first_steps", "review_rookie", "xp_rookie", "quest_kickoff", "social_starter", "friend_quester"}
            <= set(evidence["gamifiedProgress"]["awardedAchievementKeys"])
            and "daily_xp_soft_limit_exceeded" in evidence["gamifiedProgress"]["xpAbuseFlagReasons"]
            and "boosted_xp_soft_limit_exceeded" in evidence["gamifiedProgress"]["xpAbuseFlagReasons"]
            and evidence["gamifiedProgress"]["boostedXpFlagStatus"] == "open"
            and evidence["gamifiedProgress"]["boostedXpFlagLeaderboardExcluded"] is True
            and evidence["gamifiedProgress"]["adminXpFlagsCount"] >= 1
            and evidence["gamifiedProgress"]["adminXpFlagsContainsBoostedFlag"] is True
            and evidence["gamifiedProgress"]["reputationRiskScore"] >= 45
            and evidence["gamifiedProgress"]["reputationRiskBand"] in {"high", "critical"}
            and evidence["gamifiedProgress"]["reputationReviewRecommended"] is True
            and evidence["gamifiedProgress"]["reputationLeaderboardEligible"] is False
            and "xp_abuse:boosted_xp_soft_limit_exceeded" in evidence["gamifiedProgress"]["reputationSignalKeys"]
            and evidence["gamifiedProgress"]["reputationOpenXpAbuseFlagCount"] >= 2
            and evidence["gamifiedProgress"]["reputationBlockingXpAbuseFlagCount"] >= 1
            and evidence["gamifiedProgress"]["reputationWeekXp"] >= evidence["gamifiedProgress"]["todayXp"]
            and evidence["gamifiedProgress"]["adminReputationQueueCount"] >= 1
            and evidence["gamifiedProgress"]["adminReputationQueueContainsLearner"] is True
            and evidence["gamifiedProgress"]["adminReputationDetailMatchesScore"] is True
            and evidence["gamifiedProgress"]["reputationModelStatus"] == "evaluated"
            and evidence["gamifiedProgress"]["reputationModelName"] == "offline_logistic_reputation_model_v1"
            and evidence["gamifiedProgress"]["reputationModelDbExampleCount"] >= 2
            and evidence["gamifiedProgress"]["reputationModelFixtureExampleCount"] >= 8
            and evidence["gamifiedProgress"]["reputationModelTrainCount"] >= 5
            and evidence["gamifiedProgress"]["reputationModelEvaluation"]["exampleCount"] >= 1
            and evidence["gamifiedProgress"]["reputationModelProductionTrained"] is False
            and evidence["gamifiedProgress"]["reviewedBoostedXpFlag"] is True
            and evidence["gamifiedProgress"]["reviewedBoostedXpFlagStatus"] == "resolved"
            and evidence["gamifiedProgress"]["leaderboardExcludedBeforeReview"] is True
            and "boosted_xp_soft_limit_exceeded" in evidence["gamifiedProgress"]["leaderboardExclusionReasonsBeforeReview"]
            and evidence["gamifiedProgress"]["leaderboardCurrentRank"] is None
            and evidence["gamifiedProgress"]["leaderboardExcludedAfterReview"] is False
            and evidence["gamifiedProgress"]["leaderboardRestoredRankAfterReview"] == 1
            and evidence["gamifiedProgress"]["leaderboardTopLearner"] == "benchmark",
            "jlpt_grammar_bank": evidence["grammarN5"] >= 2,
            "expanded_grammar_dataset": evidence["grammarTotal"] >= 16,
            "korean_mistake_catalog": evidence["mistakePatterns"] >= 13,
            "anki_csv_export": evidence["ankiCsv"] == "csv",
            "anki_apkg_export": evidence["ankiApkgBytes"] > 1000,
            "profile_recommendations": evidence["recommendations"] >= 1,
            "usage_tracking": evidence["usage"]["usageRecords"] >= 1,
            "docker_artifact_static_verification": evidence["dockerArtifactVerification"]["staticVerificationPassed"] is True,
            "docker_runtime_smoke_harness": evidence["dockerArtifactVerification"]["passed"] is True
            and evidence["dockerArtifactVerification"]["runtimeSmokeEnabled"] is False
            and evidence["dockerArtifactVerification"]["runtimeBuildExecuted"] is False
            and evidence["dockerArtifactVerification"]["runtimeContainerExecuted"] is False
            and evidence["dockerArtifactVerification"]["runtimeEvidenceComplete"] is False
            and evidence["dockerArtifactVerification"]["runtimeChecks"]["docker_image_build"]["status"] == "skipped"
            and evidence["dockerArtifactVerification"]["runtimeChecks"]["docker_container_run"]["status"] == "skipped"
            and evidence["dockerArtifactVerification"]["runtimeChecks"]["docker_health_endpoint"]["status"] == "skipped",
            "privacy_deletion": evidence["privacyDeletion"]["ok"] is True,
            "privacy_deletion_scoped_records": evidence["privacyDeletion"]["deletedCounts"]["conversations"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["friendQuests"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["friendInvites"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["friendRelationships"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["rewardCurrencyEvents"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["rewardShopPurchases"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["rewardInventoryItems"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["xpBoosts"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["socialSettings"] >= 1
            and evidence["privacyDeletion"]["deletedCounts"]["socialBlocks"] >= 1,
            "audit_logging": "privacy_deletion_completed" in evidence["auditLogActions"],
        }
        score = round(sum(1 for passed in checks.values() if passed) / len(checks) * 110)
        return {"score": score, "target": 105, "passed": all(checks.values()), "checks": checks, "evidence": evidence}


def _public_benchmark_result(result: dict) -> dict:
    return {
        "score": int(result.get("score", 0)),
        "target": int(result.get("target", 0)),
        "passed": bool(result.get("passed")),
        "checks": {str(key): bool(value) for key, value in result.get("checks", {}).items()},
    }


def main() -> int:
    result = run_benchmark()
    print(json.dumps(_public_benchmark_result(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["score"] >= result["target"] and result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
