from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import main
from app.main import create_app


def _admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "publisher"}


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "dev")
    monkeypatch.delenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", raising=False)
    return TestClient(create_app(tmp_path / "security.sqlite3"))


def test_anki_connect_allows_only_normalized_loopback_service() -> None:
    assert main._local_anki_connect_url("http://localhost:8765") == "http://127.0.0.1:8765/"
    assert main._local_anki_connect_url("http://[::1]:8765/") == "http://[::1]:8765/"

    for url in (
        "https://127.0.0.1:8765",
        "http://127.0.0.1:9000",
        "http://example.test:8765",
        "http://127.0.0.1:8765/proxy",
        "http://127.0.0.1:8765/?target=example.test",
        "http://127.0.0.1@evil.test:8765",
    ):
        with pytest.raises(HTTPException) as error:
            main._local_anki_connect_url(url)
        assert error.value.status_code == 400


def test_anki_connect_rejects_external_url_before_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(tmp_path, monkeypatch)

    def request_must_not_run(*args, **kwargs):
        raise AssertionError("external AnkiConnect URL was requested")

    monkeypatch.setattr(main, "_post_to_local_anki_connect", request_must_not_run)
    response = client.post(
        "/v1/export/anki-connect",
        json={"apply": True, "ankiConnectUrl": "http://example.test:8765"},
    )

    assert response.status_code == 400
    assert "local service" in response.json()["detail"]


def test_anki_connect_redirect_handler_never_follows_redirects() -> None:
    request = urllib.request.Request("http://127.0.0.1:8765/")
    assert main._NoRedirectHandler().redirect_request(request, None, 302, "Found", {}, "http://example.test/") is None


def test_anki_connect_disables_environment_proxies(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_handlers: list[object] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            return json.dumps({"result": [], "error": None}).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            assert request.full_url == "http://127.0.0.1:8765/"
            assert timeout == 10
            return FakeResponse()

    def fake_build_opener(*handlers):
        captured_handlers.extend(handlers)
        return FakeOpener()

    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.test:8080")
    monkeypatch.setattr(urllib.request, "build_opener", fake_build_opener)

    result = main._post_to_local_anki_connect("http://127.0.0.1:8765/", b"{}")

    proxy_handler = next(handler for handler in captured_handlers if isinstance(handler, urllib.request.ProxyHandler))
    assert proxy_handler.proxies == {}
    assert result == {"result": [], "error": None}


def test_filesystem_resource_paths_reject_traversal_and_symlink_escape(tmp_path: Path) -> None:
    assert main._safe_path_segment("aivis_まお_ノーマル_1", "voice identifier") == "aivis_まお_ノーマル_1"
    for value in ("..", "../secret", "voice.name", "voice\\name", " voice"):
        with pytest.raises(HTTPException) as error:
            main._safe_path_segment(value, "resource identifier")
        assert error.value.status_code == 400

    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"not-a-sample")
    (root / "sample.wav").symlink_to(outside)
    with pytest.raises(HTTPException) as error:
        main._resolve_contained_path(root, "sample.wav")
    assert error.value.status_code == 400


def test_email_hash_is_keyed_not_a_plain_fast_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    email = "learner@example.com"
    monkeypatch.setattr(main, "_EMAIL_HASH_KEY", b"test-email-hash-key")

    digest = main._email_hash(email)

    assert digest == main._email_hash(email)
    assert digest == hashlib.pbkdf2_hmac(
        "sha256",
        email.encode("utf-8"),
        b"test-email-hash-key",
        120_000,
        dklen=8,
    ).hex()
    assert digest != hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]
    assert main._default_account_learner_id(email) == f"learner_{digest}"


def test_content_worker_and_scheduler_errors_do_not_expose_exception_details(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    headers = _admin_headers()
    created = client.post(
        "/v1/content/operations/jobs",
        headers=headers,
        json={"jobType": "run_due_releases", "payload": {"limit": 1}},
    )
    assert created.status_code == 200

    def fail_worker(*args, **kwargs):
        raise RuntimeError("database password=not-for-clients")

    monkeypatch.setattr(client.app.state.store, "run_due_content_releases", fail_worker)
    worker = client.post(
        "/v1/content/operations/jobs/run-next",
        headers=headers,
        json={"confirmation": "run-next-content-operation-job"},
    )
    assert worker.status_code == 200
    assert worker.json()["error"] == "Content operation failed"
    assert worker.json()["job"]["error"] == "content_operation_failed"
    assert "database password" not in worker.text

    scheduler = client.post(
        "/v1/content/scheduler/run-once",
        headers=headers,
        json={"confirmation": "run-content-scheduler-once", "maxOperationJobs": 0},
    )
    assert scheduler.status_code == 200
    assert scheduler.json()["error"] == "Content scheduler failed"
    assert scheduler.json()["run"]["error"] == "content_scheduler_failed"
    assert "database password" not in scheduler.text


def test_rs256_jwk_signing_and_verification_use_cryptography_with_n_e_d_only() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = key.private_numbers()
    private_jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "n": main._b64url_encode(numbers.public_numbers.n.to_bytes(256, "big")),
        "e": main._b64url_encode(numbers.public_numbers.e.to_bytes(3, "big")),
        "d": main._b64url_encode(numbers.d.to_bytes(256, "big")),
    }
    public_jwk = {key: value for key, value in private_jwk.items() if key != "d"}

    signature = main._sign_rs256_with_jwk("header.payload", private_jwk)

    assert main._verify_rs256_with_jwk("header.payload", signature, public_jwk) is True
    assert main._verify_rs256_with_jwk("other.payload", signature, public_jwk) is False
