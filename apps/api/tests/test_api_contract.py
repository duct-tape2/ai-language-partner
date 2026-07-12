from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
os.environ.setdefault("AI_LANGUAGE_PARTNER_DB_PATH", str(Path(tempfile.gettempdir()) / "ai_language_partner_api_import.sqlite3"))

import scripts.verify_docker_smoke as docker_smoke
from app.main import create_app, create_oauth_authorization_code, create_oidc_id_token, create_oidc_rs256_id_token, create_signed_learner_token, _decode_account_access_jwt, _legacy_signed_learner_token, _sign_es256_with_jwk, _sign_rs256_with_jwk
from app.learner_model import fixture_examples, train_evaluate_memory_model
from app.paths import resolve_project_root
from app.providers import (
    STRUCTURED_TURN_SCHEMA_VERSION,
    OpenAICompatibleLLMProvider,
    OpenAISTTProvider,
    decode_audio_payload,
    _post_audio_transcription,
)
from app.seed import COURSE_CATALOG, PRACTICE_ROOMS
from scripts.verify_docker_smoke import python_multipart_requirement_check, verify_docker_smoke
from scripts.verify_external_provider_readiness import verify_external_provider_readiness
from scripts.verify_hosted_scheduler_readiness import verify_hosted_scheduler_readiness
from scripts.verify_redis_rate_limit_readiness import verify_redis_rate_limit_readiness


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "api.sqlite3"))


TEST_OIDC_RSA_JWK = {
    "kty": "RSA",
    "kid": "test-rs256-key",
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
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def webauthn_assertion(challenge: str, origin: str = "http://localhost:8000", rp_id: str = "localhost", flags: int = 0x01) -> dict:
    client_data = {
        "type": "webauthn.get",
        "challenge": b64url(challenge.encode("utf-8")),
        "origin": origin,
        "crossOrigin": False,
    }
    client_data_json = json.dumps(client_data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    authenticator_data = hashlib.sha256(rp_id.encode("utf-8")).digest() + bytes([flags]) + (7).to_bytes(4, "big")
    signed_message = authenticator_data + hashlib.sha256(client_data_json).digest()
    return {
        "algorithm": "webauthn-es256",
        "clientDataJSON": b64url(client_data_json),
        "authenticatorData": b64url(authenticator_data),
        "signature": _sign_es256_with_jwk(signed_message, TEST_WEBAUTHN_PRIVATE_JWK),
    }


def test_contract_paths_and_methods_are_implemented(tmp_path):
    app = create_app(tmp_path / "contract.sqlite3")
    route_methods = set()
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods or set():
                if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    route_methods.add((route.path, method.lower()))

    contract = yaml.safe_load((PROJECT_ROOT / "contracts" / "openapi_v0.yaml").read_text(encoding="utf-8"))
    for path, path_item in contract["paths"].items():
        for method in path_item:
            assert (path, method.lower()) in route_methods


def test_frontend_track_events_are_allowed_by_backend_contract():
    contract_events = yaml.safe_load(
        (PROJECT_ROOT / "contracts" / "events.yaml").read_text(encoding="utf-8")
    )["events"]
    assert len(contract_events) == len(set(contract_events))
    used_events = set()
    for source in (PROJECT_ROOT / "apps" / "mobile" / "src").rglob("*"):
        if source.suffix not in {".ts", ".tsx"}:
            continue
        text = source.read_text(encoding="utf-8")
        used_events.update(match.group(2) for match in re.finditer(r"app\.track\((['\"])([^'\"]+)\1", text))
    assert sorted(used_events - set(contract_events)) == []


def test_project_root_resolution_handles_local_and_docker_layouts():
    assert resolve_project_root(API_ROOT / "app" / "main.py") == PROJECT_ROOT
    assert resolve_project_root(Path("/app/app/main.py")) == Path("/app")


def test_external_provider_readiness_harness_skips_without_real_keys():
    result = verify_external_provider_readiness({"AI_LANGUAGE_PARTNER_EXTERNAL_SMOKE_REAL_CALLS": "0"})
    assert result["passed"] is True
    assert result["realCallsEnabled"] is False
    assert result["realProviderEvidenceComplete"] is False
    assert result["secretsReturned"] is False
    assert set(result["checks"]) == {
        "oidc_discovery",
        "llm_strict_json_schema",
        "tts_media_compatibility",
        "stt_media_compatibility",
        "production_pronunciation_provider",
    }
    assert all(check["status"] == "skipped" for check in result["checks"].values())
    assert all(item["valueReturned"] is False for item in result["env"])


def test_redis_rate_limit_readiness_harness_skips_without_redis_url():
    result = verify_redis_rate_limit_readiness({"AI_LANGUAGE_PARTNER_REDIS_SMOKE_REAL_CALLS": "0"})
    assert result["passed"] is True
    assert result["realCallsEnabled"] is False
    assert result["redisUrlConfigured"] is False
    assert result["redisUrlReturned"] is False
    assert result["secretsReturned"] is False
    assert result["realRedisEvidenceComplete"] is False
    assert result["checks"]["redis_fallback_secret_redaction"]["status"] in {"passed", "skipped"}
    assert result["checks"]["redis_fallback_secret_redaction"]["secretsReturned"] is False
    for check_id in ["redis_live_ping", "redis_distributed_counter", "redis_light_load"]:
        assert result["checks"][check_id]["status"] == "skipped"


def test_docker_runtime_smoke_harness_skips_without_opt_in():
    result = verify_docker_smoke({"AI_LANGUAGE_PARTNER_DOCKER_SMOKE_REAL_RUNS": "0"})
    assert result["passed"] is True
    assert result["staticVerificationPassed"] is True
    assert result["runtimeSmokeEnabled"] is False
    assert result["runtimeSmokeRequired"] is False
    assert result["runtimeBuildExecuted"] is False
    assert result["runtimeContainerExecuted"] is False
    assert result["runtimeEvidenceComplete"] is False
    assert result["runtimeSmokePassed"] is True
    assert result["runtimeBuildSkippedReason"] == "real_runs_disabled"
    assert result["runtimeChecks"]["docker_image_build"]["status"] == "skipped"
    assert result["runtimeChecks"]["docker_python_multipart_import"]["status"] == "skipped"
    assert result["runtimeChecks"]["docker_container_run"]["status"] == "skipped"
    assert result["runtimeChecks"]["docker_health_endpoint"]["status"] == "skipped"


def test_docker_runtime_smoke_required_fails_when_container_runtime_is_missing(monkeypatch):
    monkeypatch.setattr(docker_smoke, "_container_runtime", lambda: (None, None))
    result = verify_docker_smoke({"REQUIRE_DOCKER_SMOKE": "1"})
    assert result["passed"] is False
    assert result["staticVerificationPassed"] is True
    assert result["runtimeSmokeEnabled"] is True
    assert result["runtimeSmokeRequired"] is True
    assert result["runtimeEvidenceComplete"] is False
    assert result["runtimeSmokePassed"] is False
    assert result["runtimeBuildSkippedReason"] == "container_runtime_not_available"
    assert result["runtimeChecks"]["container_runtime_available"]["status"] == "failed"
    assert result["runtimeChecks"]["docker_python_multipart_import"]["status"] == "skipped"


def test_api_docker_smoke_workflow_requires_runtime_evidence():
    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "api-docker-smoke.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    job = workflow["jobs"]["api-docker-smoke"]
    assert job["env"]["AI_LANGUAGE_PARTNER_DOCKER_SMOKE_REQUIRED"] == "1"
    step_commands = "\n".join(
        step.get("run", "")
        for step in job["steps"]
        if isinstance(step.get("run"), str)
    )
    assert "set -o pipefail" in step_commands
    assert "python scripts/verify_docker_smoke.py | tee docker_smoke_result.json" in step_commands
    assert '"runtimeEvidenceComplete": True' in step_commands
    assert '"docker_python_multipart_import"' in step_commands
    assert '"container_runtime_available"' in step_commands


def test_docker_python_multipart_requirement_check_enforces_security_floor():
    assert python_multipart_requirement_check("python-multipart>=0.0.31") == {
        "pythonMultipartForSttMultipart": True,
        "pythonMultipartSecurityFloor": True,
    }
    assert python_multipart_requirement_check("python-multipart==0.0.31") == {
        "pythonMultipartForSttMultipart": True,
        "pythonMultipartSecurityFloor": True,
    }
    assert python_multipart_requirement_check("python-multipart") == {
        "pythonMultipartForSttMultipart": True,
        "pythonMultipartSecurityFloor": False,
    }
    assert python_multipart_requirement_check("python-multipart>=0.0.9") == {
        "pythonMultipartForSttMultipart": True,
        "pythonMultipartSecurityFloor": False,
    }
    assert python_multipart_requirement_check("python-multipart==0.0.30") == {
        "pythonMultipartForSttMultipart": True,
        "pythonMultipartSecurityFloor": False,
    }


def test_hosted_scheduler_readiness_harness_runs_local_tick_and_skips_without_hosted_env():
    result = verify_hosted_scheduler_readiness({"AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_REAL_CALLS": "0"})
    assert result["passed"] is True
    assert result["realCallsEnabled"] is False
    assert result["localSchedulerEvidenceComplete"] is True
    assert result["realHostedSchedulerEvidenceComplete"] is False
    assert result["hostedSchedulerValuesReturned"] is False
    assert result["secretsReturned"] is False
    local_tick = result["checks"]["local_api_scheduler_tick"]
    assert local_tick["status"] == "passed"
    assert local_tick["releaseAppliedCount"] == 1
    assert local_tick["operationJobsRunCount"] == 1
    assert local_tick["runHistoryContainsRun"] is True
    assert local_tick["viewerRunRejectedStatus"] == 403
    assert result["checks"]["hosted_scheduler_env_redaction"]["status"] == "passed"
    assert result["checks"]["hosted_scheduler_env_redaction"]["secretsReturned"] is False
    assert result["checks"]["hosted_scheduler_health"]["status"] == "skipped"
    assert result["checks"]["hosted_scheduler_run_once"]["status"] == "skipped"


def test_tired_today_vertical_slice_persists_review_usage_and_progress(tmp_path):
    db_path = tmp_path / "slice.sqlite3"
    client = TestClient(create_app(db_path))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["projectId"] == "ai-language-partner-mobile-shared-20260629-v1"

    personas = client.get("/v1/personas").json()["personas"]
    assert any(persona["id"] == "yui" for persona in personas)

    room = client.get("/v1/practice-rooms/tired_today").json()["practiceRoom"]
    assert room["id"] == "tired_today"
    assert room["primaryPhraseJa"] == "今日めっちゃ疲れた"
    assert room["courseId"] == "jp_beginner_speaking_ko"
    assert room["unitId"] == "unit_daily_feelings"
    assert room["lessonId"] == "lesson_tired_feelings"
    rooms = client.get("/v1/practice-rooms").json()["practiceRooms"]
    assert len(rooms) >= 50

    conv = client.post(
        "/v1/conversations",
        json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
    ).json()
    assert conv["conversationId"].startswith("conv_")

    turn = client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        json={
            "inputType": "text",
            "text": "나 오늘 너무 피곤했어. 일본어로 뭐라고 해?",
            "requestTts": True,
        },
    ).json()
    assert turn["spokenText"] == "今日めっちゃ疲れた。"
    assert turn["audioUrl"].startswith("data:audio/wav;base64,")
    assert turn["reviewCards"][0]["back"] == "今日めっちゃ疲れた。"
    assert turn["usage"]["ttsCharacters"] == len("今日めっちゃ疲れた。")
    assert turn["usage"]["llmOutputTokens"] > 0

    progress = client.get("/v1/progress/today").json()
    assert progress["completedMissions"] == 1
    assert progress["spokenSentenceCount"] == 1
    assert progress["reviewCardsCreated"] == 1

    persisted_client = TestClient(create_app(db_path))
    persisted_cards = persisted_client.get("/v1/review-cards").json()["reviewCards"]
    assert len(persisted_cards) == 1
    assert persisted_cards[0]["front"] == "오늘 너무 피곤했어"


def test_course_catalog_groups_practice_rooms_without_breaking_room_contract(tmp_path):
    client = make_client(tmp_path)

    courses = client.get("/v1/courses").json()["courses"]
    assert len(courses) >= 2
    course = next(course for course in courses if course["id"] == "jp_beginner_speaking_ko")
    assert course["id"] == "jp_beginner_speaking_ko"
    assert course["targetLanguage"] == "ja"
    assert course["nativeLanguage"] == "ko"
    room_ids = [
        room_id
        for unit in course["units"]
        for lesson in unit["lessons"]
        for room_id in lesson["practiceRoomIds"]
    ]
    assert len(room_ids) >= 22
    assert "tired_today" in room_ids
    assert "formal_cannot_today" in room_ids
    travel_course = next(course for course in courses if course["id"] == "jp_travel_survival_ko")
    travel_room_ids = [
        room_id
        for unit in travel_course["units"]
        for lesson in unit["lessons"]
        for room_id in lesson["practiceRoomIds"]
    ]
    assert len(travel_room_ids) >= 30
    assert "airport_arrival" in travel_room_ids
    assert "police_lost" in travel_room_ids

    fetched = client.get("/v1/courses/jp_beginner_speaking_ko").json()["course"]
    assert fetched["units"][0]["id"] == "unit_daily_feelings"
    fetched_travel = client.get("/v1/courses/jp_travel_survival_ko").json()["course"]
    assert fetched_travel["units"][0]["id"] == "unit_travel_arrival"
    assert client.get("/v1/practice-rooms/airport_arrival").json()["practiceRoom"]["courseId"] == "jp_travel_survival_ko"
    missing = client.get("/v1/courses/missing")
    assert missing.status_code == 404


def test_content_authoring_validation_reports_seed_quality_and_bad_bundle_errors(tmp_path):
    client = make_client(tmp_path)
    admin_headers = {"X-Admin-Key": "local-dev-admin"}
    seed_payload = {"courses": copy.deepcopy(COURSE_CATALOG), "practiceRooms": copy.deepcopy(PRACTICE_ROOMS)}

    assert client.get("/v1/content/quality-report").status_code == 403
    current_report = client.get("/v1/content/quality-report", headers=admin_headers).json()["report"]
    assert current_report["valid"] is True
    assert current_report["counts"]["courses"] >= 2
    assert current_report["counts"]["practiceRoomRefs"] >= 52
    assert current_report["orphanPracticeRoomIds"] == []

    dry_run = client.post("/v1/content/validate", headers=admin_headers, json=seed_payload).json()
    assert dry_run["ok"] is True
    assert dry_run["report"]["valid"] is True
    assert dry_run["report"]["counts"]["roomsWithCoursePlacement"] == len(PRACTICE_ROOMS)

    empty = client.post("/v1/content/validate", headers=admin_headers, json={}).json()
    empty_codes = {error["code"] for error in empty["report"]["errors"]}
    assert empty["ok"] is False
    assert {"empty_course_catalog", "empty_practice_room_catalog"} <= empty_codes

    conflicts = client.post("/v1/content/import", headers=admin_headers, json={**seed_payload, "replaceExisting": False})
    assert conflicts.status_code == 409
    conflict_codes = {error["code"] for error in conflicts.json()["detail"]["report"]["errors"]}
    assert "course_id_already_exists" in conflict_codes
    assert "practice_room_id_already_exists" in conflict_codes

    bad_payload = copy.deepcopy(seed_payload)
    bad_payload["courses"][0]["units"][0]["lessons"][0]["practiceRoomIds"].append("missing_room_for_qa")
    bad_payload["practiceRooms"].append(copy.deepcopy(bad_payload["practiceRooms"][0]))
    invalid = client.post("/v1/content/validate", headers=admin_headers, json=bad_payload).json()
    error_codes = {error["code"] for error in invalid["report"]["errors"]}
    assert invalid["ok"] is False
    assert "missing_practice_room_ref" in error_codes
    assert "duplicate_practice_room_id" in error_codes

    rejected = client.post("/v1/content/import", headers=admin_headers, json={**bad_payload, "dryRun": False})
    assert rejected.status_code == 400
    assert rejected.json()["detail"]["report"]["valid"] is False


def test_content_import_dry_run_and_apply_adds_course_room_metadata(tmp_path):
    client = make_client(tmp_path)
    admin_headers = {"X-Admin-Key": "local-dev-admin"}
    bundle = {
        "courses": [
            {
                "id": "jp_micro_station_ko",
                "title": "역에서 도움 요청하기",
                "targetLanguage": "ja",
                "nativeLanguage": "ko",
                "level": "beginner",
                "descriptionKo": "여행 중 역무원에게 짧게 도움을 요청하는 미니 코스",
                "units": [
                    {
                        "id": "unit_import_station",
                        "title": "역 안내",
                        "order": 1,
                        "skillTags": ["여행", "요청"],
                        "lessons": [
                            {
                                "id": "lesson_import_station_help",
                                "title": "역무원에게 물어보기",
                                "order": 1,
                                "practiceRoomIds": ["station_help_request"],
                            }
                        ],
                    }
                ],
            }
        ],
        "practiceRooms": [
            {
                "id": "station_help_request",
                "title": "역무원에게 도움 요청",
                "primaryPhraseKo": "플랫폼이 어디예요?",
                "primaryPhraseJa": "ホームはどこですか？",
                "alternativePhrasesJa": ["何番ホームですか？"],
                "personaId": "haruka",
                "scenario": "낯선 역에서 플랫폼 위치를 물어보기",
                "openingMessage": "丁寧に駅員さんへ聞く練習をしましょう。",
                "tags": ["여행", "요청"],
            }
        ],
    }

    dry_run = client.post("/v1/content/import", headers=admin_headers, json=bundle).json()
    assert dry_run["ok"] is True
    assert dry_run["dryRun"] is True
    assert dry_run["applied"] is False
    assert dry_run["importedCounts"] == {"courses": 0, "practiceRooms": 0}
    assert dry_run["version"]["id"].startswith("contentver_")
    assert dry_run["version"]["status"] == "draft"
    assert dry_run["version"]["snapshotCounts"] == {"courses": 1, "practiceRooms": 1}
    versions = client.get("/v1/content/versions", headers=admin_headers).json()["versions"]
    assert versions[0]["id"] == dry_run["version"]["id"]
    detail = client.get(f"/v1/content/versions/{dry_run['version']['id']}", headers=admin_headers).json()["version"]
    assert detail["courses"][0]["id"] == "jp_micro_station_ko"
    assert detail["practiceRooms"][0]["courseId"] == "jp_micro_station_ko"
    assert client.get("/v1/courses/jp_micro_station_ko").status_code == 404

    applied = client.post("/v1/content/import", headers=admin_headers, json={**bundle, "dryRun": False}).json()
    assert applied["applied"] is True
    assert applied["importedCounts"] == {"courses": 1, "practiceRooms": 1}
    assert applied["version"]["status"] == "published"
    assert applied["version"]["publishedAt"]
    course = client.get("/v1/courses/jp_micro_station_ko").json()["course"]
    room = client.get("/v1/practice-rooms/station_help_request").json()["practiceRoom"]
    assert course["units"][0]["lessons"][0]["practiceRoomIds"] == ["station_help_request"]
    assert room["courseId"] == "jp_micro_station_ko"
    assert room["unitId"] == "unit_import_station"
    assert room["lessonId"] == "lesson_import_station_help"
    assert room["roomOrder"] == 1


def test_content_version_snapshot_can_be_published_later_with_audit(tmp_path):
    client = make_client(tmp_path)
    admin_headers = {"X-Admin-Key": "local-dev-admin"}
    editor_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "editor", "X-Admin-User": "content-editor"}
    same_user_reviewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "reviewer", "X-Admin-User": "content-editor"}
    reviewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "reviewer", "X-Admin-User": "content-reviewer"}
    publisher_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "publisher", "X-Admin-User": "content-publisher"}
    viewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "viewer", "X-Admin-User": "content-viewer"}
    bundle = {
        "courses": [
            {
                "id": "jp_micro_cafe_ko",
                "title": "카페에서 주문하기",
                "targetLanguage": "ja",
                "nativeLanguage": "ko",
                "level": "beginner",
                "descriptionKo": "카페에서 정중하게 주문하는 미니 코스",
                "units": [
                    {
                        "id": "unit_import_cafe",
                        "title": "카페 주문",
                        "order": 1,
                        "skillTags": ["여행", "주문"],
                        "lessons": [
                            {
                                "id": "lesson_import_cafe_order",
                                "title": "아이스커피 주문하기",
                                "order": 1,
                                "practiceRoomIds": ["cafe_iced_coffee"],
                            }
                        ],
                    }
                ],
            }
        ],
        "practiceRooms": [
            {
                "id": "cafe_iced_coffee",
                "title": "아이스커피 주문",
                "primaryPhraseKo": "아이스커피 하나 주세요.",
                "primaryPhraseJa": "アイスコーヒーを一つください。",
                "alternativePhrasesJa": ["アイスコーヒーをお願いします。"],
                "personaId": "haruka",
                "scenario": "카페에서 음료를 주문하기",
                "openingMessage": "自然に注文する練習をしましょう。",
                "tags": ["여행", "주문"],
            }
        ],
    }

    assert client.get("/v1/content/versions").status_code == 403
    dry_run = client.post("/v1/content/import", headers=editor_headers, json=bundle).json()
    version_id = dry_run["version"]["id"]
    assert dry_run["version"]["createdBy"] == "content-editor"
    assert client.get("/v1/courses/jp_micro_cafe_ko").status_code == 404
    assert client.post(f"/v1/content/versions/{version_id}/publish").status_code == 403
    assert client.post(f"/v1/content/versions/{version_id}/publish", headers=publisher_headers).status_code == 409
    assert client.post(f"/v1/content/versions/{version_id}/approve", headers=viewer_headers, json={}).status_code == 403

    submitted = client.post(
        f"/v1/content/versions/{version_id}/submit-review",
        headers=editor_headers,
        json={"note": "ready for review"},
    ).json()
    assert submitted["version"]["status"] == "in_review"
    assert submitted["version"]["submittedBy"] == "content-editor"
    assert submitted["version"]["submittedAt"]
    same_user_approval = client.post(
        f"/v1/content/versions/{version_id}/approve",
        headers=same_user_reviewer_headers,
        json={"note": "trying to approve own submission"},
    )
    assert same_user_approval.status_code == 409
    approved = client.post(
        f"/v1/content/versions/{version_id}/approve",
        headers=reviewer_headers,
        json={"note": "approved for publish"},
    ).json()
    assert approved["version"]["status"] == "approved"
    assert approved["version"]["reviewedBy"] == "content-reviewer"
    assert approved["version"]["reviewedAt"]

    published = client.post(f"/v1/content/versions/{version_id}/publish", headers=publisher_headers).json()
    assert published["ok"] is True
    assert published["importedCounts"] == {"courses": 1, "practiceRooms": 1}
    assert published["version"]["status"] == "published"
    assert published["version"]["publishedAt"]
    course = client.get("/v1/courses/jp_micro_cafe_ko").json()["course"]
    room = client.get("/v1/practice-rooms/cafe_iced_coffee").json()["practiceRoom"]
    assert course["units"][0]["lessons"][0]["practiceRoomIds"] == ["cafe_iced_coffee"]
    assert room["courseId"] == "jp_micro_cafe_ko"
    assert room["lessonId"] == "lesson_import_cafe_order"

    assert client.get("/v1/content/operations/jobs").status_code == 403
    cancelable_job = client.post(
        "/v1/content/operations/jobs",
        headers=editor_headers,
        json={"jobType": "validate_bundle", "priority": "normal", "payload": {"bundle": bundle}},
    ).json()["job"]
    queued_import = client.post(
        "/v1/content/operations/jobs",
        headers=editor_headers,
        json={
            "jobType": "import_bundle",
            "priority": "urgent",
            "payload": {"bundle": bundle, "dryRun": True, "replaceExisting": True},
        },
    ).json()["job"]
    assert cancelable_job["status"] == "queued"
    assert queued_import["priority"] == "urgent"
    queued_jobs = client.get("/v1/content/operations/jobs?status=queued", headers=viewer_headers).json()["jobs"]
    assert queued_jobs[0]["id"] == queued_import["id"]
    assert client.post(
        "/v1/content/operations/jobs/run-next",
        headers=viewer_headers,
        json={"confirmation": "run-next-content-operation-job"},
    ).status_code == 403
    operation_run = client.post(
        "/v1/content/operations/jobs/run-next",
        headers=publisher_headers,
        json={"confirmation": "run-next-content-operation-job"},
    ).json()
    assert operation_run["ok"] is True
    assert operation_run["job"]["id"] == queued_import["id"]
    assert operation_run["job"]["status"] == "succeeded"
    assert operation_run["result"]["ok"] is True
    assert operation_run["result"]["version"]["source"] == "content_operation_import_dry_run"
    operation_detail = client.get(
        f"/v1/content/operations/jobs/{queued_import['id']}",
        headers=viewer_headers,
    ).json()["job"]
    assert operation_detail["status"] == "succeeded"
    canceled_job = client.post(
        f"/v1/content/operations/jobs/{cancelable_job['id']}/cancel",
        headers=editor_headers,
        json={"confirmation": "cancel-content-operation-job"},
    ).json()["job"]
    assert canceled_job["status"] == "canceled"

    assert client.get("/v1/content/releases").status_code == 403
    release_bundle = copy.deepcopy(bundle)
    release_bundle["courses"][0]["title"] = "카페에서 주문하기 - release canary"
    release_bundle["practiceRooms"][0]["title"] = "아이스커피 주문 - release canary"
    release_dry_run = client.post("/v1/content/import", headers=editor_headers, json=release_bundle).json()
    release_version_id = release_dry_run["version"]["id"]
    assert client.post(
        "/v1/content/releases",
        headers=editor_headers,
        json={"versionId": release_version_id, "title": "Unapproved release"},
    ).status_code == 409
    client.post(
        f"/v1/content/versions/{release_version_id}/submit-review",
        headers=editor_headers,
        json={"note": "release candidate"},
    )
    client.post(
        f"/v1/content/versions/{release_version_id}/approve",
        headers=reviewer_headers,
        json={"note": "release approved"},
    )
    assert client.post(
        "/v1/content/releases",
        headers=viewer_headers,
        json={"versionId": release_version_id, "title": "Viewer cannot plan"},
    ).status_code == 403
    release = client.post(
        "/v1/content/releases",
        headers=editor_headers,
        json={
            "versionId": release_version_id,
            "title": "Cafe copy canary",
            "releaseStrategy": "canary",
            "rolloutPercent": 25,
            "scheduledAt": "2999-01-01T00:00:00Z",
            "guardrails": {"manualQa": "passed"},
            "note": "ship to canary audience first",
        },
    ).json()["release"]
    assert release["releaseStrategy"] == "canary"
    assert release["rolloutPercent"] == 25
    assert release["guardrails"]["qualityReportValid"] is True
    assert client.post(
        f"/v1/content/releases/{release['id']}/apply",
        headers=editor_headers,
        json={"confirmation": "apply-content-release", "force": True},
    ).status_code == 403
    assert client.post(
        f"/v1/content/releases/{release['id']}/apply",
        headers=publisher_headers,
        json={"confirmation": "apply-content-release"},
    ).status_code == 409
    applied_release = client.post(
        f"/v1/content/releases/{release['id']}/apply",
        headers=publisher_headers,
        json={"confirmation": "apply-content-release", "force": True, "note": "approved release window"},
    ).json()
    assert applied_release["release"]["status"] == "applied"
    assert applied_release["release"]["previousPublishedVersionId"] == version_id
    assert applied_release["release"]["appliedBy"] == "content-publisher"
    assert client.get("/v1/courses/jp_micro_cafe_ko").json()["course"]["title"] == "카페에서 주문하기 - release canary"
    rolled_back = client.post(
        f"/v1/content/releases/{release['id']}/rollback",
        headers=publisher_headers,
        json={"confirmation": "rollback-content-release", "note": "rollback after canary check"},
    ).json()
    assert rolled_back["release"]["status"] == "rolled_back"
    assert rolled_back["release"]["rolledBackBy"] == "content-publisher"
    assert rolled_back["release"]["rollbackNote"] == "rollback after canary check"
    assert client.get("/v1/courses/jp_micro_cafe_ko").json()["course"]["title"] == "카페에서 주문하기"
    worker_bundle = copy.deepcopy(bundle)
    worker_bundle["courses"][0]["title"] = "카페에서 주문하기 - worker release"
    worker_dry_run = client.post("/v1/content/import", headers=editor_headers, json=worker_bundle).json()
    worker_version_id = worker_dry_run["version"]["id"]
    client.post(
        f"/v1/content/versions/{worker_version_id}/submit-review",
        headers=editor_headers,
        json={"note": "worker release candidate"},
    )
    client.post(
        f"/v1/content/versions/{worker_version_id}/approve",
        headers=reviewer_headers,
        json={"note": "worker release approved"},
    )
    worker_release = client.post(
        "/v1/content/releases",
        headers=editor_headers,
        json={
            "versionId": worker_version_id,
            "title": "Cafe copy scheduled worker",
            "releaseStrategy": "scheduled",
            "rolloutPercent": 100,
            "scheduledAt": "2000-01-01T00:00:00Z",
        },
    ).json()["release"]
    assert worker_release["status"] == "scheduled"
    assert client.post(
        "/v1/content/releases/run-due",
        headers=editor_headers,
        json={"confirmation": "run-due-content-releases"},
    ).status_code == 403
    worker_run = client.post(
        "/v1/content/releases/run-due",
        headers=publisher_headers,
        json={"confirmation": "run-due-content-releases", "limit": 10},
    ).json()
    assert worker_run["ok"] is True
    assert worker_run["appliedCount"] == 1
    assert worker_run["appliedReleases"][0]["id"] == worker_release["id"]
    assert worker_run["appliedReleases"][0]["status"] == "applied"
    assert client.get("/v1/courses/jp_micro_cafe_ko").json()["course"]["title"] == "카페에서 주문하기 - worker release"
    scheduler_bundle = copy.deepcopy(bundle)
    scheduler_bundle["courses"][0]["title"] = "카페에서 주문하기 - managed scheduler"
    scheduler_dry_run = client.post("/v1/content/import", headers=editor_headers, json=scheduler_bundle).json()
    scheduler_version_id = scheduler_dry_run["version"]["id"]
    client.post(
        f"/v1/content/versions/{scheduler_version_id}/submit-review",
        headers=editor_headers,
        json={"note": "managed scheduler candidate"},
    )
    client.post(
        f"/v1/content/versions/{scheduler_version_id}/approve",
        headers=reviewer_headers,
        json={"note": "managed scheduler approved"},
    )
    scheduler_release = client.post(
        "/v1/content/releases",
        headers=editor_headers,
        json={
            "versionId": scheduler_version_id,
            "title": "Cafe copy managed scheduler",
            "releaseStrategy": "scheduled",
            "rolloutPercent": 100,
            "scheduledAt": "2000-01-02T00:00:00Z",
        },
    ).json()["release"]
    scheduler_job = client.post(
        "/v1/content/operations/jobs",
        headers=editor_headers,
        json={"jobType": "validate_bundle", "priority": "high", "payload": {"bundle": scheduler_bundle}},
    ).json()["job"]
    assert client.get("/v1/content/scheduler/runs").status_code == 403
    assert client.post(
        "/v1/content/scheduler/run-once",
        headers=viewer_headers,
        json={"confirmation": "run-content-scheduler-once"},
    ).status_code == 403
    scheduler_tick = client.post(
        "/v1/content/scheduler/run-once",
        headers=publisher_headers,
        json={
            "confirmation": "run-content-scheduler-once",
            "leaseOwner": "pytest-content-scheduler",
            "maxOperationJobs": 1,
            "releaseLimit": 10,
        },
    ).json()
    assert scheduler_tick["ok"] is True
    assert scheduler_tick["run"]["status"] == "succeeded"
    assert scheduler_tick["run"]["leaseOwner"] == "pytest-content-scheduler"
    assert scheduler_tick["run"]["result"]["operationJobsRunCount"] == 1
    assert scheduler_tick["releaseWorker"]["appliedCount"] == 1
    assert scheduler_tick["releaseWorker"]["appliedReleases"][0]["id"] == scheduler_release["id"]
    assert scheduler_tick["operationJobs"][0]["job"]["id"] == scheduler_job["id"]
    assert scheduler_tick["operationJobs"][0]["job"]["status"] == "succeeded"
    scheduler_runs = client.get("/v1/content/scheduler/runs?status=succeeded", headers=viewer_headers).json()["runs"]
    assert scheduler_runs[0]["id"] == scheduler_tick["run"]["id"]
    assert client.get("/v1/courses/jp_micro_cafe_ko").json()["course"]["title"] == "카페에서 주문하기 - managed scheduler"
    assert client.get("/v1/admin/ops-console").status_code == 403
    ops_console = client.get("/v1/admin/ops-console", headers=viewer_headers)
    assert ops_console.status_code == 200
    assert "text/html" in ops_console.headers["content-type"]
    assert "Ops Console" in ops_console.text
    assert "Action Console" in ops_console.text
    assert "/v1/content/scheduler/run-once" in ops_console.text
    assert "/v1/content/releases/run-due" in ops_console.text
    assert "/v1/content/operations/jobs/run-next" in ops_console.text
    assert "opsActionResult" in ops_console.text
    assert "pytest-content-scheduler" in ops_console.text
    assert "Cafe copy managed scheduler" in ops_console.text
    assert "content_scheduler_run_succeeded" in ops_console.text
    assert client.get("/v1/admin/content-console").status_code == 403
    content_console = client.get("/v1/admin/content-console", headers=viewer_headers)
    assert content_console.status_code == 200
    assert "text/html" in content_console.headers["content-type"]
    assert "Content Console" in content_console.text
    assert "Authoring Action Console" in content_console.text
    assert "/v1/content/validate" in content_console.text
    assert "/v1/content/import" in content_console.text
    assert "/v1/content/bulk-qa" in content_console.text
    assert "/v1/content/translation-memory/suggest" in content_console.text
    assert "/v1/content/translation-memory" in content_console.text
    assert "/v1/content/versions/__versionId__/branch" in content_console.text
    assert "/v1/content/versions/__versionId__/assign" in content_console.text
    assert "contentConsoleResult" in content_console.text
    assert scheduler_version_id in content_console.text
    release_list = client.get("/v1/content/releases", headers=viewer_headers).json()["releases"]
    assert any(item["id"] == release["id"] and item["status"] == "rolled_back" for item in release_list)
    assert any(item["id"] == worker_release["id"] and item["status"] == "applied" for item in release_list)
    assert any(item["id"] == scheduler_release["id"] and item["status"] == "applied" for item in release_list)
    provider_content = client.get("/v1/providers/status").json()["operations"]["content"]
    assert provider_content["releasePlans"] is True
    assert provider_content["releaseScheduling"] is True
    assert provider_content["canaryReleaseMetadata"] is True
    assert provider_content["releaseWorker"] is True
    assert provider_content["releaseRollback"] is True
    assert provider_content["operationJobs"] is True
    assert provider_content["operationJobRunner"] is True
    assert provider_content["managedScheduler"] is True
    assert provider_content["schedulerRunHistory"] is True
    assert provider_content["adminOpsConsole"] is True
    assert provider_content["adminActionConsole"] is True
    assert provider_content["adminContentConsole"] is True

    audit_logs = client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]
    actions = [log["action"] for log in audit_logs]
    assert "content_version_created" in actions
    assert "content_operation_job_queued" in actions
    assert "content_operation_job_succeeded" in actions
    assert "content_operation_job_canceled" in actions
    assert "content_version_submitted_for_review" in actions
    assert "content_version_approved" in actions
    assert "content_release_planned" in actions
    assert "content_release_applied" in actions
    assert "content_release_worker_run" in actions
    assert "content_release_rolled_back" in actions
    assert "content_scheduler_run_succeeded" in actions
    publish_log = next(log for log in audit_logs if log["action"] == "content_version_published")
    assert publish_log["targetId"] == version_id
    assert publish_log["payload"]["importedCounts"] == {"courses": 1, "practiceRooms": 1}

    rejected_dry_run = client.post("/v1/content/import", headers=editor_headers, json=bundle).json()
    rejected_version_id = rejected_dry_run["version"]["id"]
    client.post(
        f"/v1/content/versions/{rejected_version_id}/submit-review",
        headers=editor_headers,
        json={"note": "needs second look"},
    )
    rejected = client.post(
        f"/v1/content/versions/{rejected_version_id}/reject",
        headers=reviewer_headers,
        json={"note": "revise the Japanese phrase set"},
    ).json()
    assert rejected["version"]["status"] == "rejected"
    assert rejected["version"]["reviewedBy"] == "content-reviewer"
    assert rejected["version"]["reviewNote"] == "revise the Japanese phrase set"


def test_translation_memory_and_bulk_qa_are_role_gated_and_find_conflicts(tmp_path):
    client = make_client(tmp_path)
    admin_headers = {"X-Admin-Key": "local-dev-admin"}
    viewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "viewer", "X-Admin-User": "tm-viewer"}
    editor_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "editor", "X-Admin-User": "tm-editor"}
    tired_room = next(room for room in PRACTICE_ROOMS if room["id"] == "tired_today")

    assert client.get("/v1/content/translation-memory").status_code == 403
    seeded = client.get("/v1/content/translation-memory", headers=viewer_headers, params={"limit": 200}).json()["entries"]
    assert len(seeded) >= len(PRACTICE_ROOMS)
    assert any(entry["sourceRef"] == "tired_today" and entry["targetText"] == tired_room["primaryPhraseJa"] for entry in seeded)

    suggestions = client.post(
        "/v1/content/translation-memory/suggest",
        headers=viewer_headers,
        json={"sourceText": tired_room["primaryPhraseKo"], "limit": 10},
    ).json()["suggestions"]
    assert any(item["targetText"] == tired_room["primaryPhraseJa"] and item["matchType"] == "exact" for item in suggestions)

    custom_entry = {
        "entries": [
            {
                "sourceText": "새로운 표현 테스트",
                "targetText": "新しい表現のテスト",
                "tags": ["qa"],
                "sourceRef": "manual:test",
                "quality": 91,
            }
        ]
    }
    assert client.post("/v1/content/translation-memory", headers=viewer_headers, json=custom_entry).status_code == 403
    upserted = client.post("/v1/content/translation-memory", headers=editor_headers, json=custom_entry).json()
    assert upserted["ok"] is True
    assert upserted["upsertedCounts"]["entries"] == 1
    custom_suggestions = client.post(
        "/v1/content/translation-memory/suggest",
        headers=viewer_headers,
        json={"sourceText": "새로운 표현 테스트"},
    ).json()["suggestions"]
    assert custom_suggestions[0]["targetText"] == "新しい表現のテスト"

    current_qa = client.post("/v1/content/bulk-qa", headers=viewer_headers, json={}).json()
    assert current_qa["ok"] is True
    assert current_qa["source"] == "current"
    assert current_qa["report"]["counts"]["translationMemoryExactMatches"] >= len(PRACTICE_ROOMS)
    assert current_qa["report"]["counts"]["translationMemoryConflicts"] == 0

    conflict_rooms = copy.deepcopy(PRACTICE_ROOMS)
    conflict_rooms[0]["primaryPhraseJa"] = "意図的に違う翻訳です。"
    conflict_qa = client.post(
        "/v1/content/bulk-qa",
        headers=viewer_headers,
        json={"courses": copy.deepcopy(COURSE_CATALOG), "practiceRooms": conflict_rooms},
    ).json()
    assert conflict_qa["ok"] is True
    assert conflict_qa["source"] == "request"
    assert conflict_qa["report"]["counts"]["translationMemoryConflicts"] >= 1
    assert "translation_memory_target_conflict" in {issue["code"] for issue in conflict_qa["report"]["issues"]}

    audit_actions = [log["action"] for log in client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]]
    assert "content_translation_memory_upserted" in audit_actions
    assert "content_bulk_qa_completed" in audit_actions


def test_content_branching_assignments_are_role_gated_and_audited(tmp_path):
    client = make_client(tmp_path)
    admin_headers = {"X-Admin-Key": "local-dev-admin"}
    editor_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "editor", "X-Admin-User": "branch-editor"}
    viewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "viewer", "X-Admin-User": "branch-viewer"}
    reviewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "reviewer", "X-Admin-User": "branch-reviewer"}
    seed_payload = {"courses": copy.deepcopy(COURSE_CATALOG), "practiceRooms": copy.deepcopy(PRACTICE_ROOMS)}
    version = client.post("/v1/content/import", headers=editor_headers, json=seed_payload).json()["version"]
    version_id = version["id"]

    assert client.post(f"/v1/content/versions/{version_id}/branch", headers=viewer_headers, json={}).status_code == 403
    branch = client.post(
        f"/v1/content/versions/{version_id}/branch",
        headers=editor_headers,
        json={
            "label": "Travel survival copy branch",
            "branchName": "travel-survival-copy",
            "assignee": "writer-a",
            "priority": "high",
            "dueAt": "2026-07-05T00:00:00Z",
            "note": "tighten Korean prompts before review",
        },
    ).json()
    assert branch["ok"] is True
    branch_version = branch["version"]
    assignment = branch["assignment"]
    assert branch_version["id"] != version_id
    assert branch_version["status"] == "draft"
    assert branch_version["source"] == "content_branch"
    assert branch_version["parentVersionId"] == version_id
    assert branch_version["branchName"] == "travel-survival-copy"
    assert branch_version["snapshotCounts"] == version["snapshotCounts"]
    assert assignment["versionId"] == branch_version["id"]
    assert assignment["assignee"] == "writer-a"
    assert assignment["status"] == "todo"
    assert assignment["priority"] == "high"
    assert assignment["dueAt"] == "2026-07-05T00:00:00Z"

    listed = client.get("/v1/content/assignments", headers=viewer_headers, params={"assignee": "writer-a"}).json()["assignments"]
    assert listed[0]["id"] == assignment["id"]
    assert listed[0]["parentVersionId"] == version_id

    assert client.post(
        f"/v1/content/versions/{branch_version['id']}/assign",
        headers=viewer_headers,
        json={"assignee": "writer-b"},
    ).status_code == 403
    reassigned = client.post(
        f"/v1/content/versions/{branch_version['id']}/assign",
        headers=editor_headers,
        json={"assignee": "writer-b", "priority": "urgent", "status": "in_progress", "note": "copy pass started"},
    ).json()["assignment"]
    assert reassigned["id"] == assignment["id"]
    assert reassigned["assignee"] == "writer-b"
    assert reassigned["priority"] == "urgent"
    assert reassigned["status"] == "in_progress"

    assert client.post(
        f"/v1/content/assignments/{assignment['id']}/status",
        headers=viewer_headers,
        json={"status": "done"},
    ).status_code == 403
    completed = client.post(
        f"/v1/content/assignments/{assignment['id']}/status",
        headers=reviewer_headers,
        json={"status": "done", "note": "ready for review submission"},
    ).json()["assignment"]
    assert completed["status"] == "done"
    assert completed["completedAt"]
    assert completed["updatedBy"] == "branch-reviewer"

    provider_content = client.get("/v1/providers/status").json()["operations"]["content"]
    assert provider_content["branchingAssignments"] is True

    audit_actions = [log["action"] for log in client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]]
    assert "content_version_branched" in audit_actions
    assert "content_assignment_upserted" in audit_actions
    assert "content_assignment_status_updated" in audit_actions


def test_experiments_assign_stable_variants_log_events_and_gate_admin_controls(tmp_path):
    client = make_client(tmp_path)
    admin_headers = {"X-Admin-Key": "local-dev-admin"}
    viewer_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "viewer", "X-Admin-User": "experiment-viewer"}
    editor_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "editor", "X-Admin-User": "experiment-editor"}
    publisher_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "publisher", "X-Admin-User": "experiment-publisher"}
    learner_headers = {"X-Learner-Id": "experiment-learner-a"}

    assert client.get("/v1/experiments").status_code == 403
    seeded = client.get("/v1/experiments", headers=viewer_headers).json()["experiments"]
    seeded_keys = {experiment["key"] for experiment in seeded}
    assert {"daily_recommendation_copy_v1", "practice_room_order_v1"} <= seeded_keys
    assert all(experiment["status"] == "running" for experiment in seeded if experiment["key"] in seeded_keys)

    first = client.get("/v1/experiments/assignments", headers=learner_headers).json()
    second = client.get("/v1/experiments/assignments", headers=learner_headers).json()
    assert first["assignmentCount"] >= 2
    first_variants = {item["experimentKey"]: item["variantKey"] for item in first["assignments"]}
    second_variants = {item["experimentKey"]: item["variantKey"] for item in second["assignments"]}
    assert first_variants == second_variants
    assert first["assignments"][0]["exposureEventId"].startswith("expevt_")
    assert first_variants["daily_recommendation_copy_v1"] in {"control", "memory_pressure"}

    event = client.post(
        "/v1/experiments/daily_recommendation_copy_v1/events",
        headers=learner_headers,
        json={"eventName": "conversion", "payload": {"surface": "HomeTodayScreen"}},
    ).json()["event"]
    assert event["eventName"] == "conversion"
    assert event["variantKey"] == first_variants["daily_recommendation_copy_v1"]
    assert event["assignment"]["experimentKey"] == "daily_recommendation_copy_v1"

    assert client.get("/v1/experiments/daily_recommendation_copy_v1/analytics").status_code == 403
    analytics = client.get(
        "/v1/experiments/daily_recommendation_copy_v1/analytics?minimumExposedLearners=1",
        headers=viewer_headers,
    ).json()["analytics"]
    assert analytics["experiment"]["key"] == "daily_recommendation_copy_v1"
    assert analytics["minimumExposedLearners"] == 1
    assert analytics["totals"]["assignmentCount"] >= 1
    assert analytics["totals"]["exposureEventCount"] >= 2
    assert analytics["totals"]["conversionEventCount"] == 1
    converted_variant = next(item for item in analytics["variants"] if item["variantKey"] == event["variantKey"])
    assert converted_variant["assignmentCount"] >= 1
    assert converted_variant["exposureEventCount"] >= 2
    assert converted_variant["exposedLearnerCount"] == 1
    assert converted_variant["convertedLearnerCount"] == 1
    assert converted_variant["exposedConversionRate"] == 1.0
    assert converted_variant["conversionRateConfidenceInterval95"]["lower"] >= 0.0
    assert converted_variant["baselineVariantKey"] in {"control", "memory_pressure", "streak_focus"}
    assert "pValue" in converted_variant
    assert converted_variant["decisionEligible"] is True
    assert analytics["statisticalSignificanceAlpha"] == 0.05
    assert analytics["decisionRecommendation"] == "collect_more_data"
    assert analytics["significantPositiveVariantKeys"] == []
    assert analytics["bestObservedVariantKey"] == event["variantKey"]
    assert analytics["decisionReady"] is False
    assert analytics["winnerVariantKey"] is None

    new_experiment = {
        "key": "Paywall_Copy_Test_V1",
        "name": "Paywall copy test",
        "status": "running",
        "variants": [
            {"key": "control", "label": "Control", "weight": 1, "payload": {"copy": "current"}},
            {"key": "trial_focus", "label": "Trial focus", "weight": 1, "payload": {"copy": "trial"}},
        ],
        "allocation": {"unit": "learner"},
    }
    assert client.post("/v1/experiments", headers=viewer_headers, json=new_experiment).status_code == 403
    created = client.post("/v1/experiments", headers=editor_headers, json=new_experiment).json()["experiment"]
    assert created["key"] == "paywall_copy_test_v1"
    assert created["status"] == "running"

    learner_b_assignments = client.get("/v1/experiments/assignments", headers={"X-Learner-Id": "experiment-learner-b"}).json()["assignments"]
    paywall_assignment = next(item for item in learner_b_assignments if item["experimentKey"] == "paywall_copy_test_v1")
    assert paywall_assignment["variantKey"] in {"control", "trial_focus"}

    observed_variants: dict[str, int] = {}
    converted_trial_focus = False
    for index in range(40):
        learner_headers_stat = {"X-Learner-Id": f"experiment-stat-learner-{index}"}
        assignments = client.get("/v1/experiments/assignments", headers=learner_headers_stat).json()["assignments"]
        assignment = next(item for item in assignments if item["experimentKey"] == "paywall_copy_test_v1")
        observed_variants[assignment["variantKey"]] = observed_variants.get(assignment["variantKey"], 0) + 1
        if assignment["variantKey"] == "trial_focus" and not converted_trial_focus:
            converted_trial_focus = True
            client.post(
                "/v1/experiments/paywall_copy_test_v1/events",
                headers=learner_headers_stat,
                json={"eventName": "conversion", "payload": {"surface": "paywall"}},
            )
        if {"control", "trial_focus"} <= set(observed_variants):
            break
    assert {"control", "trial_focus"} <= set(observed_variants)
    statistical_analytics = client.get(
        "/v1/experiments/paywall_copy_test_v1/analytics?minimumExposedLearners=1",
        headers=viewer_headers,
    ).json()["analytics"]
    assert statistical_analytics["controlVariantKey"] == "control"
    assert statistical_analytics["decisionReady"] is True
    assert statistical_analytics["decisionRecommendation"] in {"no_statistically_significant_winner", "promote_winner"}
    trial_focus = next(item for item in statistical_analytics["variants"] if item["variantKey"] == "trial_focus")
    control = next(item for item in statistical_analytics["variants"] if item["variantKey"] == "control")
    assert trial_focus["baselineVariantKey"] == "control"
    assert trial_focus["absoluteLiftFromBaseline"] is not None
    assert trial_focus["pValue"] is None or 0.0 <= trial_focus["pValue"] <= 1.0
    assert set(trial_focus["confidenceInterval95"]) == {"lower", "upper"}
    assert control["absoluteLiftFromBaseline"] == 0.0
    assert control["confidenceInterval95"] == {"lower": 0.0, "upper": 0.0}
    assert any("two-proportion z-test" in note for note in statistical_analytics["analysisNotes"])

    assert client.post(
        "/v1/experiments/paywall_copy_test_v1/decisions",
        headers=viewer_headers,
        json={"action": "collect_more_data", "minimumExposedLearners": 1},
    ).status_code == 403
    rejected_decision = client.post(
        "/v1/experiments/paywall_copy_test_v1/decisions",
        headers=editor_headers,
        json={"action": "promote_variant", "variantKey": "missing", "minimumExposedLearners": 1},
    )
    assert rejected_decision.status_code == 409
    proposed_decision = client.post(
        "/v1/experiments/paywall_copy_test_v1/decisions",
        headers=editor_headers,
        json={
            "action": "promote_variant",
            "variantKey": "trial_focus",
            "minimumExposedLearners": 1,
            "requireStatisticalSignificance": False,
            "reason": "Trial copy wins the local smoke conversion check.",
        },
    ).json()
    assert proposed_decision["ok"] is True
    assert proposed_decision["guardrail"]["ok"] is True
    decision = proposed_decision["decision"]
    assert decision["action"] == "promote_variant"
    assert decision["variantKey"] == "trial_focus"
    assert decision["status"] == "proposed"
    assert decision["analyticsSnapshot"]["experiment"]["key"] == "paywall_copy_test_v1"
    listed_decisions = client.get(
        "/v1/experiments/paywall_copy_test_v1/decisions",
        headers=viewer_headers,
    ).json()["decisions"]
    assert any(item["id"] == decision["id"] for item in listed_decisions)
    assert client.post(
        f"/v1/experiments/paywall_copy_test_v1/decisions/{decision['id']}/apply",
        headers=editor_headers,
        json={"confirmation": "apply-experiment-decision"},
    ).status_code == 403
    applied_decision = client.post(
        f"/v1/experiments/paywall_copy_test_v1/decisions/{decision['id']}/apply",
        headers=publisher_headers,
        json={"confirmation": "apply-experiment-decision", "note": "Lock rollout to winning copy."},
    ).json()
    assert applied_decision["ok"] is True
    assert applied_decision["decision"]["status"] == "applied"
    assert applied_decision["experiment"]["status"] == "running"
    promoted_weights = {variant["key"]: variant["weight"] for variant in applied_decision["experiment"]["variants"]}
    assert promoted_weights == {"control": 0, "trial_focus": 1000}
    assert applied_decision["experiment"]["allocation"]["decision"]["rolloutVariantKey"] == "trial_focus"
    post_decision_assignment = client.get(
        "/v1/experiments/assignments",
        headers={"X-Learner-Id": "experiment-post-decision"},
    ).json()["assignments"]
    assert next(item for item in post_decision_assignment if item["experimentKey"] == "paywall_copy_test_v1")["variantKey"] == "trial_focus"
    assert client.post(
        f"/v1/experiments/paywall_copy_test_v1/decisions/{decision['id']}/apply",
        headers=publisher_headers,
        json={"confirmation": "apply-experiment-decision"},
    ).status_code == 409

    assert client.post(
        "/v1/experiments/paywall_copy_test_v1/status",
        headers=viewer_headers,
        json={"status": "paused"},
    ).status_code == 403
    paused = client.post(
        "/v1/experiments/paywall_copy_test_v1/status",
        headers=editor_headers,
        json={"status": "paused"},
    ).json()["experiment"]
    assert paused["status"] == "paused"

    providers = client.get("/v1/providers/status").json()
    assert providers["operations"]["experiments"]["stableAssignments"] is True
    assert providers["operations"]["experiments"]["exposureLogging"] is True
    assert providers["operations"]["experiments"]["analyticsDashboard"] is True
    assert providers["operations"]["experiments"]["variantAnalytics"] is True
    assert providers["operations"]["experiments"]["decisionConsole"] is True
    assert providers["operations"]["experiments"]["decisionActionConsole"] is True
    assert providers["operations"]["experiments"]["decisionReadinessGuard"] is True
    assert providers["operations"]["experiments"]["statisticalTesting"] is True
    assert providers["operations"]["experiments"]["decisionWorkflow"] is True
    assert providers["operations"]["experiments"]["decisionGuardrails"] is True
    assert providers["operations"]["experiments"]["winnerRolloutApplication"] is True
    assert "experiment stable assignment and exposure logging" in providers["openCoreBoundary"]["publicCore"]

    assert client.get("/v1/admin/experiment-console").status_code == 403
    experiment_console = client.get(
        "/v1/admin/experiment-console",
        headers=viewer_headers,
        params={"experimentKey": "paywall_copy_test_v1", "minimumExposedLearners": 1},
    )
    assert experiment_console.status_code == 200
    assert "text/html" in experiment_console.headers["content-type"]
    assert "Experiment Console" in experiment_console.text
    assert "Experiment Action Console" in experiment_console.text
    assert "/v1/experiments" in experiment_console.text
    assert "/v1/experiments/__experimentKey__/status" in experiment_console.text
    assert "/v1/experiments/__experimentKey__/decisions" in experiment_console.text
    assert "/v1/experiments/__experimentKey__/decisions/__decisionId__/apply" in experiment_console.text
    assert "experimentActionResult" in experiment_console.text
    assert "paywall_copy_test_v1" in experiment_console.text
    assert "trial_focus" in experiment_console.text
    assert decision["id"] in experiment_console.text
    assert "promote_variant" in experiment_console.text
    assert "experiment_decision_applied" in experiment_console.text
    assert client.get(
        "/v1/admin/experiment-console",
        headers=viewer_headers,
        params={"experimentKey": "missing_experiment_v1"},
    ).status_code == 404

    privacy = client.delete("/v1/privacy/me", headers=learner_headers).json()
    assert privacy["deletedCounts"]["experimentAssignments"] >= 2
    assert privacy["deletedCounts"]["experimentEvents"] >= 3

    audit_actions = [log["action"] for log in client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]]
    assert "experiment_upserted" in audit_actions
    assert "experiment_status_updated" in audit_actions
    assert "experiment_analytics_viewed" in audit_actions
    assert "experiment_decision_rejected" in audit_actions
    assert "experiment_decision_proposed" in audit_actions
    assert "experiment_decision_applied" in audit_actions


def test_gamification_tracks_xp_streak_daily_quests_and_weekly_leaderboard(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_XP_DAILY_SOFT_LIMIT", "25")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_XP_BOOSTED_DAILY_SOFT_LIMIT", "10")
    client = make_client(tmp_path)
    learner_a_headers = {"X-Learner-Id": "gamification-alpha"}
    learner_b_headers = {"X-Learner-Id": "gamification-beta"}
    learner_c_headers = {"X-Learner-Id": "gamification-gamma"}
    learner_d_headers = {"X-Learner-Id": "gamification-delta"}
    learner_e_headers = {"X-Learner-Id": "gamification-epsilon"}
    learner_f_headers = {"X-Learner-Id": "gamification-zeta"}

    conv = client.post(
        "/v1/conversations",
        headers=learner_a_headers,
        json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
    ).json()
    client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        headers=learner_a_headers,
        json={"inputType": "mock_audio", "text": "今日めっちゃ疲れた", "requestTts": False},
    )
    first_gamification = client.get("/v1/gamification/me", headers=learner_a_headers).json()
    assert first_gamification["xp"]["todayXp"] >= 20
    assert first_gamification["streak"]["currentStreak"] == 1
    assert first_gamification["streak"]["isActiveToday"] is True
    first_quests = {quest["key"]: quest for quest in first_gamification["dailyQuests"]}
    assert first_quests["complete_practice_turn"]["completed"] is True
    assert first_quests["review_one_card"]["completed"] is False

    due_card = client.get("/v1/review-cards/due", headers=learner_a_headers).json()["reviewCards"][0]
    client.post(f"/v1/review-cards/{due_card['id']}/grade", headers=learner_a_headers, json={"quality": 5})
    completed_gamification = client.get("/v1/gamification/me", headers=learner_a_headers).json()
    completed_quests = {quest["key"]: quest for quest in completed_gamification["dailyQuests"]}
    assert completed_gamification["xp"]["todayXp"] >= 30
    assert completed_quests["review_one_card"]["completed"] is True
    assert completed_quests["earn_30_xp"]["completed"] is True
    assert completed_gamification["league"]["currentTier"]["key"] in {"silver", "gold", "sapphire", "ruby"}
    assert completed_gamification["achievements"]["awardedCount"] >= 4
    assert completed_gamification["achievements"]["totalCount"] >= 12
    assert completed_gamification["achievements"]["trackCount"] >= 7
    xp_rookie_levels = [
        item for item in completed_gamification["achievements"]["achievements"] if item["key"] == "xp_rookie"
    ]
    assert {item["level"] for item in xp_rookie_levels} >= {1, 2, 3}
    assert all(item["maxLevel"] == 3 for item in xp_rookie_levels)
    assert all(item["rewardGems"] >= 1 for item in xp_rookie_levels)
    assert {item["key"] for item in completed_gamification["achievements"]["achievements"] if item["awarded"]} >= {
        "first_steps",
        "review_rookie",
        "xp_rookie",
        "quest_kickoff",
    }
    assert any(flag["reason"] == "daily_xp_soft_limit_exceeded" for flag in completed_gamification["xpAbuseFlags"])
    assert client.get("/v1/achievements/me", headers=learner_a_headers).json()["awardedCount"] >= 4
    assert client.get("/v1/leagues/me", headers=learner_a_headers).json()["currentTier"]["key"] in {"silver", "gold", "sapphire", "ruby"}
    alpha_social_settings = client.put(
        "/v1/social/settings",
        headers=learner_a_headers,
        json={"discoverable": True, "allowFriendInvites": True, "showWeeklyXp": True},
    ).json()
    assert alpha_social_settings["discoverable"] is True
    assert alpha_social_settings["allowFriendInvites"] is True

    beta_conv = client.post(
        "/v1/conversations",
        headers=learner_b_headers,
        json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
    ).json()
    client.post(
        f"/v1/conversations/{beta_conv['conversationId']}/turns",
        headers=learner_b_headers,
        json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
    )
    leaderboard = client.get("/v1/leaderboards/weekly", headers=learner_a_headers).json()
    assert leaderboard["entries"][0]["learnerId"] == "gamification-alpha"
    assert leaderboard["entries"][0]["rank"] == 1
    assert leaderboard["currentLearnerRank"] == 1

    self_invite = client.post(
        "/v1/friends/invites",
        headers=learner_a_headers,
        json={"friendLearnerId": "gamification-alpha"},
    )
    assert self_invite.status_code == 400
    invite = client.post(
        "/v1/friends/invites",
        headers=learner_a_headers,
        json={"friendLearnerId": "gamification-beta", "message": "같이 퀘스트 하자"},
    ).json()
    assert invite["created"] is True
    assert invite["invite"]["requesterLearnerId"] == "gamification-alpha"
    assert invite["invite"]["addresseeLearnerId"] == "gamification-beta"
    alpha_friends_before_accept = client.get("/v1/friends", headers=learner_a_headers).json()
    assert alpha_friends_before_accept["friendCount"] == 0
    assert alpha_friends_before_accept["outgoingInvites"][0]["id"] == invite["invite"]["id"]
    beta_friends_before_accept = client.get("/v1/friends", headers=learner_b_headers).json()
    assert beta_friends_before_accept["incomingInvites"][0]["id"] == invite["invite"]["id"]
    accepted = client.post(f"/v1/friends/invites/{invite['invite']['id']}/accept", headers=learner_b_headers).json()
    assert accepted["accepted"] is True
    assert accepted["relationship"]["friendLearnerId"] == "gamification-alpha"
    alpha_social_achievements = client.get("/v1/achievements/me", headers=learner_a_headers).json()
    social_starter = next(item for item in alpha_social_achievements["achievements"] if item["key"] == "social_starter")
    assert social_starter["awarded"] is True
    assert social_starter["rewardGems"] == 1
    alpha_friends = client.get("/v1/friends", headers=learner_a_headers).json()
    assert alpha_friends["friendCount"] == 1
    assert alpha_friends["friends"][0]["friendLearnerId"] == "gamification-beta"
    gamma_conv = client.post(
        "/v1/conversations",
        headers=learner_c_headers,
        json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
    ).json()
    client.post(
        f"/v1/conversations/{gamma_conv['conversationId']}/turns",
        headers=learner_c_headers,
        json={"inputType": "text", "text": "오늘은 친구랑 공부했어", "requestTts": False},
    )
    delta_conv = client.post(
        "/v1/conversations",
        headers=learner_d_headers,
        json={"personaId": "yui", "practiceRoomId": "cant_go_today", "mode": "practice"},
    ).json()
    client.post(
        f"/v1/conversations/{delta_conv['conversationId']}/turns",
        headers=learner_d_headers,
        json={"inputType": "text", "text": "오늘은 약속에 못 가", "requestTts": False},
    )
    epsilon_conv = client.post(
        "/v1/conversations",
        headers=learner_e_headers,
        json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
    ).json()
    client.post(
        f"/v1/conversations/{epsilon_conv['conversationId']}/turns",
        headers=learner_e_headers,
        json={"inputType": "text", "text": "오늘은 비공개로 공부할래", "requestTts": False},
    )
    private_settings = client.put(
        "/v1/social/settings",
        headers=learner_e_headers,
        json={"discoverable": False, "allowFriendInvites": False, "showWeeklyXp": False},
    ).json()
    assert private_settings["discoverable"] is False
    zeta_conv = client.post(
        "/v1/conversations",
        headers=learner_f_headers,
        json={"personaId": "yui", "practiceRoomId": "tired_today", "mode": "practice"},
    ).json()
    client.post(
        f"/v1/conversations/{zeta_conv['conversationId']}/turns",
        headers=learner_f_headers,
        json={"inputType": "text", "text": "오늘은 친구 차단 테스트야", "requestTts": False},
    )
    blocked_zeta = client.post("/v1/social/blocks/gamification-zeta", headers=learner_a_headers).json()
    assert blocked_zeta["blocked"] is True
    assert blocked_zeta["block"]["blockedLearnerId"] == "gamification-zeta"
    assert client.get("/v1/social/blocks", headers=learner_a_headers).json()["count"] == 1
    blocked_invite = client.post(
        "/v1/friends/invites",
        headers=learner_a_headers,
        json={"friendLearnerId": "gamification-zeta", "message": "차단 후 초대 확인"},
    )
    assert blocked_invite.status_code == 409
    assert blocked_invite.json()["detail"]["reason"] == "blocked"
    pending_delta = client.post(
        "/v1/friends/invites",
        headers=learner_a_headers,
        json={"friendLearnerId": "gamification-delta", "message": "추천 제외 확인"},
    ).json()
    assert pending_delta["created"] is True
    friend_recommendations = client.get("/v1/friends/recommendations", headers=learner_a_headers).json()
    recommended_ids = {item["learnerId"] for item in friend_recommendations["recommendations"]}
    assert "gamification-gamma" in recommended_ids
    assert "gamification-beta" not in recommended_ids
    assert "gamification-delta" not in recommended_ids
    assert "gamification-epsilon" not in recommended_ids
    assert "gamification-zeta" not in recommended_ids
    assert friend_recommendations["excludedFriendCount"] >= 1
    assert friend_recommendations["excludedPendingInviteCount"] >= 1
    assert friend_recommendations["excludedPrivateCount"] >= 1
    assert friend_recommendations["excludedBlockedCount"] >= 1
    gamma_recommendation = next(item for item in friend_recommendations["recommendations"] if item["learnerId"] == "gamification-gamma")
    assert gamma_recommendation["score"] > 0
    assert "target_language_match" in gamma_recommendation["reasonCodes"]
    assert gamma_recommendation["alreadyFriend"] is False
    assert gamma_recommendation["pendingInvite"] is False
    social_discovery = client.get("/v1/social/discovery", headers=learner_a_headers, params={"limit": 10, "targetLanguage": "ja"}).json()
    discovered_ids = {item["learnerId"] for item in social_discovery["candidates"]}
    assert "gamification-gamma" in discovered_ids
    assert "gamification-beta" not in discovered_ids
    assert "gamification-delta" not in discovered_ids
    assert "gamification-epsilon" not in discovered_ids
    assert "gamification-zeta" not in discovered_ids
    assert social_discovery["excludedFriendOrPendingCount"] >= 2
    assert social_discovery["excludedPrivateCount"] >= 1
    assert social_discovery["excludedBlockedCount"] >= 1
    gamma_discovery = next(item for item in social_discovery["candidates"] if item["learnerId"] == "gamification-gamma")
    assert gamma_discovery["canInvite"] is True
    assert gamma_discovery["friendQuestEligible"] is True
    assert "target_language_match" in gamma_discovery["reasonCodes"]

    shop_admin_viewer_headers = {
        "X-Admin-Key": "local-dev-admin",
        "X-Admin-Role": "viewer",
        "X-Admin-User": "shop-viewer",
    }
    shop_admin_editor_headers = {
        "X-Admin-Key": "local-dev-admin",
        "X-Admin-Role": "editor",
        "X-Admin-User": "shop-editor",
    }
    admin_shop = client.get("/v1/admin/rewards/shop", headers=shop_admin_viewer_headers).json()
    assert admin_shop["count"] >= 2
    assert any(item["rewardKey"] == "streak_freeze_1" for item in admin_shop["items"])
    viewer_update_rejected = client.put(
        "/v1/admin/rewards/shop/streak_freeze_1",
        headers=shop_admin_viewer_headers,
        json={"priceCurrency": "gems", "priceAmount": 2, "available": True, "dailyPurchaseLimit": 1, "inventoryLimit": 1, "sortOrder": 5},
    )
    assert viewer_update_rejected.status_code == 403
    updated_shop_item = client.put(
        "/v1/admin/rewards/shop/streak_freeze_1",
        headers=shop_admin_editor_headers,
        json={"priceCurrency": "gems", "priceAmount": 2, "available": True, "dailyPurchaseLimit": 1, "inventoryLimit": 1, "sortOrder": 5},
    ).json()
    assert updated_shop_item["updated"] is True
    assert updated_shop_item["item"]["dailyPurchaseLimit"] == 1
    assert updated_shop_item["item"]["inventoryLimit"] == 1
    assert updated_shop_item["item"]["updatedBy"] == "shop-editor"

    shop = client.get("/v1/rewards/shop", headers=learner_a_headers).json()
    shop_gem_balance_before = next(item for item in shop["balances"] if item["currencyKey"] == "gems")["balance"]
    assert shop_gem_balance_before >= 2
    streak_freeze = next(item for item in shop["items"] if item["rewardKey"] == "streak_freeze_1")
    assert streak_freeze["affordable"] is True
    assert streak_freeze["dailyPurchaseLimit"] == 1
    assert streak_freeze["remainingDailyPurchases"] == 1
    assert streak_freeze["inventoryLimit"] == 1
    purchased = client.post("/v1/rewards/shop/streak_freeze_1/purchase", headers=learner_a_headers).json()
    assert purchased["purchased"] is True
    assert purchased["inventoryItem"]["rewardKey"] == "streak_freeze_1"
    assert next(item for item in purchased["shop"]["balances"] if item["currencyKey"] == "gems")["balance"] == shop_gem_balance_before - 2
    purchased_streak_freeze = next(item for item in purchased["shop"]["items"] if item["rewardKey"] == "streak_freeze_1")
    assert purchased_streak_freeze["remainingDailyPurchases"] == 0
    assert purchased_streak_freeze["remainingInventory"] == 0
    second_purchase = client.post("/v1/rewards/shop/streak_freeze_1/purchase", headers=learner_a_headers)
    assert second_purchase.status_code == 409
    assert second_purchase.json()["detail"]["reason"] == "daily_purchase_limit_reached"

    friend_quests = client.get(
        "/v1/friends/quests",
        headers=learner_a_headers,
        params={"partnerLearnerId": "gamification-beta"},
    ).json()
    quest = friend_quests["friendQuests"][0]
    assert quest["partnerLearnerId"] == "gamification-beta"
    assert quest["combinedXp"] >= 40
    assert quest["completed"] is True
    assert quest["claimed"] is False

    claimed = client.post(f"/v1/friends/quests/{quest['id']}/claim", headers=learner_a_headers).json()
    assert claimed["claimed"] is True
    assert claimed["alreadyClaimed"] is False
    assert claimed["rewardItem"]["rewardKey"] == "xp_boost_2x_15m"
    assert claimed["rewardItem"]["quantity"] == 1
    alpha_friend_quest_achievements = client.get("/v1/achievements/me", headers=learner_a_headers).json()
    alpha_awarded_keys = {
        item["key"] for item in alpha_friend_quest_achievements["achievements"] if item["awarded"]
    }
    assert {"social_starter", "friend_quester"} <= alpha_awarded_keys
    assert alpha_friend_quest_achievements["awardedCount"] >= 7
    claimed_again = client.post(f"/v1/friends/quests/{quest['id']}/claim", headers=learner_a_headers).json()
    assert claimed_again["alreadyClaimed"] is True
    assert claimed_again["rewardItem"]["quantity"] == 1

    activated = client.post("/v1/rewards/boosts/xp_boost_2x_15m/activate", headers=learner_a_headers).json()
    assert activated["activated"] is True
    assert activated["activeBoost"]["multiplier"] == 2.0
    activated_xp_boost_item = next(item for item in activated["inventory"]["items"] if item["rewardKey"] == "xp_boost_2x_15m")
    assert activated_xp_boost_item["quantity"] == 0
    inventory = client.get("/v1/rewards/inventory", headers=learner_a_headers).json()
    assert inventory["activeXpBoosts"][0]["rewardKey"] == "xp_boost_2x_15m"

    before_boost_xp = client.get("/v1/gamification/me", headers=learner_a_headers).json()["xp"]["todayXp"]
    boost_conv = client.post(
        "/v1/conversations",
        headers=learner_a_headers,
        json={"personaId": "yui", "practiceRoomId": "cant_go_today", "mode": "practice"},
    ).json()
    client.post(
        f"/v1/conversations/{boost_conv['conversationId']}/turns",
        headers=learner_a_headers,
        json={"inputType": "text", "text": "전철이 늦었어", "requestTts": False},
    )
    boosted_gamification = client.get("/v1/gamification/me", headers=learner_a_headers).json()
    assert boosted_gamification["xp"]["todayXp"] >= before_boost_xp + 30
    beta_friend_quest = next(
        item for item in boosted_gamification["friendQuests"] if item["partnerLearnerId"] == "gamification-beta"
    )
    assert beta_friend_quest["claimed"] is True
    assert any(item["rewardKey"] == "xp_boost_2x_15m" for item in boosted_gamification["rewardInventory"]["items"])
    assert any(item["rewardKey"] == "streak_freeze_1" for item in boosted_gamification["rewardInventory"]["items"])
    assert boosted_gamification["activeXpBoosts"][0]["multiplier"] == 2.0
    boosted_flag = next(
        flag for flag in boosted_gamification["xpAbuseFlags"] if flag["reason"] == "boosted_xp_soft_limit_exceeded"
    )
    assert boosted_flag["severity"] == "block"
    assert boosted_flag["status"] == "open"
    assert boosted_flag["leaderboardExcluded"] is True
    excluded_leaderboard = client.get("/v1/leaderboards/weekly", headers=learner_a_headers).json()
    excluded_alpha_entry = next(item for item in excluded_leaderboard["entries"] if item["learnerId"] == "gamification-alpha")
    assert excluded_alpha_entry["leaderboardExcluded"] is True
    assert "boosted_xp_soft_limit_exceeded" in excluded_alpha_entry["exclusionReasons"]
    assert excluded_leaderboard["currentLearnerRank"] is None
    admin_headers = {"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "viewer"}
    admin_flags = client.get(
        "/v1/admin/xp-abuse-flags",
        headers=admin_headers,
        params={"learnerId": "gamification-alpha", "status": "open"},
    ).json()
    assert admin_flags["count"] >= 1
    assert any(flag["id"] == boosted_flag["id"] for flag in admin_flags["flags"])
    reputation = client.get("/v1/reputation/me", headers=learner_a_headers).json()
    assert reputation["learnerId"] == "gamification-alpha"
    assert reputation["riskBand"] in {"high", "critical"}
    assert reputation["riskScore"] >= 45
    assert reputation["reviewRecommended"] is True
    assert reputation["leaderboardEligible"] is False
    assert reputation["summary"]["openXpAbuseFlagCount"] >= 2
    assert reputation["summary"]["blockingXpAbuseFlagCount"] >= 1
    assert any(signal["key"] == "xp_abuse:boosted_xp_soft_limit_exceeded" for signal in reputation["signals"])
    admin_reputation_queue = client.get(
        "/v1/admin/reputation/learners",
        headers=admin_headers,
        params={"band": reputation["riskBand"]},
    ).json()
    assert admin_reputation_queue["count"] >= 1
    assert any(profile["learnerId"] == "gamification-alpha" for profile in admin_reputation_queue["profiles"])
    admin_reputation_detail = client.get(
        "/v1/admin/reputation/learners/gamification-alpha",
        headers=admin_headers,
    ).json()
    assert admin_reputation_detail["riskScore"] == reputation["riskScore"]
    assert admin_reputation_detail["summary"]["incomingBlockCount"] == reputation["summary"]["incomingBlockCount"]
    reviewed = client.post(
        f"/v1/admin/xp-abuse-flags/{boosted_flag['id']}/status",
        headers={"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "reviewer", "X-Admin-User": "ops-reviewer"},
        json={"status": "resolved", "note": "boosted XP reviewed for test evidence"},
    ).json()
    assert reviewed["ok"] is True
    assert reviewed["flag"]["status"] == "resolved"
    assert reviewed["flag"]["leaderboardExcluded"] is False
    restored_leaderboard = client.get("/v1/leaderboards/weekly", headers=learner_a_headers).json()
    restored_alpha_entry = next(item for item in restored_leaderboard["entries"] if item["learnerId"] == "gamification-alpha")
    assert restored_alpha_entry["leaderboardExcluded"] is False
    assert restored_leaderboard["currentLearnerRank"] == 1

    progress = client.get("/v1/progress/today", headers=learner_a_headers).json()
    assert progress["xpEarnedToday"] == boosted_gamification["xp"]["todayXp"]
    assert progress["dailyQuestsCompleted"] >= 3

    providers = client.get("/v1/providers/status").json()
    assert providers["operations"]["gamification"]["xpLedger"] is True
    assert providers["operations"]["gamification"]["dailyQuests"] is True
    assert providers["operations"]["gamification"]["weeklyLeaderboard"] is True
    assert providers["operations"]["gamification"]["achievements"] is True
    assert providers["operations"]["gamification"]["achievementLevels"] is True
    assert providers["operations"]["gamification"]["achievementRewardCurrency"] is True
    assert providers["operations"]["gamification"]["leagueTiers"] is True
    assert providers["operations"]["gamification"]["xpAnomalyFlags"] is True
    assert providers["operations"]["gamification"]["friendQuests"] is True
    assert providers["operations"]["gamification"]["friendGraph"] is True
    assert providers["operations"]["gamification"]["friendInvites"] is True
    assert providers["operations"]["gamification"]["friendRecommendations"] is True
    assert providers["operations"]["gamification"]["socialDiscovery"] is True
    assert providers["operations"]["gamification"]["socialPrivacySettings"] is True
    assert providers["operations"]["gamification"]["socialBlocking"] is True
    assert providers["operations"]["gamification"]["rewardCurrencyLedger"] is True
    assert providers["operations"]["gamification"]["rewardShop"] is True
    assert providers["operations"]["gamification"]["rewardShopOperations"] is True
    assert providers["operations"]["gamification"]["rewardShopPurchaseLimits"] is True
    assert providers["operations"]["gamification"]["rewardInventory"] is True
    assert providers["operations"]["gamification"]["xpBoosts"] is True
    assert providers["operations"]["gamification"]["boostedXpLedger"] is True
    assert providers["operations"]["gamification"]["singleSourceAnomalyFlags"] is True
    assert providers["operations"]["gamification"]["boostAbuseFlags"] is True
    assert providers["operations"]["gamification"]["leaderboardExclusionFlags"] is True
    assert providers["operations"]["gamification"]["xpAbuseReviewQueue"] is True
    assert providers["operations"]["gamification"]["multiSignalReputation"] is True
    assert providers["operations"]["gamification"]["reputationReviewQueue"] is True
    assert providers["operations"]["gamification"]["offlineReputationModelEvaluation"] is True
    assert providers["operations"]["gamification"]["productionLearnedAntiCheatModel"] is False

    privacy = client.delete("/v1/privacy/me", headers=learner_a_headers).json()
    assert privacy["deletedCounts"]["xpEvents"] >= 4
    assert privacy["deletedCounts"]["achievementAwards"] >= 7
    assert privacy["deletedCounts"]["xpAbuseFlags"] >= 1
    assert privacy["deletedCounts"]["rewardCurrencyEvents"] >= 3
    assert privacy["deletedCounts"]["rewardShopPurchases"] >= 1
    assert privacy["deletedCounts"]["friendInvites"] >= 1
    assert privacy["deletedCounts"]["friendRelationships"] >= 1
    assert privacy["deletedCounts"]["friendQuests"] >= 1
    assert privacy["deletedCounts"]["socialSettings"] >= 1
    assert privacy["deletedCounts"]["socialBlocks"] >= 1
    assert privacy["deletedCounts"]["rewardInventoryItems"] >= 2
    assert privacy["deletedCounts"]["xpBoosts"] >= 1


def test_tts_cache_stt_manual_review_event_and_entitlements(tmp_path):
    client = make_client(tmp_path)

    first_tts = client.post(
        "/v1/tts/synthesize",
        json={"text": "今日めっちゃ疲れた。", "personaId": "yui", "language": "ja"},
    ).json()
    second_tts = client.post(
        "/v1/tts/synthesize",
        json={"text": "今日めっちゃ疲れた。", "personaId": "yui", "language": "ja"},
    ).json()
    assert first_tts["provider"] == "mock"
    assert first_tts["cacheHit"] is False
    persona_voices = json.loads((API_ROOT / "app" / "persona_voices.json").read_text(encoding="utf-8"))
    assert first_tts["voiceUsed"] == persona_voices["yui"]["emotions"]["gentle"]
    assert second_tts["cacheHit"] is True
    assert second_tts["audioBase64"] == first_tts["audioBase64"]

    stt = client.post("/v1/stt/transcribe", json={"language": "ja", "mockText": "今日は疲れるだった"}).json()
    assert stt["text"] == "今日は疲れるだった"
    assert stt["provider"] == "mock"
    assert stt["confidence"] == 0.92
    assert stt["latencyMs"] >= 0

    created = client.post(
        "/v1/review-cards",
        json={"front": "멘탈 나갔어", "back": "今日メンタルやられた。", "tags": ["감정표현"]},
    ).json()["reviewCard"]
    assert created["id"].startswith("card_")

    event = client.post("/v1/events", json={"eventName": "home_today_viewed", "payload": {"screen": "HomeTodayScreen"}})
    assert event.status_code == 200
    assert event.json() == {"ok": True}

    entitlements = client.get("/v1/entitlements/me").json()
    assert entitlements["plan"] == "master_sandbox"
    assert entitlements["premiumVoices"] is True


def test_stt_transcribe_accepts_multipart_form_upload_and_hint_formats(tmp_path):
    app = create_app(tmp_path / "multipart-stt.sqlite3")
    captured = {}

    class CapturingSTT:
        provider = "capture_stt"

        def transcribe(self, request):
            captured.clear()
            captured.update(request)
            return {
                "text": request.get("mockText") or "ok",
                "provider": self.provider,
                "confidence": 0.91,
                "sttSeconds": 1.25,
                "latencyMs": 3,
            }

    app.state.stt = CapturingSTT()
    client = TestClient(app)

    response = client.post(
        "/v1/stt/transcribe",
        data={"language": "ja", "mockText": "今日は疲れました", "hintLineIds": '["line_a","line_b"]'},
        files={"file": ("utterance.webm", b"fake-webm", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "今日は疲れました"
    assert captured["language"] == "ja"
    assert captured["hintLineIds"] == ["line_a", "line_b"]
    assert captured["audioBase64"].startswith("data:audio/webm;base64,")
    assert base64.b64decode(captured["audioBase64"].split(",", 1)[1]) == b"fake-webm"

    comma_response = client.post(
        "/v1/stt/transcribe",
        data={"language": "ja", "hintLineIds": "line_c,line_d"},
        files={"file": ("utterance.m4a", b"fake-m4a", "audio/mp4")},
    )
    assert comma_response.status_code == 200
    assert captured["hintLineIds"] == ["line_c", "line_d"]

    repeated_response = client.post(
        "/v1/stt/transcribe",
        data={"language": "ja"},
        files=[
            ("hintLineIds", (None, "")),
            ("hintLineIds", (None, "line_e")),
            ("hintLineIds", (None, " ")),
            ("hintLineIds", (None, "line_e")),
            ("hintLineIds", (None, "line_f")),
            ("file", ("utterance.wav", b"fake-wav", "audio/wav")),
        ],
    )
    assert repeated_response.status_code == 200
    assert captured["hintLineIds"] == ["line_e", "line_f"]

    empty_array_response = client.post(
        "/v1/stt/transcribe",
        data={"language": "ja", "hintLineIds": "[]"},
        files={"file": ("utterance.wav", b"fake-wav", "audio/wav")},
    )
    assert empty_array_response.status_code == 200
    assert captured["hintLineIds"] == []

    empty_string_response = client.post(
        "/v1/stt/transcribe",
        data={"language": "ja", "hintLineIds": ""},
        files={"file": ("utterance.wav", b"fake-wav", "audio/wav")},
    )
    assert empty_string_response.status_code == 200
    assert captured["hintLineIds"] == []

    sparse_comma_response = client.post(
        "/v1/stt/transcribe",
        data={"language": "ja", "hintLineIds": "line_g,,line_h"},
        files={"file": ("utterance.wav", b"fake-wav", "audio/wav")},
    )
    assert sparse_comma_response.status_code == 200
    assert captured["hintLineIds"] == ["line_g", "line_h"]

    bracket_text_response = client.post(
        "/v1/stt/transcribe",
        data={"language": "ja", "hintLineIds": "not-json-but-has-[bracket"},
        files={"file": ("utterance.wav", b"fake-wav", "audio/wav")},
    )
    assert bracket_text_response.status_code == 200
    assert captured["hintLineIds"] == ["not-json-but-has-[bracket"]


def test_stt_transcribe_rejects_malformed_or_excessive_hint_line_ids(tmp_path):
    client = make_client(tmp_path)
    too_many_hints = ",".join(f"line_{index}" for index in range(101))
    cases = [
        ('["line_a",3,null]', "hintLineIds JSON array must contain only strings"),
        ("[not-json", "hintLineIds JSON array is malformed"),
        ("x" * 161, "hintLineIds value is too long"),
        (too_many_hints, "Too many hintLineIds"),
    ]

    for raw_hints, expected_detail in cases:
        response = client.post(
            "/v1/stt/transcribe",
            data={"language": "ja", "hintLineIds": raw_hints},
            files={"file": ("utterance.wav", b"fake-wav", "audio/wav")},
        )
        assert response.status_code == 422
        assert response.json()["detail"] == expected_detail

    json_response = client.post(
        "/v1/stt/transcribe",
        json={"language": "ja", "hintLineIds": ["line_a", 3, None]},
    )
    assert json_response.status_code == 422
    assert json_response.json()["detail"] == "hintLineIds values must be strings"


def test_voice_gallery_dialogue_pack_match_and_unmatched_log(tmp_path):
    client = make_client(tmp_path)

    voices = client.get("/v1/voices").json()
    assert len(voices) >= 30
    assert all(voice["creditText"] for voice in voices)
    assert any(voice["personaId"] == "yui" for voice in voices)

    packs = client.get("/v1/dialogue/packs").json()
    yui_pack = next(pack for pack in packs if pack["personaId"] == "yui" and pack["packVersion"] == "v1")
    assert yui_pack["scenarioCount"] == 10
    assert yui_pack["audioCount"] == 75

    zip_response = client.get("/v1/dialogue/packs/yui/v1.zip")
    assert zip_response.status_code == 200
    assert zip_response.content.startswith(b"PK")

    match = client.post(
        "/v1/dialogue/match",
        json={
            "personaId": "yui",
            "packVersion": "v1",
            "utterance": "こんにちは",
            "candidateLineIds": ["yui_greetings_intro_n5_u01a", "yui_greetings_intro_n5_u01b"],
            "globalIntents": True,
        },
    ).json()
    assert match["tier"] == "match"
    assert match["matchedLineId"] == "yui_greetings_intro_n5_u01a"
    assert match["score"] >= 0.75
    assert match["latencyMs"] < 50

    repeat = client.post(
        "/v1/dialogue/match",
        json={"personaId": "yui", "packVersion": "v1", "utterance": "もう一回", "candidateLineIds": []},
    ).json()
    assert repeat["globalIntent"] == "repeat"

    fallback = client.post(
        "/v1/dialogue/match",
        json={
            "personaId": "yui",
            "packVersion": "v1",
            "utterance": "宇宙船を修理したい",
            "candidateLineIds": ["yui_greetings_intro_n5_u01a", "yui_greetings_intro_n5_u01b"],
        },
    ).json()
    assert fallback["tier"] == "fallback"

    unmatched = client.post(
        "/v1/dialogue/unmatched",
        json={"personaId": "yui", "packVersion": "v1", "nodeId": "node_1", "utterance": "宇宙船を修理したい", "sttConfidence": 0.41},
    )
    assert unmatched.status_code == 202
    assert unmatched.json()["accepted"] is True

    status = client.get("/v1/providers/status").json()
    assert status["providers"]["dialogue"]["engine"] == "bank"
    assert status["providers"]["dialogue"]["runtimeLlmCalls"] is False

@pytest.mark.parametrize(
    "bad_persona_id",
    [
        "..",
        "../x",
        "..%2Fx",
        "%2e%2e",
        "%2e%2e%2Fx",
    ],
)
def test_dialogue_pack_zip_rejects_path_traversal(tmp_path, bad_persona_id):
    client = make_client(tmp_path)
    response = client.get(f"/v1/dialogue/packs/{bad_persona_id}/v1.zip")
    assert response.status_code in (400, 404)

def test_dialogue_authoring_validation_scripts_are_green():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "authoring" / "validate_bank.py")],
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["scenarioFiles"] == 30
    assert payload["variants"] >= 30 * 6 * 2 * 8


def test_audio_turn_safety_and_not_found_responses(tmp_path):
    client = make_client(tmp_path)

    missing = client.post("/v1/conversations", json={"personaId": "missing", "practiceRoomId": "tired_today"})
    assert missing.status_code == 404

    conv = client.post("/v1/conversations", json={"personaId": "yui", "practiceRoomId": "tired_today"}).json()
    audio_turn = client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        json={"inputType": "mock_audio", "text": "今日は疲れるだった", "requestTts": False},
    ).json()
    assert audio_turn["userText"] == "今日は疲れるだった"
    assert audio_turn["corrections"][0]["category"] == "verb_tense"
    assert audio_turn["audioUrl"] is None
    assert audio_turn["usage"]["sttSeconds"] >= 2.0

    blocked = client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        json={"inputType": "text", "text": "미성년자 야한 롤플레이 해줘", "requestTts": False},
    ).json()
    assert blocked["reviewCards"] == []
    assert "성적/미성년자" in blocked["assistantText"]


def test_105_score_backend_extensions_cover_srs_profile_recommendations_and_export(tmp_path):
    client = make_client(tmp_path)

    profile = client.put(
        "/v1/profile/me",
        json={
            "level": "intermediate",
            "jlptLevel": "N3",
            "weakTags": ["감정표현", "친구말투"],
            "preferredPersonaId": "yui",
        },
    ).json()["profile"]
    assert profile["level"] == "intermediate"
    assert profile["jlptLevel"] == "N3"

    conv = client.post("/v1/conversations", json={"personaId": "yui", "practiceRoomId": "tired_today"}).json()
    audio_turn = client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        json={"inputType": "mock_audio", "text": "今日めっちゃ疲れた", "requestTts": True},
    ).json()
    assert audio_turn["pronunciation"]["score"] >= 90
    assert audio_turn["pronunciation"]["rating"] == "excellent"
    client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        json={"inputType": "mock_audio", "text": "今日は疲れるだった", "requestTts": False},
    )

    due = client.get("/v1/review-cards/due").json()["reviewCards"]
    assert due
    assert due[0]["recallRisk"] == "new"
    assert due[0]["recallProbability"] == 0.0
    graded = client.post(f"/v1/review-cards/{due[0]['id']}/grade", json={"quality": 5}).json()["reviewCard"]
    assert graded["reviewCount"] == 1
    assert graded["intervalDays"] == 1
    assert graded["easeFactor"] > 2.5
    assert graded["memoryStrengthDays"] >= 1.0
    assert 0.0 <= graded["recallProbability"] <= 1.0
    assert graded["recallRisk"] in {"low", "medium"}
    assert graded["lastReviewQuality"] == 5

    memory = client.get("/v1/memory/summary").json()
    assert memory["model"] == "hlr_inspired_local_estimator_v1"
    assert memory["cardCount"] >= 1
    assert memory["reviewedCardCount"] >= 1
    assert any(item["tag"] == "감정표현" for item in memory["tagMastery"])
    assert "감정표현" in memory["pressureTags"] or memory["averageRecallProbability"] is not None

    recommendations = client.get("/v1/recommendations/today").json()
    assert recommendations["profile"]["jlptLevel"] == "N3"
    assert recommendations["recommendedPracticeRooms"][0]["practiceRoom"]["id"] == "tired_today"
    assert recommendations["nextBestAction"] in {"review_due_cards", "start_practice_room", "repair_memory"}
    assert any(item["category"] == "verb_tense" for item in recommendations["signalSummary"]["correctionCategories"])
    assert "동사시제" in recommendations["signalSummary"]["pressureTags"]
    assert recommendations["memorySummary"]["cardCount"] == memory["cardCount"]

    anki = client.get("/v1/export/anki").json()
    assert anki["format"] == "csv"
    assert "front,back,example,tags,dueAt,reviewCount,easeFactor" in anki["content"]
    assert "今日めっちゃ疲れた" in anki["content"]

    anki_apkg = client.get("/v1/export/anki-apkg").json()
    assert anki_apkg["format"] == "apkg"
    assert anki_apkg["noteCount"] >= 1
    assert base64.b64decode(anki_apkg["contentBase64"]).startswith(b"PK")

    anki_connect = client.post("/v1/export/anki-connect", json={"deckName": "AI JP", "apply": False}).json()
    assert anki_connect["ok"] is True
    assert anki_connect["dryRun"] is True
    assert anki_connect["notes"][0]["deckName"] == "AI JP"
    assert anki_connect["notes"][0]["fields"]["Front"]

    grammar = client.get("/v1/grammar/jlpt?level=N5").json()["grammarPoints"]
    assert any(point["id"] == "grammar_n5_ta_past" for point in grammar)

    weaknesses = client.get("/v1/weaknesses/summary").json()
    assert any(item["tag"] == "감정표현" for item in weaknesses["weakTags"])
    assert weaknesses["recommendedGrammar"]
    assert weaknesses["recommendedMistakes"]

    mistakes = client.get("/v1/mistakes/korean-patterns?tag=감정표현").json()["mistakePatterns"]
    assert any(pattern["id"] == "km_verb_past_tired" for pattern in mistakes)

    providers = client.get("/v1/providers/status").json()
    assert providers["externalApiKeysRequired"] is False
    assert "SRS scheduler" in providers["openCoreBoundary"]["publicCore"]
    assert "acoustic pronunciation adapter" in providers["openCoreBoundary"]["publicCore"]
    assert providers["operations"]["auditLogging"] is True
    assert providers["operations"]["privacyDeletion"] is True
    assert providers["operations"]["rateLimit"]["backend"] == "memory"
    assert providers["operations"]["content"]["translationMemory"] is True
    assert providers["operations"]["content"]["bulkQa"] is True
    assert providers["operations"]["content"]["branchingAssignments"] is True
    assert providers["operations"]["learnerModel"]["offlineTrainEvaluatePipeline"] is True
    assert providers["operations"]["learnerModel"]["offlineModelName"] == "offline_logistic_memory_model_v1"
    assert providers["operations"]["learnerModel"]["productionTrainedModel"] is False

    usage = client.get("/v1/usage/summary").json()["usage"]
    assert usage["ttsCharacters"] >= len("今日めっちゃ疲れた。")
    assert usage["ttsCacheEntries"] >= 1

    assert (API_ROOT / "Dockerfile").exists()
    assert (API_ROOT / "docker-compose.yml").exists()


def test_offline_learner_memory_model_train_eval_pipeline_and_script_artifact(tmp_path):
    result = train_evaluate_memory_model(db_examples=fixture_examples()[:4], include_fixture=True)
    assert result["status"] == "evaluated"
    assert result["modelName"] == "offline_logistic_memory_model_v1"
    assert result["trainCount"] > 0
    assert result["evaluation"]["exampleCount"] > 0
    assert result["evaluation"]["accuracy"] is not None
    assert result["productionTrained"] is False

    output = tmp_path / "learner_model_evaluation.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(API_ROOT / "scripts" / "evaluate_learner_model.py"),
            "--db-path",
            str(tmp_path / "learner-model.sqlite3"),
            "--output",
            str(output),
        ],
        cwd=API_ROOT,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["status"] == "evaluated"
    assert artifact["fixtureIncluded"] is True
    assert artifact["fixtureExampleCount"] > 0
    assert artifact["evaluation"]["exampleCount"] > 0
    assert artifact["productionTrained"] is False


def test_acoustic_pronunciation_dataset_depth_privacy_and_audit(tmp_path):
    client = make_client(tmp_path)

    tts = client.post(
        "/v1/tts/synthesize",
        json={"text": "今日めっちゃ疲れた。", "personaId": "yui", "language": "ja"},
    ).json()
    scored = client.post(
        "/v1/pronunciation/score",
        json={
            "expectedText": "今日めっちゃ疲れた。",
            "actualText": "今日めっちゃ疲れた。",
            "audioBase64": tts["audioBase64"],
        },
    ).json()
    assert scored["provider"] == "acoustic_feature_mock"
    assert scored["scoringMode"] == "text_plus_acoustic_features"
    assert scored["acousticEvidencePresent"] is True
    assert scored["acousticFeatures"]["durationMs"] > 0
    assert scored["score"] >= 85

    grammar = client.get("/v1/grammar/jlpt").json()["grammarPoints"]
    mistakes = client.get("/v1/mistakes/korean-patterns").json()["mistakePatterns"]
    assert len(grammar) >= 16
    assert len(mistakes) >= 13
    assert any(point["id"] == "grammar_n4_te_miru" for point in grammar)
    assert any(pattern["id"] == "km_while_shadowing" for pattern in mistakes)

    learner_headers = {"X-Learner-Id": "test-user", "X-User-Id": "test-user"}
    conv = client.post(
        "/v1/conversations",
        headers=learner_headers,
        json={"personaId": "yui", "practiceRoomId": "tired_today"},
    ).json()
    client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        headers=learner_headers,
        json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
    )
    deleted = client.delete("/v1/privacy/me", headers=learner_headers).json()
    assert deleted["ok"] is True
    assert deleted["deletedCounts"]["conversations"] >= 1
    assert client.get("/v1/review-cards").json()["reviewCards"] == []
    audit_logs = client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
    assert any(log["action"] == "privacy_deletion_completed" for log in audit_logs)


def test_rate_limiting_records_audit_log(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE", "2")
    monkeypatch.setattr("app.rate_limit.time.time", lambda: 1_725_000_000.0)
    client = TestClient(create_app(tmp_path / "rate-limit.sqlite3"))
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
    limited = client.get("/health")
    assert limited.status_code == 429
    assert limited.json()["detail"] == "Rate limit exceeded"
    audit_logs = client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
    assert any(log["action"] == "rate_limit_exceeded" for log in audit_logs)


def test_rate_limiting_uses_learner_hint_to_avoid_cross_learner_localhost_collisions(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_RATE_LIMIT_PER_MINUTE", "1")
    monkeypatch.setattr("app.rate_limit.time.time", lambda: 1_725_000_000.0)
    client = TestClient(create_app(tmp_path / "rate-limit-learners.sqlite3"))

    assert client.get("/health", headers={"X-Learner-Id": "alpha"}).status_code == 200
    assert client.get("/health", headers={"X-Learner-Id": "beta"}).status_code == 200
    assert client.get("/health", headers={"X-Learner-Id": "alpha"}).status_code == 429


def test_rate_limiter_redis_mode_falls_back_without_leaking_redis_url(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_REDIS_URL", "redis://:secret-password@127.0.0.1:6390/0")
    client = TestClient(create_app(tmp_path / "rate-limit-redis-fallback.sqlite3"))

    response = client.get("/v1/providers/status")
    assert response.status_code == 200
    rate_limit = response.json()["operations"]["rateLimit"]
    assert rate_limit["backend"] in {"memory", "redis"}
    serialized = str(response.json())
    assert "secret-password" not in serialized
    if rate_limit["backend"] == "memory":
        assert rate_limit["requestedBackend"] == "redis"
        assert rate_limit["fallbackReason"].startswith("redis_unavailable:")


def test_learner_scoping_prevents_cross_user_review_visibility_and_deletion(tmp_path):
    client = make_client(tmp_path)

    alpha = {"X-Learner-Id": "alpha"}
    beta = {"X-Learner-Id": "beta"}
    alpha_conv = client.post(
        "/v1/conversations",
        headers=alpha,
        json={"personaId": "yui", "practiceRoomId": "tired_today"},
    ).json()
    client.post(
        f"/v1/conversations/{alpha_conv['conversationId']}/turns",
        headers=alpha,
        json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
    )

    assert client.get("/v1/review-cards", headers=alpha).json()["reviewCards"]
    assert client.get("/v1/review-cards", headers=beta).json()["reviewCards"] == []

    cross_turn = client.post(
        f"/v1/conversations/{alpha_conv['conversationId']}/turns",
        headers=beta,
        json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
    )
    assert cross_turn.status_code == 404

    client.delete("/v1/privacy/me", headers=beta)
    assert client.get("/v1/review-cards", headers=alpha).json()["reviewCards"]
    client.delete("/v1/privacy/me", headers=alpha)
    assert client.get("/v1/review-cards", headers=alpha).json()["reviewCards"] == []


def test_token_auth_mode_rejects_unsigned_learner_headers_and_accepts_signed_token(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "token")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_SECRET", "dev-secret")
    client = make_client(tmp_path)

    rejected = client.get("/v1/profile/me", headers={"X-Learner-Id": "alpha"})
    assert rejected.status_code == 401

    token = create_signed_learner_token("alpha", "dev-secret")
    assert token.startswith("v2:alpha:")
    accepted = client.get("/v1/profile/me", headers={"X-Learner-Token": token})
    assert accepted.status_code == 200
    assert accepted.json()["profile"]["learnerId"] == "alpha"

    expired = create_signed_learner_token("alpha", "dev-secret", ttl_seconds=-60)
    assert client.get("/v1/profile/me", headers={"X-Learner-Token": expired}).status_code == 401

    legacy = _legacy_signed_learner_token("alpha", "dev-secret")
    assert client.get("/v1/profile/me", headers={"X-Learner-Token": legacy}).status_code == 401

    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ALLOW_LEGACY_TOKENS", "true")
    assert client.get("/v1/profile/me", headers={"X-Learner-Token": legacy}).status_code == 200

    invalid = client.get("/v1/profile/me", headers={"X-Learner-Token": "v1:alpha:bad"})
    assert invalid.status_code == 401


def test_account_auth_register_refresh_logout_and_learner_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-account-jwt-secret")
    db_path = tmp_path / "account-auth.sqlite3"
    client = TestClient(create_app(db_path))

    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "Learner@example.com",
            "password": "correct-horse-battery",
            "learnerId": "account-alpha",
            "deviceLabel": "ios-simulator",
        },
    )
    assert registered.status_code == 200
    register_payload = registered.json()
    assert register_payload["account"]["email"] == "learner@example.com"
    assert register_payload["account"]["learnerId"] == "account-alpha"
    assert register_payload["account"]["authProvider"] == "password"
    assert register_payload["tokenType"] == "Bearer"
    assert register_payload["accessTokenFormat"] == "jwt_hs256"
    assert register_payload["accessToken"].count(".") == 2
    assert register_payload["refreshToken"].startswith("alp_rt_")
    assert "correct-horse-battery" not in str(register_payload)
    claims = _decode_account_access_jwt(register_payload["accessToken"])
    assert claims
    assert claims["sub"] == register_payload["account"]["id"]
    assert claims["learnerId"] == "account-alpha"
    assert claims["typ"] == "access"
    assert claims["aud"] == "ai-language-partner-mobile"

    with sqlite3.connect(db_path) as conn:
        stored_hash = conn.execute("SELECT password_hash FROM accounts WHERE email = ?", ("learner@example.com",)).fetchone()[0]
        stored_access = conn.execute("SELECT access_token_hash FROM account_sessions").fetchone()[0]
    assert stored_hash.startswith("pbkdf2_sha256$")
    assert stored_hash != "correct-horse-battery"
    assert register_payload["accessToken"] not in stored_access

    duplicate = client.post(
        "/v1/auth/register",
        json={"email": "learner@example.com", "password": "another-password"},
    )
    assert duplicate.status_code == 409

    bearer = {"Authorization": f"Bearer {register_payload['accessToken']}"}
    me = client.get("/v1/auth/me", headers=bearer).json()
    assert me["account"]["learnerId"] == "account-alpha"
    assert me["session"]["deviceLabel"] == "ios-simulator"

    conv = client.post(
        "/v1/conversations",
        headers=bearer,
        json={"personaId": "yui", "practiceRoomId": "tired_today"},
    ).json()
    assert conv["learnerId"] == "account-alpha"
    client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        headers=bearer,
        json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
    )
    assert client.get("/v1/review-cards", headers=bearer).json()["reviewCards"]
    assert client.get("/v1/review-cards", headers={"X-Learner-Id": "account-alpha"}).status_code == 401

    refreshed = client.post(
        "/v1/auth/refresh",
        json={"refreshToken": register_payload["refreshToken"], "deviceLabel": "ios-simulator-refresh"},
    ).json()
    assert refreshed["accessToken"] != register_payload["accessToken"]
    assert client.get("/v1/auth/me", headers=bearer).status_code == 401
    new_bearer = {"Authorization": f"Bearer {refreshed['accessToken']}"}
    assert client.get("/v1/auth/me", headers=new_bearer).json()["session"]["deviceLabel"] == "ios-simulator-refresh"
    assert client.post("/v1/auth/logout", headers=new_bearer).json() == {"ok": True}
    assert client.get("/v1/auth/me", headers=new_bearer).status_code == 401

    bad_login = client.post("/v1/auth/login", json={"email": "learner@example.com", "password": "wrong"})
    assert bad_login.status_code == 401
    good_login = client.post(
        "/v1/auth/login",
        json={"email": "learner@example.com", "password": "correct-horse-battery"},
    )
    assert good_login.status_code == 200
    assert good_login.json()["account"]["learnerId"] == "account-alpha"
    auth_status = client.get("/v1/providers/status", headers={"Authorization": f"Bearer {good_login.json()['accessToken']}"}).json()["operations"]["auth"]
    assert auth_status["jwtAccessTokens"] is True
    assert auth_status["accessTokenFormat"] == "jwt_hs256"
    assert auth_status["jwtSigningSecretConfigured"] is True


def test_oidc_id_token_login_links_external_identity_and_issues_account_session(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-oidc-account-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-oidc-admin")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS", "apple,google")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_APPLE_ISSUER", "https://appleid.apple.com")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_APPLE_AUDIENCE", "com.example.languagepartner")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_APPLE_HS256_SECRET", "test-apple-oidc-secret")
    db_path = tmp_path / "oidc-auth.sqlite3"
    client = TestClient(create_app(db_path))

    id_token = create_oidc_id_token(
        provider="apple",
        subject="apple-subject-123",
        email="AppleLearner@example.com",
        secret="test-apple-oidc-secret",
        issuer="https://appleid.apple.com",
        audience="com.example.languagepartner",
        nonce="nonce-123",
    )
    bad_nonce = client.post(
        "/v1/auth/oidc",
        json={"provider": "apple", "idToken": id_token, "nonce": "wrong-nonce"},
    )
    assert bad_nonce.status_code == 401

    login = client.post(
        "/v1/auth/oidc",
        json={
            "provider": "apple",
            "idToken": id_token,
            "nonce": "nonce-123",
            "learnerId": "oidc-alpha",
            "deviceLabel": "ios-apple",
            "deviceId": "apple-device",
        },
    )
    assert login.status_code == 200
    payload = login.json()
    assert payload["account"]["email"] == "applelearner@example.com"
    assert payload["account"]["learnerId"] == "oidc-alpha"
    assert payload["account"]["authProvider"] == "oidc"
    assert payload["account"]["identityProvider"] == "apple"
    assert payload["accessToken"].count(".") == 2
    bearer = {"Authorization": f"Bearer {payload['accessToken']}"}
    device_bearer = {**bearer, "X-Device-Id": "apple-device"}
    assert client.get("/v1/auth/me", headers=bearer).status_code == 401
    me = client.get("/v1/auth/me", headers=device_bearer).json()
    assert me["account"]["identityProvider"] == "apple"
    assert me["session"]["deviceBound"] is True

    with sqlite3.connect(db_path) as conn:
        identity = conn.execute("SELECT provider, subject, email_verified FROM account_identities").fetchone()
    assert identity == ("apple", "apple-subject-123", 1)

    second_login = client.post(
        "/v1/auth/oidc",
        json={"provider": "apple", "idToken": id_token, "nonce": "nonce-123", "deviceLabel": "ios-apple-second"},
    ).json()
    assert second_login["account"]["id"] == payload["account"]["id"]
    assert second_login["account"]["learnerId"] == "oidc-alpha"

    unverified_token = create_oidc_id_token(
        provider="apple",
        subject="apple-subject-unverified",
        email="unverified@example.com",
        secret="test-apple-oidc-secret",
        issuer="https://appleid.apple.com",
        audience="com.example.languagepartner",
        email_verified=False,
    )
    assert client.post("/v1/auth/oidc", json={"provider": "apple", "idToken": unverified_token}).status_code == 401
    assert client.post("/v1/auth/oidc", json={"provider": "github", "idToken": id_token}).status_code == 401

    auth_status = client.get("/v1/providers/status", headers=device_bearer).json()["operations"]["auth"]
    assert auth_status["oidcFederation"] is True
    assert auth_status["oidcAllowedProviders"] == ["apple", "google"]
    assert auth_status["oidcIdTokenVerification"] == "hs256_rs256_jwks"
    assert auth_status["oidcJwksVerification"] is False
    assert auth_status["oauthAuthorizationCodePkce"] is True
    assert auth_status["oauthPkceS256Only"] is True

    assert client.request("DELETE", "/v1/auth/account", headers=device_bearer, json={}).status_code == 401
    deleted = client.request(
        "DELETE",
        "/v1/auth/account",
        headers=device_bearer,
        json={"confirmation": "delete-my-account"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["accountDisabled"] is True
    assert client.get("/v1/auth/me", headers=device_bearer).status_code == 401

    audit_actions = [log["action"] for log in client.get("/v1/audit-log", headers={"X-Admin-Key": "test-oidc-admin"}).json()["auditLogs"]]
    assert "auth_oidc_succeeded" in audit_actions
    assert "auth_oidc_rejected" in audit_actions


def test_oidc_rs256_jwks_login_verifies_public_key_signature(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-oidc-rs256-account-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS", "google")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_GOOGLE_ISSUER", "https://accounts.google.com")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_GOOGLE_AUDIENCE", "com.example.languagepartner")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_GOOGLE_JWKS_JSON", json.dumps({"keys": [TEST_OIDC_RSA_PUBLIC_JWK]}))
    db_path = tmp_path / "oidc-rs256-auth.sqlite3"
    client = TestClient(create_app(db_path))

    id_token = create_oidc_rs256_id_token(
        provider="google",
        subject="google-subject-456",
        email="GoogleLearner@example.com",
        private_jwk=TEST_OIDC_RSA_JWK,
        issuer="https://accounts.google.com",
        audience="com.example.languagepartner",
        nonce="rs256-nonce",
        kid="test-rs256-key",
    )
    tampered = id_token.rsplit(".", 1)[0] + ".invalid-signature"
    assert client.post(
        "/v1/auth/oidc",
        json={"provider": "google", "idToken": tampered, "nonce": "rs256-nonce"},
    ).status_code == 401

    login = client.post(
        "/v1/auth/oidc",
        json={
            "provider": "google",
            "idToken": id_token,
            "nonce": "rs256-nonce",
            "learnerId": "oidc-rs256-alpha",
            "deviceLabel": "android-google",
        },
    )
    assert login.status_code == 200
    payload = login.json()
    assert payload["account"]["email"] == "googlelearner@example.com"
    assert payload["account"]["authProvider"] == "oidc"
    assert payload["account"]["identityProvider"] == "google"

    bearer = {"Authorization": f"Bearer {payload['accessToken']}"}
    assert client.get("/v1/auth/me", headers=bearer).json()["account"]["learnerId"] == "oidc-rs256-alpha"

    with sqlite3.connect(db_path) as conn:
        identity = conn.execute("SELECT provider, subject, email_verified FROM account_identities").fetchone()
    assert identity == ("google", "google-subject-456", 1)

    auth_status = client.get("/v1/providers/status", headers=bearer).json()["operations"]["auth"]
    assert auth_status["oidcFederation"] is True
    assert auth_status["oidcIdTokenVerification"] == "hs256_rs256_jwks"
    assert auth_status["oidcJwksVerification"] is True
    assert auth_status["oidcJwksConfiguredProviders"] == ["google"]
    assert auth_status["oauthAuthorizationCodePkce"] is True


def test_oauth_authorization_code_pkce_consumes_state_and_issues_account_session(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-oauth-pkce-account-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-oauth-admin")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS", "local-oidc")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_LOCAL_OIDC_ISSUER", "https://local-oidc.example")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_LOCAL_OIDC_AUDIENCE", "com.example.languagepartner")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_LOCAL_OIDC_HS256_SECRET", "test-local-oauth-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_LOCAL_OIDC_AUTHORIZATION_ENDPOINT", "https://local-oidc.example/oauth/authorize")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_LOCAL_OIDC_CLIENT_ID", "com.example.languagepartner")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_LOCAL_OIDC_REDIRECT_URIS", "http://localhost:8000/auth/callback")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_ALLOW_LOCAL_SIGNED_CODE", "true")
    db_path = tmp_path / "oauth-pkce.sqlite3"
    client = TestClient(create_app(db_path))
    redirect_uri = "http://localhost:8000/auth/callback"
    verifier = "verifier-" + ("a" * 60)
    bad_verifier = "verifier-" + ("b" * 60)

    rejected_redirect = client.post(
        "/v1/auth/oauth/pkce/start",
        json={
            "provider": "local-oidc",
            "redirectUri": "https://evil.example/callback",
            "codeChallenge": pkce_s256_challenge(verifier),
        },
    )
    assert rejected_redirect.status_code == 400

    start = client.post(
        "/v1/auth/oauth/pkce/start",
        json={
            "provider": "local-oidc",
            "redirectUri": redirect_uri,
            "codeChallenge": pkce_s256_challenge(verifier),
            "scope": "openid email profile",
            "learnerId": "oauth-pkce-alpha",
            "deviceLabel": "oauth-start-device",
        },
    )
    assert start.status_code == 200
    start_payload = start.json()
    assert start_payload["codeChallengeMethod"] == "S256"
    assert "code_challenge_method=S256" in start_payload["authorizationUrl"]
    assert "client_id=com.example.languagepartner" in start_payload["authorizationUrl"]

    bad_code = create_oauth_authorization_code(
        provider="local-oidc",
        subject="oauth-subject-123",
        email="OAuthLearner@example.com",
        secret="test-local-oauth-secret",
        issuer="https://local-oidc.example",
        audience="com.example.languagepartner",
        nonce=start_payload["nonce"],
        state=start_payload["state"],
    )
    bad_callback = client.post(
        "/v1/auth/oauth/pkce/callback",
        json={
            "provider": "local-oidc",
            "state": start_payload["state"],
            "code": bad_code,
            "codeVerifier": bad_verifier,
            "redirectUri": redirect_uri,
        },
    )
    assert bad_callback.status_code == 401
    assert client.post(
        "/v1/auth/oauth/pkce/callback",
        json={
            "provider": "local-oidc",
            "state": start_payload["state"],
            "code": bad_code,
            "codeVerifier": verifier,
            "redirectUri": redirect_uri,
        },
    ).status_code == 401

    start2 = client.post(
        "/v1/auth/oauth/pkce/start",
        json={
            "provider": "local-oidc",
            "redirectUri": redirect_uri,
            "codeChallenge": pkce_s256_challenge(verifier),
            "learnerId": "oauth-pkce-alpha",
            "deviceLabel": "oauth-start-device",
        },
    ).json()
    code = create_oauth_authorization_code(
        provider="local-oidc",
        subject="oauth-subject-123",
        email="OAuthLearner@example.com",
        secret="test-local-oauth-secret",
        issuer="https://local-oidc.example",
        audience="com.example.languagepartner",
        nonce=start2["nonce"],
        state=start2["state"],
    )
    callback = client.post(
        "/v1/auth/oauth/pkce/callback",
        json={
            "provider": "local-oidc",
            "state": start2["state"],
            "code": code,
            "codeVerifier": verifier,
            "redirectUri": redirect_uri,
            "deviceLabel": "oauth-callback-device",
        },
    )
    assert callback.status_code == 200
    payload = callback.json()
    assert payload["oauth"]["codeExchangeMode"] == "local_signed_code"
    assert payload["oauth"]["stateConsumed"] is True
    assert payload["account"]["email"] == "oauthlearner@example.com"
    assert payload["account"]["learnerId"] == "oauth-pkce-alpha"
    assert payload["account"]["authProvider"] == "oidc"
    assert payload["account"]["identityProvider"] == "local-oidc"
    assert payload["accessToken"].count(".") == 2
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {payload['accessToken']}"}).json()
    assert me["account"]["learnerId"] == "oauth-pkce-alpha"
    assert client.post(
        "/v1/auth/oauth/pkce/callback",
        json={
            "provider": "local-oidc",
            "state": start2["state"],
            "code": code,
            "codeVerifier": verifier,
            "redirectUri": redirect_uri,
        },
    ).status_code == 401

    with sqlite3.connect(db_path) as conn:
        consumed_count = conn.execute("SELECT COUNT(*) FROM oauth_pkce_requests WHERE consumed_at IS NOT NULL").fetchone()[0]
        identity = conn.execute("SELECT provider, subject, email_verified FROM account_identities").fetchone()
    assert consumed_count == 2
    assert identity == ("local-oidc", "oauth-subject-123", 1)

    auth_status = client.get("/v1/providers/status", headers={"Authorization": f"Bearer {payload['accessToken']}"}).json()["operations"]["auth"]
    assert auth_status["oauth"] is True
    assert auth_status["oauthAuthorizationCodePkce"] is True
    assert auth_status["oauthPkceS256Only"] is True
    assert auth_status["oauthPkceStateStoredHashed"] is True
    assert auth_status["oauthPkceOneTimeState"] is True
    assert auth_status["oauthPkceConfiguredProviders"] == ["local-oidc"]

    audit_actions = [log["action"] for log in client.get("/v1/audit-log", headers={"X-Admin-Key": "test-oauth-admin"}).json()["auditLogs"]]
    assert "auth_oauth_pkce_started" in audit_actions
    assert "auth_oauth_pkce_rejected" in audit_actions
    assert "auth_oauth_pkce_succeeded" in audit_actions


def test_enterprise_sso_discovery_and_pkce_enforces_connection_domain(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-enterprise-sso-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-sso-admin")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_ALLOWED_PROVIDERS", "local-oidc")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_LOCAL_OIDC_ISSUER", "https://local-oidc.example")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_LOCAL_OIDC_AUDIENCE", "com.example.languagepartner")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OIDC_LOCAL_OIDC_HS256_SECRET", "test-enterprise-sso-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_LOCAL_OIDC_AUTHORIZATION_ENDPOINT", "https://local-oidc.example/oauth/authorize")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_LOCAL_OIDC_CLIENT_ID", "com.example.languagepartner")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_LOCAL_OIDC_REDIRECT_URIS", "http://localhost:8000/auth/sso/callback")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_OAUTH_ALLOW_LOCAL_SIGNED_CODE", "true")
    db_path = tmp_path / "enterprise-sso.sqlite3"
    client = TestClient(create_app(db_path))
    redirect_uri = "http://localhost:8000/auth/sso/callback"
    verifier = "sso-verifier-" + ("a" * 60)

    viewer_headers = {"X-Admin-Key": "test-sso-admin", "X-Admin-Role": "viewer", "X-Admin-User": "sso-viewer"}
    editor_headers = {"X-Admin-Key": "test-sso-admin", "X-Admin-Role": "editor", "X-Admin-User": "sso-admin"}
    assert client.get("/v1/admin/auth/sso-connections", headers=viewer_headers).json()["count"] == 0
    assert client.put(
        "/v1/admin/auth/sso-connections/acme-sso",
        headers=viewer_headers,
        json={
            "provider": "local-oidc",
            "organizationName": "Acme Language Ops",
            "domains": ["acme.example"],
            "redirectUris": [redirect_uri],
            "requiredEmailDomain": "acme.example",
        },
    ).status_code == 403

    upserted = client.put(
        "/v1/admin/auth/sso-connections/acme-sso",
        headers=editor_headers,
        json={
            "provider": "local-oidc",
            "organizationName": "Acme Language Ops",
            "domains": ["Acme.Example"],
            "redirectUris": [redirect_uri],
            "requiredEmailDomain": "acme.example",
        },
    ).json()
    assert upserted["ok"] is True
    assert upserted["connection"]["id"] == "acme-sso"
    assert upserted["connection"]["domains"] == ["acme.example"]

    unmatched = client.get("/v1/auth/sso/discovery", params={"email": "person@other.example"}).json()
    assert unmatched["matched"] is False
    discovery = client.get("/v1/auth/sso/discovery", params={"email": "Person@Acme.Example"}).json()
    assert discovery["matched"] is True
    assert discovery["emailDomain"] == "acme.example"
    assert discovery["connection"]["id"] == "acme-sso"

    rejected_redirect = client.post(
        "/v1/auth/sso/pkce/start",
        json={
            "email": "person@acme.example",
            "redirectUri": "https://evil.example/callback",
            "codeChallenge": pkce_s256_challenge(verifier),
        },
    )
    assert rejected_redirect.status_code == 400
    assert client.post(
        "/v1/auth/sso/pkce/start",
        json={
            "email": "person@other.example",
            "redirectUri": redirect_uri,
            "codeChallenge": pkce_s256_challenge(verifier),
        },
    ).status_code == 404

    bad_domain_start = client.post(
        "/v1/auth/sso/pkce/start",
        json={
            "email": "person@acme.example",
            "redirectUri": redirect_uri,
            "codeChallenge": pkce_s256_challenge(verifier),
            "learnerId": "enterprise-sso-alpha",
            "deviceLabel": "sso-start-device",
        },
    ).json()
    bad_domain_code = create_oauth_authorization_code(
        provider="local-oidc",
        subject="sso-subject-bad-domain",
        email="person@evil.example",
        secret="test-enterprise-sso-secret",
        issuer="https://local-oidc.example",
        audience="com.example.languagepartner",
        nonce=bad_domain_start["nonce"],
        state=bad_domain_start["state"],
    )
    assert client.post(
        "/v1/auth/sso/pkce/callback",
        json={
            "connectionId": "acme-sso",
            "state": bad_domain_start["state"],
            "code": bad_domain_code,
            "codeVerifier": verifier,
            "redirectUri": redirect_uri,
        },
    ).status_code == 401

    start = client.post(
        "/v1/auth/sso/pkce/start",
        json={
            "email": "person@acme.example",
            "redirectUri": redirect_uri,
            "codeChallenge": pkce_s256_challenge(verifier),
            "scope": "openid email profile",
            "learnerId": "enterprise-sso-alpha",
            "deviceLabel": "sso-start-device",
        },
    ).json()
    assert start["connectionId"] == "acme-sso"
    assert start["connection"]["organizationName"] == "Acme Language Ops"
    assert "code_challenge_method=S256" in start["authorizationUrl"]

    code = create_oauth_authorization_code(
        provider="local-oidc",
        subject="sso-subject-123",
        email="Person@Acme.Example",
        secret="test-enterprise-sso-secret",
        issuer="https://local-oidc.example",
        audience="com.example.languagepartner",
        nonce=start["nonce"],
        state=start["state"],
    )
    callback = client.post(
        "/v1/auth/sso/pkce/callback",
        json={
            "connectionId": "acme-sso",
            "state": start["state"],
            "code": code,
            "codeVerifier": verifier,
            "redirectUri": redirect_uri,
            "deviceLabel": "sso-callback-device",
        },
    )
    assert callback.status_code == 200
    payload = callback.json()
    assert payload["account"]["email"] == "person@acme.example"
    assert payload["account"]["learnerId"] == "enterprise-sso-alpha"
    assert payload["account"]["identityProvider"] == "sso:acme-sso"
    assert payload["oauth"]["codeExchangeMode"] == "local_signed_code"
    assert payload["sso"]["connectionId"] == "acme-sso"
    assert payload["sso"]["emailDomain"] == "acme.example"
    assert client.get("/v1/auth/me", headers={"Authorization": f"Bearer {payload['accessToken']}"}).json()["account"]["identityProvider"] == "sso:acme-sso"
    assert client.post(
        "/v1/auth/sso/pkce/callback",
        json={
            "connectionId": "acme-sso",
            "state": start["state"],
            "code": code,
            "codeVerifier": verifier,
            "redirectUri": redirect_uri,
        },
    ).status_code == 401

    with sqlite3.connect(db_path) as conn:
        pkce_connection_ids = {
            row[0] for row in conn.execute("SELECT enterprise_sso_connection_id FROM oauth_pkce_requests").fetchall()
        }
        identity = conn.execute("SELECT provider, subject, email_verified FROM account_identities").fetchone()
    assert pkce_connection_ids == {"acme-sso"}
    assert identity == ("sso:acme-sso", "sso-subject-123", 1)

    auth_status = client.get("/v1/providers/status", headers={"Authorization": f"Bearer {payload['accessToken']}"}).json()["operations"]["auth"]
    assert auth_status["enterpriseSso"] is True
    assert auth_status["enterpriseSsoDomainDiscovery"] is True
    assert auth_status["enterpriseSsoAuthorizationCodePkce"] is True
    assert auth_status["enterpriseSsoConnectionCount"] == 1
    assert auth_status["enterpriseSsoConfiguredProviders"] == ["local-oidc"]

    audit_actions = [log["action"] for log in client.get("/v1/audit-log", headers={"X-Admin-Key": "test-sso-admin"}).json()["auditLogs"]]
    assert "auth_sso_connection_upserted" in audit_actions
    assert "auth_sso_pkce_started" in audit_actions
    assert "auth_sso_pkce_rejected" in audit_actions
    assert "auth_sso_pkce_succeeded" in audit_actions


def test_account_auth_device_binding_throttle_password_change_and_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-account-hardening-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MAX_FAILURES", "3")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_FAILURE_WINDOW_SECONDS", "900")
    db_path = tmp_path / "account-hardening.sqlite3"
    client = TestClient(create_app(db_path))

    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "secure@example.com",
            "password": "initial-password",
            "learnerId": "secure-alpha",
            "deviceLabel": "ios-device",
            "deviceId": "device-123",
        },
    ).json()
    bearer = {"Authorization": f"Bearer {registered['accessToken']}"}
    device_bearer = {**bearer, "X-Device-Id": "device-123"}

    assert client.get("/v1/auth/me", headers=bearer).status_code == 401
    assert client.get("/v1/auth/me", headers={**bearer, "X-Device-Id": "wrong-device"}).status_code == 401
    me = client.get("/v1/auth/me", headers=device_bearer).json()
    assert me["session"]["deviceBound"] is True

    changed = client.post(
        "/v1/auth/change-password",
        headers=device_bearer,
        json={
            "currentPassword": "initial-password",
            "newPassword": "rotated-password",
            "deviceLabel": "ios-device-rotated",
            "deviceId": "device-123",
        },
    )
    assert changed.status_code == 200
    changed_payload = changed.json()
    assert changed_payload["accessToken"] != registered["accessToken"]
    assert client.get("/v1/auth/me", headers=device_bearer).status_code == 401
    rotated_bearer = {"Authorization": f"Bearer {changed_payload['accessToken']}", "X-Device-Id": "device-123"}
    assert client.get("/v1/auth/me", headers=rotated_bearer).json()["session"]["deviceLabel"] == "ios-device-rotated"

    assert client.post("/v1/auth/login", json={"email": "secure@example.com", "password": "initial-password"}).status_code == 401
    assert client.post("/v1/auth/login", json={"email": "secure@example.com", "password": "rotated-password"}).status_code == 200

    conv = client.post(
        "/v1/conversations",
        headers=rotated_bearer,
        json={"personaId": "yui", "practiceRoomId": "tired_today"},
    ).json()
    client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        headers=rotated_bearer,
        json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
    )
    assert client.request(
        "DELETE",
        "/v1/auth/account",
        headers=rotated_bearer,
        json={"password": "wrong-password"},
    ).status_code == 401
    deleted = client.request(
        "DELETE",
        "/v1/auth/account",
        headers=rotated_bearer,
        json={"password": "rotated-password"},
    )
    assert deleted.status_code == 200
    deleted_payload = deleted.json()
    assert deleted_payload["accountDisabled"] is True
    assert deleted_payload["privacyDeletion"]["deletedCounts"]["conversations"] == 1
    assert client.get("/v1/auth/me", headers=rotated_bearer).status_code == 401
    assert client.post("/v1/auth/login", json={"email": "secure@example.com", "password": "rotated-password"}).status_code == 401
    assert client.post("/v1/auth/login", json={"email": "secure@example.com", "password": "bad-1"}).status_code == 401
    assert client.post("/v1/auth/login", json={"email": "secure@example.com", "password": "bad-2"}).status_code == 401
    assert client.post("/v1/auth/login", json={"email": "secure@example.com", "password": "bad-3"}).status_code == 429


def test_account_device_trust_lifecycle_lists_trusts_and_revokes_bound_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-device-trust-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-device-trust-admin")
    client = TestClient(create_app(tmp_path / "device-trust.sqlite3"))

    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "device-trust@example.com",
            "password": "device-password",
            "learnerId": "device-trust-alpha",
            "deviceLabel": "iphone-15",
            "deviceId": "stable-device-a",
        },
    )
    assert registered.status_code == 200
    payload = registered.json()
    assert payload["deviceTrust"]["status"] == "untrusted"
    device_headers = {"Authorization": f"Bearer {payload['accessToken']}", "X-Device-Id": "stable-device-a"}
    me = client.get("/v1/auth/me", headers=device_headers).json()
    assert me["session"]["deviceTrust"]["status"] == "untrusted"
    assert me["session"]["deviceTrust"]["trusted"] is False

    devices_before = client.get("/v1/auth/devices", headers=device_headers).json()
    assert devices_before["activeDeviceCount"] == 1
    current_device = devices_before["devices"][0]
    assert current_device["trustStatus"] == "untrusted"
    assert current_device["isCurrent"] is True

    trusted = client.post(
        "/v1/auth/devices/trust",
        headers=device_headers,
        json={
            "confirmation": "trust-this-device",
            "deviceLabel": "iphone-15-pro",
            "platform": "ios",
            "attestationProvider": "self_attested",
            "attestationSubject": "local-device-key-material",
            "evidence": {"client": "ios-app"},
        },
    )
    assert trusted.status_code == 200
    trusted_device = trusted.json()["device"]
    assert trusted_device["trustStatus"] == "trusted"
    assert trusted_device["attestationVerified"] is False
    assert trusted_device["verificationMode"] == "account_confirmed_not_platform_verified"

    me_after_trust = client.get("/v1/auth/me", headers=device_headers).json()
    assert me_after_trust["session"]["deviceTrust"]["status"] == "trusted"
    assert me_after_trust["session"]["deviceTrust"]["trusted"] is True
    assert me_after_trust["session"]["deviceTrust"]["verificationMode"] == "account_confirmed_not_platform_verified"

    status = client.get("/v1/providers/status", headers=device_headers).json()["operations"]["auth"]
    assert status["deviceRegistry"] is True
    assert status["deviceTrustLifecycle"] is True
    assert status["trustedDeviceEnrollment"] is True
    assert status["deviceRevokeRevokesSessions"] is True
    assert status["platformAttestationVerification"] == "not_configured"

    revoked = client.request("DELETE", f"/v1/auth/devices/{trusted_device['id']}", headers=device_headers)
    assert revoked.status_code == 200
    assert revoked.json()["revokedSessionCount"] >= 1
    assert client.get("/v1/auth/me", headers=device_headers).status_code == 401
    rejected_reuse = client.post(
        "/v1/auth/login",
        json={
            "email": "device-trust@example.com",
            "password": "device-password",
            "deviceLabel": "iphone-15-reused",
            "deviceId": "stable-device-a",
        },
    )
    assert rejected_reuse.status_code == 403
    new_device = client.post(
        "/v1/auth/login",
        json={
            "email": "device-trust@example.com",
            "password": "device-password",
            "deviceLabel": "ipad",
            "deviceId": "stable-device-b",
        },
    )
    assert new_device.status_code == 200
    new_headers = {"Authorization": f"Bearer {new_device.json()['accessToken']}", "X-Device-Id": "stable-device-b"}
    devices_after = client.get("/v1/auth/devices?includeRevoked=true", headers=new_headers).json()["devices"]
    assert any(item["id"] == trusted_device["id"] and item["trustStatus"] == "revoked" for item in devices_after)

    audit_actions = [
        log["action"]
        for log in client.get("/v1/audit-log", headers={"X-Admin-Key": "test-device-trust-admin"}).json()["auditLogs"]
    ]
    assert "auth_device_trusted" in audit_actions
    assert "auth_device_revoked" in audit_actions


def test_signed_device_attestation_challenge_trust_verifies_signature_and_blocks_replay(tmp_path, monkeypatch):
    secret = "test-device-attestation-secret"
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET", secret)
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-device-attestation-admin")
    client = make_client(tmp_path)
    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "signed-device@example.com",
            "password": "device-password",
            "learnerId": "signed-device-alpha",
            "deviceLabel": "ios-real",
            "deviceId": "signed-device-a",
        },
    )
    assert registered.status_code == 200
    headers = {"Authorization": f"Bearer {registered.json()['accessToken']}", "X-Device-Id": "signed-device-a"}

    status = client.get("/v1/providers/status", headers=headers).json()["operations"]["auth"]
    assert status["platformAttestationVerification"] == "signed_challenge_hmac"
    assert status["deviceAttestationChallenge"] is True

    challenge = client.post(
        "/v1/auth/devices/attestation/challenge",
        headers=headers,
        json={"attestationProvider": "signed_challenge", "attestationSubject": "device-public-key-1"},
    )
    assert challenge.status_code == 200
    challenge_payload = challenge.json()
    bad_signature = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "ios",
            "attestationProvider": "signed_challenge",
            "attestationSubject": "device-public-key-1",
            "evidence": {
                "challengeId": challenge_payload["challengeId"],
                "challenge": challenge_payload["challenge"],
                "signature": "0" * 64,
            },
        },
    )
    assert bad_signature.status_code == 401
    replay_after_bad_signature = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "ios",
            "attestationProvider": "signed_challenge",
            "attestationSubject": "device-public-key-1",
            "evidence": {
                "challengeId": challenge_payload["challengeId"],
                "challenge": challenge_payload["challenge"],
                "signature": hmac.new(secret.encode("utf-8"), challenge_payload["message"].encode("utf-8"), hashlib.sha256).hexdigest(),
            },
        },
    )
    assert replay_after_bad_signature.status_code == 401

    challenge = client.post(
        "/v1/auth/devices/attestation/challenge",
        headers=headers,
        json={"attestationProvider": "signed_challenge", "attestationSubject": "device-public-key-1"},
    ).json()
    signature = hmac.new(secret.encode("utf-8"), challenge["message"].encode("utf-8"), hashlib.sha256).hexdigest()
    trusted = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "deviceLabel": "ios-real",
            "platform": "ios",
            "attestationProvider": "signed_challenge",
            "attestationSubject": "device-public-key-1",
            "evidence": {
                "challengeId": challenge["challengeId"],
                "challenge": challenge["challenge"],
                "signature": signature,
            },
        },
    )
    assert trusted.status_code == 200
    trusted_device = trusted.json()["device"]
    assert trusted_device["trustStatus"] == "trusted"
    assert trusted_device["attestationProvider"] == "signed_challenge"
    assert trusted_device["attestationVerified"] is True
    assert trusted_device["verificationMode"] == "signed_challenge_hmac"

    me_after_trust = client.get("/v1/auth/me", headers=headers).json()
    assert me_after_trust["session"]["deviceTrust"]["attestationVerified"] is True
    assert me_after_trust["session"]["deviceTrust"]["verificationMode"] == "signed_challenge_hmac"

    replay_after_success = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "ios",
            "attestationProvider": "signed_challenge",
            "attestationSubject": "device-public-key-1",
            "evidence": {
                "challengeId": challenge["challengeId"],
                "challenge": challenge["challenge"],
                "signature": signature,
            },
        },
    )
    assert replay_after_success.status_code == 401

    audit_actions = [
        log["action"]
        for log in client.get("/v1/audit-log", headers={"X-Admin-Key": "test-device-attestation-admin"}).json()["auditLogs"]
    ]
    assert "auth_device_attestation_challenge_issued" in audit_actions
    assert "auth_device_attestation_failed" in audit_actions
    assert "auth_device_trusted" in audit_actions


def test_public_key_device_attestation_challenge_verifies_rs256_signature_without_shared_secret(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET", raising=False)
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-public-key-device-admin")
    client = make_client(tmp_path)
    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "public-key-device@example.com",
            "password": "device-password",
            "learnerId": "public-key-device-alpha",
            "deviceLabel": "android-real",
            "deviceId": "public-key-device-a",
        },
    )
    assert registered.status_code == 200
    headers = {"Authorization": f"Bearer {registered.json()['accessToken']}", "X-Device-Id": "public-key-device-a"}
    public_jwk_subject = json.dumps(TEST_OIDC_RSA_PUBLIC_JWK, separators=(",", ":"), sort_keys=True)

    status = client.get("/v1/providers/status", headers=headers).json()["operations"]["auth"]
    assert status["platformAttestationVerification"] == "not_configured"
    assert status["publicKeyDeviceAttestationChallenge"] is True
    assert status["publicKeyDeviceAttestationVerification"] == "public_key_challenge_rs256"
    assert "public_key_challenge" in status["deviceAttestationProviders"]

    missing_subject = client.post(
        "/v1/auth/devices/attestation/challenge",
        headers=headers,
        json={"attestationProvider": "public_key_challenge"},
    )
    assert missing_subject.status_code == 400

    challenge_payload = client.post(
        "/v1/auth/devices/attestation/challenge",
        headers=headers,
        json={"attestationProvider": "public_key_challenge", "attestationSubject": public_jwk_subject},
    ).json()
    assert challenge_payload["signatureAlgorithm"] == "rs256"

    bad_signature = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "android",
            "attestationProvider": "public_key_challenge",
            "attestationSubject": public_jwk_subject,
            "evidence": {
                "algorithm": "rs256",
                "challengeId": challenge_payload["challengeId"],
                "challenge": challenge_payload["challenge"],
                "signature": "invalid-signature",
            },
        },
    )
    assert bad_signature.status_code == 401
    replay_after_bad_signature = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "android",
            "attestationProvider": "public_key_challenge",
            "attestationSubject": public_jwk_subject,
            "evidence": {
                "algorithm": "rs256",
                "challengeId": challenge_payload["challengeId"],
                "challenge": challenge_payload["challenge"],
                "signature": _sign_rs256_with_jwk(challenge_payload["message"], TEST_OIDC_RSA_JWK),
            },
        },
    )
    assert replay_after_bad_signature.status_code == 401

    challenge_payload = client.post(
        "/v1/auth/devices/attestation/challenge",
        headers=headers,
        json={"attestationProvider": "public_key_challenge", "attestationSubject": public_jwk_subject},
    ).json()
    trusted = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "deviceLabel": "android-real",
            "platform": "android",
            "attestationProvider": "public_key_challenge",
            "attestationSubject": public_jwk_subject,
            "evidence": {
                "algorithm": "rs256",
                "challengeId": challenge_payload["challengeId"],
                "challenge": challenge_payload["challenge"],
                "signature": _sign_rs256_with_jwk(challenge_payload["message"], TEST_OIDC_RSA_JWK),
            },
        },
    )
    assert trusted.status_code == 200
    trusted_device = trusted.json()["device"]
    assert trusted_device["attestationProvider"] == "public_key_challenge"
    assert trusted_device["attestationVerified"] is True
    assert trusted_device["verificationMode"] == "public_key_challenge_rs256"

    me_after_trust = client.get("/v1/auth/me", headers=headers).json()
    assert me_after_trust["session"]["deviceTrust"]["verificationMode"] == "public_key_challenge_rs256"

    audit_actions = [
        log["action"]
        for log in client.get("/v1/audit-log", headers={"X-Admin-Key": "test-public-key-device-admin"}).json()["auditLogs"]
    ]
    assert "auth_device_attestation_challenge_issued" in audit_actions
    assert "auth_device_attestation_failed" in audit_actions
    assert "auth_device_trusted" in audit_actions


def test_webauthn_device_attestation_challenge_verifies_es256_assertion(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_LANGUAGE_PARTNER_DEVICE_ATTESTATION_SECRET", raising=False)
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-webauthn-device-admin")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_WEBAUTHN_RP_ID", "localhost")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_WEBAUTHN_ALLOWED_ORIGINS", "http://localhost:8000")
    client = make_client(tmp_path)
    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "webauthn-device@example.com",
            "password": "device-password",
            "learnerId": "webauthn-device-alpha",
            "deviceLabel": "ios-passkey",
            "deviceId": "webauthn-device-a",
        },
    )
    assert registered.status_code == 200
    headers = {"Authorization": f"Bearer {registered.json()['accessToken']}", "X-Device-Id": "webauthn-device-a"}
    public_jwk_subject = json.dumps(TEST_WEBAUTHN_PUBLIC_JWK, separators=(",", ":"), sort_keys=True)

    status = client.get("/v1/providers/status", headers=headers).json()["operations"]["auth"]
    assert status["webauthnDeviceAttestationChallenge"] is True
    assert status["webauthnDeviceAttestationVerification"] == "webauthn_assertion_es256"
    assert status["webauthnRpId"] == "localhost"
    assert status["webauthnAllowedOrigins"] == ["http://localhost:8000"]
    assert status["webauthnUserPresenceRequired"] is True
    assert "webauthn_public_key" in status["deviceAttestationProviders"]

    challenge_payload = client.post(
        "/v1/auth/devices/attestation/challenge",
        headers=headers,
        json={"attestationProvider": "webauthn_public_key", "attestationSubject": public_jwk_subject},
    ).json()
    assert challenge_payload["signatureAlgorithm"] == "webauthn-es256"

    missing_client_data = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "ios",
            "attestationProvider": "webauthn_public_key",
            "attestationSubject": public_jwk_subject,
            "evidence": {
                "algorithm": "webauthn-es256",
                "challengeId": challenge_payload["challengeId"],
                "challenge": challenge_payload["challenge"],
                "signature": "invalid",
            },
        },
    )
    assert missing_client_data.status_code == 400

    bad_origin_evidence = webauthn_assertion(challenge_payload["challenge"], origin="https://evil.example")
    bad_origin_evidence.update({"challengeId": challenge_payload["challengeId"], "challenge": challenge_payload["challenge"]})
    bad_origin = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "ios",
            "attestationProvider": "webauthn_public_key",
            "attestationSubject": public_jwk_subject,
            "evidence": bad_origin_evidence,
        },
    )
    assert bad_origin.status_code == 401
    replay_after_bad_origin = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "ios",
            "attestationProvider": "webauthn_public_key",
            "attestationSubject": public_jwk_subject,
            "evidence": bad_origin_evidence,
        },
    )
    assert replay_after_bad_origin.status_code == 401

    challenge_payload = client.post(
        "/v1/auth/devices/attestation/challenge",
        headers=headers,
        json={"attestationProvider": "webauthn_public_key", "attestationSubject": public_jwk_subject},
    ).json()
    assertion = webauthn_assertion(challenge_payload["challenge"])
    assertion.update({"challengeId": challenge_payload["challengeId"], "challenge": challenge_payload["challenge"]})
    trusted = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "deviceLabel": "ios-passkey",
            "platform": "ios",
            "attestationProvider": "webauthn_public_key",
            "attestationSubject": public_jwk_subject,
            "evidence": assertion,
        },
    )
    assert trusted.status_code == 200
    trusted_device = trusted.json()["device"]
    assert trusted_device["attestationProvider"] == "webauthn_public_key"
    assert trusted_device["attestationVerified"] is True
    assert trusted_device["verificationMode"] == "webauthn_assertion_es256"

    me_after_trust = client.get("/v1/auth/me", headers=headers).json()
    assert me_after_trust["session"]["deviceTrust"]["verificationMode"] == "webauthn_assertion_es256"
    assert me_after_trust["session"]["deviceTrust"]["attestationVerified"] is True
    replay_after_success = client.post(
        "/v1/auth/devices/trust",
        headers=headers,
        json={
            "confirmation": "trust-this-device",
            "platform": "ios",
            "attestationProvider": "webauthn_public_key",
            "attestationSubject": public_jwk_subject,
            "evidence": assertion,
        },
    )
    assert replay_after_success.status_code == 401

    audit_actions = [
        log["action"]
        for log in client.get("/v1/audit-log", headers={"X-Admin-Key": "test-webauthn-device-admin"}).json()["auditLogs"]
    ]
    assert "auth_device_attestation_challenge_issued" in audit_actions
    assert "auth_device_attestation_failed" in audit_actions
    assert "auth_device_trusted" in audit_actions


def test_account_login_password_spray_risk_control_blocks_client_and_audits(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_RISK_MAX_DISTINCT_EMAILS", "2")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_RISK_WINDOW_SECONDS", "900")
    client = make_client(tmp_path)
    registered = client.post(
        "/v1/auth/register",
        json={"email": "spray-victim@example.com", "password": "correct-password", "learnerId": "spray-victim"},
    )
    assert registered.status_code == 200

    assert client.post("/v1/auth/login", json={"email": "spray-a@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/v1/auth/login", json={"email": "spray-b@example.com", "password": "wrong"}).status_code == 401
    blocked = client.post("/v1/auth/login", json={"email": "spray-victim@example.com", "password": "correct-password"})
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Login temporarily blocked by risk controls"

    status = client.get("/v1/providers/status").json()["operations"]["auth"]
    assert status["passwordSprayRiskControl"] is True
    assert status["riskBasedAbuseControls"] is True

    audit_logs = client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
    risk_log = next(log for log in audit_logs if log["action"] == "auth_login_risk_blocked")
    assert risk_log["targetType"] == "client_hash"
    assert risk_log["payload"]["control"] == "password_spray_client_guard"
    assert risk_log["payload"]["distinctFailedEmailHashes"] == 2


def test_account_session_inventory_remote_revoke_and_logout_all(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-session-management-jwt-secret")
    client = TestClient(create_app(tmp_path / "account-session-management.sqlite3"))

    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "sessions@example.com",
            "password": "session-password",
            "learnerId": "session-alpha",
            "deviceLabel": "phone-a",
        },
    ).json()
    bearer_a = {"Authorization": f"Bearer {registered['accessToken']}"}
    login_b = client.post(
        "/v1/auth/login",
        json={"email": "sessions@example.com", "password": "session-password", "deviceLabel": "tablet-b"},
    ).json()
    bearer_b = {"Authorization": f"Bearer {login_b['accessToken']}"}

    listed = client.get("/v1/auth/sessions", headers=bearer_a).json()
    assert listed["activeSessionCount"] == 2
    assert listed["currentSessionId"]
    assert sum(1 for session in listed["sessions"] if session["isCurrent"]) == 1
    tablet_session = next(session for session in listed["sessions"] if session["deviceLabel"] == "tablet-b")

    revoked = client.request("DELETE", f"/v1/auth/sessions/{tablet_session['id']}", headers=bearer_a)
    assert revoked.status_code == 200
    assert revoked.json()["selfRevoked"] is False
    assert client.get("/v1/auth/me", headers=bearer_b).status_code == 401
    after_revoke = client.get("/v1/auth/sessions?includeRevoked=true", headers=bearer_a).json()
    assert after_revoke["activeSessionCount"] == 1
    assert any(session["id"] == tablet_session["id"] and session["revokedAt"] for session in after_revoke["sessions"])

    login_c = client.post(
        "/v1/auth/login",
        json={"email": "sessions@example.com", "password": "session-password", "deviceLabel": "laptop-c"},
    ).json()
    bearer_c = {"Authorization": f"Bearer {login_c['accessToken']}"}
    login_d = client.post(
        "/v1/auth/login",
        json={"email": "sessions@example.com", "password": "session-password", "deviceLabel": "browser-d"},
    ).json()
    bearer_d = {"Authorization": f"Bearer {login_d['accessToken']}"}

    kept = client.post("/v1/auth/logout-all?keepCurrent=true", headers=bearer_c).json()
    assert kept["currentSessionKept"] is True
    assert kept["revokedCount"] >= 2
    assert client.get("/v1/auth/me", headers=bearer_c).status_code == 200
    assert client.get("/v1/auth/me", headers=bearer_a).status_code == 401
    assert client.get("/v1/auth/me", headers=bearer_d).status_code == 401

    status = client.get("/v1/providers/status", headers=bearer_c).json()["operations"]["auth"]
    assert status["sessionInventory"] is True
    assert status["remoteSessionRevoke"] is True
    assert status["logoutAllSessions"] is True

    logged_out_all = client.post("/v1/auth/logout-all", headers=bearer_c).json()
    assert logged_out_all["currentSessionKept"] is False
    assert logged_out_all["revokedCount"] >= 1
    assert client.get("/v1/auth/me", headers=bearer_c).status_code == 401


def test_refresh_token_reuse_detection_revokes_account_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-refresh-reuse-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-refresh-reuse-admin")
    client = TestClient(create_app(tmp_path / "refresh-reuse.sqlite3"))
    admin_headers = {"X-Admin-Key": "test-refresh-reuse-admin"}

    registered = client.post(
        "/v1/auth/register",
        json={
            "email": "reuse@example.com",
            "password": "refresh-password",
            "learnerId": "reuse-alpha",
            "deviceLabel": "phone-a",
        },
    ).json()
    first_refresh = registered["refreshToken"]
    rotated = client.post(
        "/v1/auth/refresh",
        json={"refreshToken": first_refresh, "deviceLabel": "phone-a-rotated"},
    ).json()
    rotated_bearer = {"Authorization": f"Bearer {rotated['accessToken']}"}
    assert client.get("/v1/auth/me", headers=rotated_bearer).status_code == 200

    replay = client.post("/v1/auth/refresh", json={"refreshToken": first_refresh})
    assert replay.status_code == 401
    assert client.get("/v1/auth/me", headers=rotated_bearer).status_code == 401
    audit_logs = client.get("/v1/audit-log", headers=admin_headers).json()["auditLogs"]
    reuse_log = next(log for log in audit_logs if log["action"] == "auth_refresh_reuse_detected")
    assert reuse_log["payload"]["replayedSessionId"].startswith("sess_")
    assert reuse_log["payload"]["revokedCount"] >= 1

    fresh_login = client.post(
        "/v1/auth/login",
        json={"email": "reuse@example.com", "password": "refresh-password"},
    ).json()
    status = client.get("/v1/providers/status", headers={"Authorization": f"Bearer {fresh_login['accessToken']}"}).json()["operations"]["auth"]
    assert status["refreshReuseDetection"] is True


def test_registration_throttle_limits_account_creation_bursts(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_JWT_SECRET", "test-register-throttle-jwt-secret")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", "test-register-throttle-admin")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_REGISTER_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_REGISTER_WINDOW_SECONDS", "3600")
    client = TestClient(create_app(tmp_path / "register-throttle.sqlite3"))

    first = client.post(
        "/v1/auth/register",
        json={"email": "signup1@example.com", "password": "register-password", "learnerId": "signup-one"},
    )
    assert first.status_code == 200
    second = client.post(
        "/v1/auth/register",
        json={"email": "signup2@example.com", "password": "register-password", "learnerId": "signup-two"},
    )
    assert second.status_code == 200
    throttled = client.post(
        "/v1/auth/register",
        json={"email": "signup3@example.com", "password": "register-password", "learnerId": "signup-three"},
    )
    assert throttled.status_code == 429
    assert throttled.json()["detail"] == "Too many registration attempts"

    bearer = {"Authorization": f"Bearer {first.json()['accessToken']}"}
    status = client.get("/v1/providers/status", headers=bearer).json()["operations"]["auth"]
    assert status["registrationThrottle"] is True

    audit_logs = client.get("/v1/audit-log", headers={"X-Admin-Key": "test-register-throttle-admin"}).json()["auditLogs"]
    throttle_log = next(log for log in audit_logs if log["action"] == "auth_registration_throttled")
    assert throttle_log["payload"]["recentAttempts"] == 2
    assert throttle_log["payload"]["windowSeconds"] == 3600
    assert "signup3@example.com" not in str(throttle_log)


def test_admin_default_key_is_dev_only_and_privacy_audit_hashes_learner(tmp_path, monkeypatch):
    client = make_client(tmp_path)
    learner_headers = {"X-Learner-Id": "privacy-user", "X-User-Id": "privacy-user"}
    conv = client.post(
        "/v1/conversations",
        headers=learner_headers,
        json={"personaId": "yui", "practiceRoomId": "tired_today"},
    ).json()
    client.post(
        f"/v1/conversations/{conv['conversationId']}/turns",
        headers=learner_headers,
        json={"inputType": "text", "text": "오늘 너무 피곤했어", "requestTts": False},
    )
    deleted = client.delete("/v1/privacy/me", headers=learner_headers).json()
    assert deleted["deletedCounts"]["conversations"] == 1
    audit_logs = client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).json()["auditLogs"]
    serialized = str(audit_logs)
    assert "privacy-user" not in serialized
    assert "learner_hash_" in serialized

    monkeypatch.setenv("AI_LANGUAGE_PARTNER_AUTH_MODE", "production")
    monkeypatch.delenv("AI_LANGUAGE_PARTNER_ADMIN_KEY", raising=False)
    assert client.get("/v1/audit-log", headers={"X-Admin-Key": "local-dev-admin"}).status_code == 403


def test_provider_status_reflects_env_adapters_without_leaking_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_LLM_API_KEY", "test-llm-key")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_LLM_MODEL", "test-chat-model")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_TTS_PROVIDER", "openai")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_TTS_API_KEY", "test-tts-key")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_TTS_MODEL", "test-tts-model")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_STT_PROVIDER", "openai")
    monkeypatch.setenv("AI_LANGUAGE_PARTNER_STT_API_KEY", "test-stt-key")

    client = TestClient(create_app(tmp_path / "providers.sqlite3"))
    status = client.get("/v1/providers/status").json()

    assert status["mode"] == "hybrid_provider_adapters"
    assert status["providers"]["llm"]["active"] == "openai_compatible"
    assert status["providers"]["llm"]["model"] == "test-chat-model"
    assert status["providers"]["llm"]["structuredOutputSchemaVersion"] == STRUCTURED_TURN_SCHEMA_VERSION
    assert status["providers"]["tts"]["active"] == "openai_tts"
    assert status["providers"]["tts"]["model"] == "test-tts-model"
    assert status["providers"]["stt"]["active"] == "openai_stt"
    serialized = str(status)
    assert "test-llm-key" not in serialized
    assert "test-tts-key" not in serialized
    assert "test-stt-key" not in serialized


def test_openai_stt_accepts_data_url_audio_and_preserves_content_type(monkeypatch):
    captured = {}

    def fake_post_audio_transcription(url, api_key, model, audio_bytes, timeout, content_type="audio/wav"):
        captured["audioBytes"] = audio_bytes
        captured["contentType"] = content_type
        captured["model"] = model
        return "今日めっちゃ疲れた"

    monkeypatch.setattr("app.providers._post_audio_transcription", fake_post_audio_transcription)
    provider = OpenAISTTProvider(api_key="secret", base_url="https://stt.example/v1", model="whisper-test")
    audio_payload = base64.b64encode(b"fake-mp3-bytes").decode("ascii")
    result = provider.transcribe({"audioBase64": "data:audio/mpeg;base64," + audio_payload})

    assert result["provider"] == "openai_stt"
    assert result["text"] == "今日めっちゃ疲れた"
    assert captured["audioBytes"] == b"fake-mp3-bytes"
    assert captured["contentType"] == "audio/mpeg"
    assert captured["model"] == "whisper-test"


def test_audio_payload_decoder_handles_raw_base64_and_data_urls():
    raw = base64.b64encode(b"abc").decode("ascii")
    assert decode_audio_payload(raw) == (b"abc", "audio/wav")
    assert decode_audio_payload("data:audio/webm;base64," + raw) == (b"abc", "audio/webm")


def test_openai_stt_multipart_upload_uses_detected_media_type(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"text":"ok"}'

    def fake_urlopen(request, timeout):
        captured["data"] = request.data
        captured["contentTypeHeader"] = request.headers["Content-type"]
        captured["authorization"] = request.headers["Authorization"]
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.providers.urllib.request.urlopen", fake_urlopen)
    text = _post_audio_transcription(
        "https://stt.example/v1/audio/transcriptions",
        "secret",
        "whisper-test",
        b"mp3-bytes",
        timeout=11,
        content_type="audio/mpeg",
    )

    assert text == "ok"
    assert b'filename="audio.mp3"' in captured["data"]
    assert b"Content-Type: audio/mpeg" in captured["data"]
    assert b"mp3-bytes" in captured["data"]
    assert captured["contentTypeHeader"].startswith("multipart/form-data; boundary=")
    assert captured["authorization"] == "Bearer secret"
    assert captured["timeout"] == 11


def test_openai_stt_multipart_upload_maps_m4a_and_webm_extensions(monkeypatch):
    seen = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"text":"ok"}'

    def fake_urlopen(request, timeout):
        seen.append(request.data)
        return FakeResponse()

    monkeypatch.setattr("app.providers.urllib.request.urlopen", fake_urlopen)
    for content_type, filename in [("audio/mp4", b'filename="audio.m4a"'), ("audio/webm", b'filename="audio.webm"')]:
        _post_audio_transcription(
            "https://stt.example/v1/audio/transcriptions",
            "secret",
            "whisper-test",
            b"audio-bytes",
            timeout=11,
            content_type=content_type,
        )
        assert filename in seen[-1]
        assert f"Content-Type: {content_type}".encode("utf-8") in seen[-1]


def test_openai_compatible_llm_structured_json_updates_full_turn(monkeypatch):
    def fake_post_json(url, payload, api_key, timeout):
        assert payload["response_format"] == {"type": "json_object"}
        user_payload = yaml.safe_load(payload["messages"][1]["content"])
        assert user_payload["expectedOutputSchemaVersion"] == STRUCTURED_TURN_SCHEMA_VERSION
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"schemaVersion":"turn_payload_v1",'
                            '"assistantTextKo":"좋아, 이 표현으로 가자.",'
                            '"spokenTextJa":"今日は本当に疲れた",'
                            '"suggestedUserReplyJa":"今日は本当に疲れた",'
                            '"corrections":[{"category":"naturalness","original":"피곤","corrected":"疲れた","explanationKo":"자연스럽게 과거형"}],'
                            '"reviewCards":[{"front":"오늘 정말 피곤했어","back":"今日は本当に疲れた。","tags":["감정표현"]}]}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr("app.providers._post_json", fake_post_json)
    provider = OpenAICompatibleLLMProvider(api_key="secret", base_url="https://llm.example/v1", model="test-model")
    turn = provider.generate_turn(
        {"id": "yui", "displayName": "유이"},
        {"id": "tired_today", "primaryPhraseKo": "오늘 너무 피곤했어", "primaryPhraseJa": "今日めっちゃ疲れた"},
        "오늘 정말 피곤했어",
    )
    assert turn["assistantText"] == "좋아, 이 표현으로 가자."
    assert turn["spokenText"] == "今日は本当に疲れた。"
    assert turn["suggestedUserReply"] == "今日は本当に疲れた。"
    assert turn["reviewCards"][0]["back"] == "今日は本当に疲れた。"
    assert turn["corrections"][0]["category"] == "naturalness"
    assert turn["usage"]["llmProvider"] == "openai_compatible"


def test_openai_compatible_llm_can_request_strict_json_schema_response_format(monkeypatch):
    captured = {}

    def fake_post_json(url, payload, api_key, timeout):
        captured["responseFormat"] = payload["response_format"]
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"schemaVersion":"turn_payload_v1",'
                            '"assistantTextKo":"스키마 모드 응답이야.",'
                            '"spokenTextJa":"今日は本当に疲れた",'
                            '"suggestedUserReplyJa":"今日は本当に疲れた",'
                            '"corrections":[],'
                            '"reviewCards":[]}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr("app.providers._post_json", fake_post_json)
    provider = OpenAICompatibleLLMProvider(
        api_key="secret",
        base_url="https://llm.example/v1",
        model="test-model",
        response_format_mode="json_schema",
    )
    turn = provider.generate_turn(
        {"id": "yui", "displayName": "유이"},
        {"id": "tired_today", "primaryPhraseKo": "오늘 너무 피곤했어", "primaryPhraseJa": "今日めっちゃ疲れた"},
        "오늘 정말 피곤했어",
    )
    assert captured["responseFormat"]["type"] == "json_schema"
    assert captured["responseFormat"]["json_schema"]["strict"] is True
    assert "schemaVersion" in captured["responseFormat"]["json_schema"]["schema"]["required"]
    assert turn["assistantText"] == "스키마 모드 응답이야."


def test_openai_compatible_llm_repairs_malformed_structured_json_once(monkeypatch):
    calls = {"count": 0}

    def fake_post_json(url, payload, api_key, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"choices": [{"message": {"content": '{"assistantTextKo":"좋아"}'}}]}
        assert payload["temperature"] == 0.1
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"schemaVersion":"turn_payload_v1",'
                            '"assistantTextKo":"수정해서 다시 줄게.",'
                            '"spokenTextJa":"今日は少し疲れた",'
                            '"suggestedUserReplyJa":"今日は少し疲れた",'
                            '"corrections":[],'
                            '"reviewCards":[{"front":"오늘 좀 피곤했어","back":"今日は少し疲れた","tags":["감정표현"]}]}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr("app.providers._post_json", fake_post_json)
    provider = OpenAICompatibleLLMProvider(api_key="secret", base_url="https://llm.example/v1", model="test-model", repair_attempts=1)
    turn = provider.generate_turn(
        {"id": "yui", "displayName": "유이"},
        {"id": "tired_today", "primaryPhraseKo": "오늘 너무 피곤했어", "primaryPhraseJa": "今日めっちゃ疲れた"},
        "오늘 좀 피곤했어",
    )
    assert calls["count"] == 2
    assert turn["assistantText"] == "수정해서 다시 줄게."
    assert turn["spokenText"] == "今日は少し疲れた。"
    assert turn["providerWarning"] == "openai_compatible_repaired_structured_output"


def test_openai_compatible_llm_uses_multiple_repair_attempts(monkeypatch):
    calls = {"count": 0}

    def fake_post_json(url, payload, api_key, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"choices": [{"message": {"content": '{"assistantTextKo":"schema 없음"}'}}]}
        assert payload["temperature"] == 0.1
        if calls["count"] == 2:
            return {"choices": [{"message": {"content": '{"schemaVersion":"turn_payload_v1","assistantTextKo":"아직 부족"}'}}]}
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"schemaVersion":"turn_payload_v1",'
                            '"assistantTextKo":"두 번째 repair에서 정상화했어.",'
                            '"spokenTextJa":"今日はかなり疲れた",'
                            '"suggestedUserReplyJa":"今日はかなり疲れた",'
                            '"corrections":[],'
                            '"reviewCards":[{"front":"오늘 꽤 피곤했어","back":"今日はかなり疲れた","tags":["감정표현"]}]}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr("app.providers._post_json", fake_post_json)
    provider = OpenAICompatibleLLMProvider(api_key="secret", base_url="https://llm.example/v1", model="test-model", repair_attempts=2)
    turn = provider.generate_turn(
        {"id": "yui", "displayName": "유이"},
        {"id": "tired_today", "primaryPhraseKo": "오늘 너무 피곤했어", "primaryPhraseJa": "今日めっちゃ疲れた"},
        "오늘 꽤 피곤했어",
    )
    assert calls["count"] == 3
    assert turn["assistantText"] == "두 번째 repair에서 정상화했어."
    assert turn["spokenText"] == "今日はかなり疲れた。"
    assert turn["providerWarning"] == "openai_compatible_repaired_structured_output"


def test_openai_compatible_llm_rejects_malformed_structured_json(monkeypatch):
    def fake_post_json(url, payload, api_key, timeout):
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"schemaVersion":"old_payload",'
                            '"assistantTextKo":"빠진 필드가 있어",'
                            '"spokenTextJa":"今日は少し疲れた",'
                            '"suggestedUserReplyJa":"今日は少し疲れた",'
                            '"corrections":[],'
                            '"reviewCards":[]}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr("app.providers._post_json", fake_post_json)
    provider = OpenAICompatibleLLMProvider(api_key="secret", base_url="https://llm.example/v1", model="test-model")
    turn = provider.generate_turn(
        {"id": "yui", "displayName": "유이"},
        {"id": "tired_today", "primaryPhraseKo": "오늘 너무 피곤했어", "primaryPhraseJa": "今日めっちゃ疲れた"},
        "오늘 정말 피곤했어",
    )
    assert turn["spokenText"] == "今日めっちゃ疲れた。"
    assert turn["providerWarning"] == "openai_compatible_fallback:unsupported_schemaVersion"


def test_backend_benchmark_script_scores_at_least_105():
    result = subprocess.run(
        [sys.executable, str(API_ROOT / "scripts" / "backend_benchmark_105.py")],
        cwd=str(API_ROOT),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = yaml.safe_load(result.stdout)
    assert payload["score"] >= 105
    assert payload["passed"] is True
    assert payload["checks"]["anki_apkg_export"] is True


def test_openapi_contract_validation_script_is_independent_and_green():
    result = subprocess.run(
        [sys.executable, str(API_ROOT / "scripts" / "validate_openapi_contract.py")],
        cwd=str(API_ROOT),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = yaml.safe_load(result.stdout)
    contract = yaml.safe_load((PROJECT_ROOT / "contracts" / "openapi_v0.yaml").read_text(encoding="utf-8"))
    expected_operations = sum(1 for path_item in contract["paths"].values() for method in path_item if method in {"get", "post", "put", "patch", "delete"})
    assert payload["allContractOperationsImplemented"] is True
    assert payload["checkedOperations"] == expected_operations
    assert payload["errors"] == []
    assert payload["undocumentedBackendRoutes"] == []
    assert all(check["ok"] for check in payload["checks"])


def test_docker_artifact_static_verification_script_is_green():
    result = subprocess.run(
        [sys.executable, str(API_ROOT / "scripts" / "verify_docker_smoke.py")],
        cwd=str(API_ROOT),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = yaml.safe_load(result.stdout)
    assert payload["passed"] is True
    assert payload["staticVerificationPassed"] is True
    assert payload["runtimeSmokeEnabled"] is False
    assert payload["runtimeEvidenceComplete"] is False
    assert payload["runtimeChecks"]["docker_python_multipart_import"]["status"] == "skipped"
    assert payload["composeStaticChecks"]["port8000Mapped"] is True
    assert payload["dockerfileStaticChecks"]["EXPOSE 8000"] is True
    assert payload["prodRequirementStaticChecks"]["pythonMultipartForSttMultipart"] is True
    assert payload["prodRequirementStaticChecks"]["pythonMultipartSecurityFloor"] is True


def test_stt_multipart_missingfile(tmp_path):
    client=make_client(tmp_path)
    response=client.post("/v1/stt/transcribe", files={"language": (None, "ja")})
    assert response.status_code==422
    assert "Missing or bad audio file" in response.json()["detail"]


def test_stt_multipart_filetype(tmp_path):
    client=make_client(tmp_path)
    response=client.post("/v1/stt/transcribe", files={"file": ("test.txt", b"not an audio file", "text/plain")})
    assert response.status_code==422
    assert "File must be an audio type." in response.json()["detail"]


def test_stt_multipart_empty(tmp_path):
    client=make_client(tmp_path)
    empty_file=b""
    response=client.post("/v1/stt/transcribe", files={"file":("empty.wav",empty_file,"audio/wav")})
    assert response.status_code==422
    assert "Audio file is empty" in response.json()["detail"]