from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.main import create_app
from app.seed import COURSE_CATALOG, PRACTICE_ROOMS

PROJECT_ID = "ai-language-partner-mobile-shared-20260629-v1"


def _enabled(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_present(env: Mapping[str, str], key: str) -> bool:
    return bool((env.get(key) or "").strip())


def _redacted_env(env: Mapping[str, str], key: str) -> dict[str, Any]:
    return {"name": key, "present": _env_present(env, key), "valueReturned": False}


def _skip(check_id: str, reason: str, configured: bool = False, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    result = {"id": check_id, "status": "skipped", "configured": configured, "reason": reason}
    if extra:
        result.update(extra)
    return result


def _fail(check_id: str, reason: str, configured: bool = True, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    result = {"id": check_id, "status": "failed", "configured": configured, "reason": reason}
    if extra:
        result.update(extra)
    return result


def _pass(check_id: str, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    result = {"id": check_id, "status": "passed", "configured": True}
    if extra:
        result.update(extra)
    return result


def _json_or_text_request(
    url: str,
    method: str,
    timeout_seconds: int,
    headers: dict[str, str],
    payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
        content_type = response.headers.get("content-type", "")
        parsed: Any = None
        if "json" in content_type.lower() or raw.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None
        return {
            "statusCode": int(response.status),
            "contentType": content_type,
            "json": parsed if isinstance(parsed, dict) else None,
            "bodyBytes": len(raw.encode("utf-8")),
        }


def verify_local_api_scheduler_tick() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmpdir:
        client = TestClient(create_app(Path(tmpdir) / "scheduler_readiness.sqlite3"))
        editor_headers = {
            "X-Admin-Key": "local-dev-admin",
            "X-Admin-Role": "editor",
            "X-Admin-User": "scheduler-readiness-editor",
        }
        reviewer_headers = {
            "X-Admin-Key": "local-dev-admin",
            "X-Admin-Role": "reviewer",
            "X-Admin-User": "scheduler-readiness-reviewer",
        }
        publisher_headers = {
            "X-Admin-Key": "local-dev-admin",
            "X-Admin-Role": "publisher",
            "X-Admin-User": "scheduler-readiness-publisher",
        }
        bundle = {
            "courses": copy.deepcopy(COURSE_CATALOG),
            "practiceRooms": copy.deepcopy(PRACTICE_ROOMS),
        }
        original_title = bundle["courses"][0]["title"]
        bundle["courses"][0]["title"] = f"{original_title} - scheduler readiness"
        dry_run = client.post("/v1/content/import", headers=editor_headers, json=bundle)
        if dry_run.status_code != 200:
            return _fail("local_api_scheduler_tick", "content_import_failed", extra={"statusCode": dry_run.status_code})
        version_id = dry_run.json()["version"]["id"]
        submit = client.post(
            f"/v1/content/versions/{version_id}/submit-review",
            headers=editor_headers,
            json={"note": "scheduler readiness candidate"},
        )
        approve = client.post(
            f"/v1/content/versions/{version_id}/approve",
            headers=reviewer_headers,
            json={"note": "scheduler readiness approved"},
        )
        if submit.status_code != 200 or approve.status_code != 200:
            return _fail(
                "local_api_scheduler_tick",
                "content_review_flow_failed",
                extra={"submitStatusCode": submit.status_code, "approveStatusCode": approve.status_code},
            )
        release = client.post(
            "/v1/content/releases",
            headers=editor_headers,
            json={
                "versionId": version_id,
                "title": "Scheduler readiness due release",
                "releaseStrategy": "scheduled",
                "rolloutPercent": 100,
                "scheduledAt": "2000-01-01T00:00:00Z",
            },
        )
        if release.status_code != 200:
            return _fail("local_api_scheduler_tick", "content_release_plan_failed", extra={"statusCode": release.status_code})
        release_id = release.json()["release"]["id"]
        job = client.post(
            "/v1/content/operations/jobs",
            headers=editor_headers,
            json={"jobType": "validate_bundle", "priority": "high", "payload": {"bundle": bundle}},
        )
        if job.status_code != 200:
            return _fail("local_api_scheduler_tick", "content_operation_job_queue_failed", extra={"statusCode": job.status_code})
        job_id = job.json()["job"]["id"]
        viewer_forbidden = client.post(
            "/v1/content/scheduler/run-once",
            headers={"X-Admin-Key": "local-dev-admin", "X-Admin-Role": "viewer", "X-Admin-User": "scheduler-readiness-viewer"},
            json={"confirmation": "run-content-scheduler-once"},
        )
        tick = client.post(
            "/v1/content/scheduler/run-once",
            headers=publisher_headers,
            json={
                "confirmation": "run-content-scheduler-once",
                "schedulerKey": "readiness_content_ops",
                "leaseOwner": "readiness-local-worker",
                "maxOperationJobs": 1,
                "releaseLimit": 10,
            },
        )
        if tick.status_code != 200:
            return _fail("local_api_scheduler_tick", "scheduler_tick_failed", extra={"statusCode": tick.status_code})
        tick_payload = tick.json()
        run_id = tick_payload["run"]["id"]
        runs = client.get("/v1/content/scheduler/runs?status=succeeded", headers=publisher_headers)
        live_course = client.get(f"/v1/courses/{bundle['courses'][0]['id']}").json()["course"]
        operation_job = tick_payload["operationJobs"][0]["job"] if tick_payload.get("operationJobs") else {}
        ok = (
            tick_payload.get("ok") is True
            and tick_payload["run"]["status"] == "succeeded"
            and tick_payload["releaseWorker"]["appliedCount"] == 1
            and tick_payload["releaseWorker"]["appliedReleases"][0]["id"] == release_id
            and operation_job.get("id") == job_id
            and operation_job.get("status") == "succeeded"
            and any(item["id"] == run_id for item in runs.json().get("runs", []))
            and live_course["title"].endswith("scheduler readiness")
            and viewer_forbidden.status_code == 403
        )
        if not ok:
            return _fail(
                "local_api_scheduler_tick",
                "scheduler_evidence_mismatch",
                extra={
                    "runStatus": tick_payload.get("run", {}).get("status"),
                    "appliedCount": tick_payload.get("releaseWorker", {}).get("appliedCount"),
                    "operationJobStatus": operation_job.get("status"),
                    "historyStatusCode": runs.status_code,
                    "viewerForbiddenStatusCode": viewer_forbidden.status_code,
                },
            )
        return _pass(
            "local_api_scheduler_tick",
            {
                "runId": run_id,
                "releaseId": release_id,
                "operationJobId": job_id,
                "leaseOwner": tick_payload["run"]["leaseOwner"],
                "releaseAppliedCount": tick_payload["releaseWorker"]["appliedCount"],
                "operationJobsRunCount": tick_payload["run"]["result"]["operationJobsRunCount"],
                "runHistoryContainsRun": True,
                "viewerRunRejectedStatus": viewer_forbidden.status_code,
            },
        )


def verify_scheduler_env_redaction(env: Mapping[str, str]) -> dict[str, Any]:
    keys = [
        "AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_HEALTH_URL",
        "AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_RUN_URL",
        "AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_TOKEN",
        "AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_AUTH_HEADER",
    ]
    serialized = json.dumps({key: env.get(key) for key in keys}, ensure_ascii=False, sort_keys=True)
    redacted = [_redacted_env(env, key) for key in keys]
    returned = json.dumps(redacted, ensure_ascii=False, sort_keys=True)
    leaked = any((env.get(key) or "") and env.get(key) in returned for key in keys)
    return _pass(
        "hosted_scheduler_env_redaction",
        {
            "env": redacted,
            "secretsReturned": False,
            "configured": any(item["present"] for item in redacted),
            "rawEnvSerializedBytes": len(serialized.encode("utf-8")),
        },
    ) if not leaked else _fail("hosted_scheduler_env_redaction", "hosted_scheduler_env_value_leaked")


def _hosted_headers(env: Mapping[str, str]) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    token = (env.get("AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_TOKEN") or "").strip()
    header_name = (env.get("AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_AUTH_HEADER") or "X-Admin-Key").strip()
    if token and header_name:
        headers[header_name] = f"Bearer {token}" if header_name.lower() == "authorization" else token
    if "X-Admin-Key" in headers:
        headers.setdefault("X-Admin-Role", "publisher")
        headers.setdefault("X-Admin-User", "hosted-scheduler-readiness")
    return headers


def verify_hosted_scheduler_health(env: Mapping[str, str], real_calls: bool, timeout_seconds: int) -> dict[str, Any]:
    url = (env.get("AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_HEALTH_URL") or "").strip()
    if not url:
        return _skip("hosted_scheduler_health", "health_url_not_configured", configured=False)
    if not real_calls:
        return _skip("hosted_scheduler_health", "real_calls_disabled", configured=True)
    try:
        response = _json_or_text_request(url, "GET", timeout_seconds, _hosted_headers(env))
        ok = 200 <= response["statusCode"] < 400
        return _pass(
            "hosted_scheduler_health",
            {"statusCode": response["statusCode"], "contentType": response["contentType"], "bodyBytes": response["bodyBytes"]},
        ) if ok else _fail("hosted_scheduler_health", "health_status_not_success", extra={"statusCode": response["statusCode"]})
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return _fail("hosted_scheduler_health", exc.__class__.__name__)
    except Exception as exc:
        return _fail("hosted_scheduler_health", exc.__class__.__name__)


def verify_hosted_scheduler_run_once(env: Mapping[str, str], real_calls: bool, timeout_seconds: int) -> dict[str, Any]:
    url = (env.get("AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_RUN_URL") or "").strip()
    if not url:
        return _skip("hosted_scheduler_run_once", "run_url_not_configured", configured=False)
    if not real_calls:
        return _skip("hosted_scheduler_run_once", "real_calls_disabled", configured=True)
    payload = {
        "confirmation": "run-content-scheduler-once",
        "schedulerKey": "hosted_readiness_content_ops",
        "leaseOwner": "hosted-scheduler-readiness",
        "maxOperationJobs": 0,
        "releaseLimit": 1,
    }
    try:
        response = _json_or_text_request(url, "POST", timeout_seconds, _hosted_headers(env), payload=payload)
        body = response.get("json") or {}
        ok = 200 <= response["statusCode"] < 400 and (body.get("ok") is True or body == {})
        return _pass(
            "hosted_scheduler_run_once",
            {
                "statusCode": response["statusCode"],
                "contentType": response["contentType"],
                "bodyBytes": response["bodyBytes"],
                "jsonKeys": sorted(body.keys())[:20],
            },
        ) if ok else _fail("hosted_scheduler_run_once", "run_status_not_success", extra={"statusCode": response["statusCode"]})
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return _fail("hosted_scheduler_run_once", exc.__class__.__name__)
    except Exception as exc:
        return _fail("hosted_scheduler_run_once", exc.__class__.__name__)


def verify_hosted_scheduler_readiness(env: Optional[Mapping[str, str]] = None) -> dict[str, Any]:
    values = env or os.environ
    real_calls = _enabled(values.get("AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_REAL_CALLS"))
    timeout_seconds = max(1, min(120, int(values.get("AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_TIMEOUT_SECONDS", "10"))))
    checks = [
        verify_local_api_scheduler_tick(),
        verify_scheduler_env_redaction(values),
        verify_hosted_scheduler_health(values, real_calls, timeout_seconds),
        verify_hosted_scheduler_run_once(values, real_calls, timeout_seconds),
    ]
    failed = [item for item in checks if item["status"] == "failed"]
    passed = [item for item in checks if item["status"] == "passed"]
    skipped = [item for item in checks if item["status"] == "skipped"]
    hosted_statuses = {item["id"]: item["status"] for item in checks if item["id"].startswith("hosted_scheduler_") and item["id"] != "hosted_scheduler_env_redaction"}
    return {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "projectId": PROJECT_ID,
        "realCallsEnabled": real_calls,
        "hostedSchedulerHealthUrlConfigured": _env_present(values, "AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_HEALTH_URL"),
        "hostedSchedulerRunUrlConfigured": _env_present(values, "AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_RUN_URL"),
        "hostedSchedulerTokenConfigured": _env_present(values, "AI_LANGUAGE_PARTNER_HOSTED_SCHEDULER_TOKEN"),
        "hostedSchedulerValuesReturned": False,
        "secretsReturned": False,
        "timeoutSeconds": timeout_seconds,
        "passed": not failed,
        "localSchedulerEvidenceComplete": checks[0]["status"] == "passed",
        "realHostedSchedulerEvidenceComplete": real_calls
        and not failed
        and bool(hosted_statuses)
        and all(status == "passed" for status in hosted_statuses.values()),
        "summary": {"passed": len(passed), "skipped": len(skipped), "failed": len(failed)},
        "checks": {item["id"]: item for item in checks},
    }


def main() -> int:
    result = verify_hosted_scheduler_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
