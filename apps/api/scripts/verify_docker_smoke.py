from __future__ import annotations

import json
import os
import re
import socket
import shutil
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional

import yaml


API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "ai-language-partner-mobile-shared-20260629-v1"
PYTHON_MULTIPART_MIN_VERSION = (0, 0, 31)
PYTHON_MULTIPART_MIN_VERSION_TEXT = ".".join(str(part) for part in PYTHON_MULTIPART_MIN_VERSION)


def _enabled(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


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


def _tail(text: str, limit: int = 1600) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _version_tuple(version_text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version_text)[:4])


def python_multipart_requirement_check(requirements_text: str) -> dict[str, bool]:
    requirement_lines = [
        line.split("#", 1)[0].strip()
        for line in requirements_text.splitlines()
        if line.split("#", 1)[0].strip()
    ]
    matching_lines = [
        line
        for line in requirement_lines
        if re.match(r"(?i)^python-multipart(?=$|[\s<>=!~;\[])", line)
    ]
    present = bool(matching_lines)
    security_floor = False
    for line in matching_lines:
        floor_match = re.search(r">=\s*([0-9]+(?:\.[0-9]+){0,3})", line)
        exact_match = re.search(r"==\s*([0-9]+(?:\.[0-9]+){0,3})", line)
        if floor_match and _version_tuple(floor_match.group(1)) >= PYTHON_MULTIPART_MIN_VERSION:
            security_floor = True
        if exact_match and _version_tuple(exact_match.group(1)) >= PYTHON_MULTIPART_MIN_VERSION:
            security_floor = True
    return {
        "pythonMultipartForSttMultipart": present,
        "pythonMultipartSecurityFloor": security_floor,
    }


def _run_command(args: list[str], timeout_seconds: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            args,
            cwd=str(API_ROOT),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "returnCode": completed.returncode,
            "elapsedMs": int((time.perf_counter() - started) * 1000),
            "stdoutTail": _tail(completed.stdout),
            "stderrTail": _tail(completed.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "returnCode": -1,
            "elapsedMs": int((time.perf_counter() - started) * 1000),
            "stdoutTail": _tail(stdout),
            "stderrTail": _tail(stderr),
            "timedOut": True,
        }


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _container_runtime() -> tuple[Optional[str], Optional[str]]:
    for name in ["docker", "podman", "nerdctl"]:
        path = shutil.which(name)
        if path:
            return name, path
    return None, None


def _poll_health(url: str, timeout_seconds: int) -> dict[str, Any]:
    started = time.perf_counter()
    last_error = ""
    attempts = 0
    while (time.perf_counter() - started) < timeout_seconds:
        attempts += 1
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                body = response.read().decode("utf-8")
            payload = json.loads(body)
            if payload.get("projectId") == PROJECT_ID:
                return _pass(
                    "docker_health_endpoint",
                    {
                        "url": url,
                        "attempts": attempts,
                        "elapsedMs": int((time.perf_counter() - started) * 1000),
                        "projectId": payload.get("projectId"),
                    },
                )
            last_error = "project_id_mismatch"
        except Exception as exc:
            last_error = exc.__class__.__name__
        time.sleep(1)
    return _fail(
        "docker_health_endpoint",
        last_error or "health_timeout",
        extra={"url": url, "attempts": attempts, "elapsedMs": int((time.perf_counter() - started) * 1000)},
    )


def _run_runtime_smoke(values: Mapping[str, str]) -> dict[str, Any]:
    runtime_smoke_required = _enabled(values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_REQUIRED")) or _enabled(
        values.get("REQUIRE_DOCKER_SMOKE")
    )
    runtime_smoke_enabled = _enabled(values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_REAL_RUNS")) or runtime_smoke_required
    runtime_name, runtime_path = _container_runtime()
    checks: list[dict[str, Any]] = []
    runtime_build_executed = False
    runtime_container_executed = False
    image_tag = values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_IMAGE") or f"ai-language-partner-api-smoke:{uuid.uuid4().hex[:8]}"
    container_name = values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_CONTAINER") or f"ai-language-partner-api-smoke-{uuid.uuid4().hex[:8]}"
    build_timeout_seconds = max(30, min(1800, int(values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_BUILD_TIMEOUT_SECONDS", "600"))))
    run_timeout_seconds = max(10, min(300, int(values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_RUN_TIMEOUT_SECONDS", "60"))))
    health_timeout_seconds = max(5, min(300, int(values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_HEALTH_TIMEOUT_SECONDS", "45"))))
    host_port = int(values.get("AI_LANGUAGE_PARTNER_DOCKER_SMOKE_PORT") or _free_local_port())

    if runtime_name and runtime_path:
        checks.append(_pass("container_runtime_available", {"runtime": runtime_name, "path": runtime_path}))
    elif runtime_smoke_enabled:
        checks.append(_fail("container_runtime_available", "container_runtime_not_available", configured=True))
    else:
        checks.append(_skip("container_runtime_available", "container_runtime_not_available", configured=False))

    if not runtime_smoke_enabled:
        checks.extend(
            [
                _skip("docker_image_build", "real_runs_disabled", configured=bool(runtime_name)),
                _skip("docker_python_multipart_import", "real_runs_disabled", configured=bool(runtime_name)),
                _skip("docker_container_run", "real_runs_disabled", configured=bool(runtime_name)),
                _skip("docker_health_endpoint", "real_runs_disabled", configured=bool(runtime_name)),
            ]
        )
    elif not runtime_name or not runtime_path:
        checks.extend(
            [
                _skip("docker_image_build", "container_runtime_not_available", configured=False),
                _skip("docker_python_multipart_import", "container_runtime_not_available", configured=False),
                _skip("docker_container_run", "container_runtime_not_available", configured=False),
                _skip("docker_health_endpoint", "container_runtime_not_available", configured=False),
            ]
        )
    else:
        runtime_build_executed = True
        build = _run_command([runtime_path, "build", "-t", image_tag, "."], build_timeout_seconds)
        if build["returnCode"] != 0:
            checks.append(_fail("docker_image_build", "image_build_failed", extra=build))
            checks.extend(
                [
                    _skip("docker_python_multipart_import", "image_build_failed", configured=True),
                    _skip("docker_container_run", "image_build_failed", configured=True),
                    _skip("docker_health_endpoint", "image_build_failed", configured=True),
                ]
            )
        else:
            checks.append(
                _pass(
                    "docker_image_build",
                    {"runtime": runtime_name, "imageTag": image_tag, "elapsedMs": build["elapsedMs"]},
                )
            )
            multipart_import = _run_command(
                [runtime_path, "run", "--rm", "--entrypoint", "python", image_tag, "-c", "import multipart"],
                run_timeout_seconds,
            )
            if multipart_import["returnCode"] != 0:
                checks.append(
                    _fail(
                        "docker_python_multipart_import",
                        "python_multipart_import_failed",
                        extra=multipart_import,
                    )
                )
            else:
                checks.append(
                    _pass(
                        "docker_python_multipart_import",
                        {"runtime": runtime_name, "imageTag": image_tag, "elapsedMs": multipart_import["elapsedMs"]},
                    )
                )
            run_args = [
                runtime_path,
                "run",
                "--rm",
                "-d",
                "--name",
                container_name,
                "-p",
                f"127.0.0.1:{host_port}:8000",
                "-e",
                "AI_LANGUAGE_PARTNER_DB_PATH=/data/language_partner.sqlite3",
                "-e",
                "AI_LANGUAGE_PARTNER_LLM_PROVIDER=mock",
                "-e",
                "AI_LANGUAGE_PARTNER_TTS_PROVIDER=mock",
                "-e",
                "AI_LANGUAGE_PARTNER_STT_PROVIDER=mock",
                image_tag,
            ]
            runtime_container_executed = True
            run_result = _run_command(run_args, run_timeout_seconds)
            try:
                if run_result["returnCode"] != 0:
                    checks.append(_fail("docker_container_run", "container_run_failed", extra=run_result))
                    checks.append(_skip("docker_health_endpoint", "container_run_failed", configured=True))
                else:
                    container_id = run_result["stdoutTail"].strip()
                    checks.append(
                        _pass(
                            "docker_container_run",
                            {
                                "runtime": runtime_name,
                                "containerName": container_name,
                                "containerIdPrefix": container_id[:12],
                                "hostPort": host_port,
                                "elapsedMs": run_result["elapsedMs"],
                            },
                        )
                    )
                    checks.append(_poll_health(f"http://127.0.0.1:{host_port}/health", health_timeout_seconds))
            finally:
                _run_command([runtime_path, "stop", container_name], 20)

    failed = [item for item in checks if item["status"] == "failed"]
    passed = [item for item in checks if item["status"] == "passed"]
    skipped = [item for item in checks if item["status"] == "skipped"]
    live_check_statuses = {item["id"]: item["status"] for item in checks if item["id"] != "container_runtime_available"}
    runtime_evidence_complete = (
        runtime_smoke_enabled
        and bool(runtime_name)
        and not failed
        and all(status == "passed" for status in live_check_statuses.values())
    )
    return {
        "runtimeSmokeEnabled": runtime_smoke_enabled,
        "runtimeSmokeRequired": runtime_smoke_required,
        "containerRuntime": runtime_name,
        "runtimeBuildExecuted": runtime_build_executed,
        "runtimeContainerExecuted": runtime_container_executed,
        "runtimeEvidenceComplete": runtime_evidence_complete,
        "runtimeBuildSkippedReason": None
        if runtime_build_executed
        else ("real_runs_disabled" if not runtime_smoke_enabled else "container_runtime_not_available"),
        "runtimeSmokePassed": not failed,
        "runtimeSummary": {"passed": len(passed), "skipped": len(skipped), "failed": len(failed)},
        "runtimeChecks": {item["id"]: item for item in checks},
    }


def verify_docker_smoke(env: Optional[Mapping[str, str]] = None) -> dict[str, Any]:
    values = env or os.environ
    dockerfile = API_ROOT / "Dockerfile"
    compose_file = API_ROOT / "docker-compose.yml"
    dockerfile_text = dockerfile.read_text(encoding="utf-8")
    prod_requirements_text = (API_ROOT / "requirements-prod.txt").read_text(encoding="utf-8")
    compose = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
    service = compose["services"]["api"]

    required_fragments = [
        "FROM python:3.11-slim@sha256:e031123e3d85762b141ad1cbc56452ba69c6e722ebf2f042cc0dc86c47c0d8b3",
        "WORKDIR /app",
        "COPY requirements-prod.txt .",
        "RUN pip install --no-cache-dir -r requirements-prod.txt",
        "COPY app ./app",
        "adduser --disabled-password",
        "chown -R appuser:appuser /app /data",
        "EXPOSE 8000",
        "HEALTHCHECK --interval=30s",
        "USER appuser",
        'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]',
    ]
    fragment_checks = {fragment: fragment in dockerfile_text for fragment in required_fragments}
    prod_requirement_checks = python_multipart_requirement_check(prod_requirements_text)
    compose_checks = {
        "serviceApiExists": "api" in compose.get("services", {}),
        "buildContextCurrentDirectory": service.get("build") == ".",
        "port8000Mapped": "8000:8000" in service.get("ports", []),
        "dbPathMounted": service.get("environment", {}).get("AI_LANGUAGE_PARTNER_DB_PATH") == "/data/language_partner.sqlite3",
        "mockProvidersConfigured": all(
            service.get("environment", {}).get(key) == "mock"
            for key in [
                "AI_LANGUAGE_PARTNER_LLM_PROVIDER",
                "AI_LANGUAGE_PARTNER_TTS_PROVIDER",
                "AI_LANGUAGE_PARTNER_STT_PROVIDER",
            ]
        ),
        "namedVolumeDeclared": "ai_language_partner_api_data" in compose.get("volumes", {}),
    }
    docker_cli = shutil.which("docker")
    podman_cli = shutil.which("podman")
    colima_cli = shutil.which("colima")
    nerdctl_cli = shutil.which("nerdctl")
    runtime_smoke = _run_runtime_smoke(values)
    static_verification_passed = (
        all(fragment_checks.values())
        and all(compose_checks.values())
        and all(prod_requirement_checks.values())
    )
    return {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "projectId": PROJECT_ID,
        "dockerfile": str(dockerfile),
        "composeFile": str(compose_file),
        "dockerfileStaticChecks": fragment_checks,
        "prodRequirementStaticChecks": prod_requirement_checks,
        "composeStaticChecks": compose_checks,
        "dockerCliAvailable": bool(docker_cli),
        "podmanAvailable": bool(podman_cli),
        "colimaAvailable": bool(colima_cli),
        "nerdctlAvailable": bool(nerdctl_cli),
        "runtimeSmokeEnabled": runtime_smoke["runtimeSmokeEnabled"],
        "runtimeSmokeRequired": runtime_smoke["runtimeSmokeRequired"],
        "containerRuntime": runtime_smoke["containerRuntime"],
        "runtimeBuildExecuted": runtime_smoke["runtimeBuildExecuted"],
        "runtimeContainerExecuted": runtime_smoke["runtimeContainerExecuted"],
        "runtimeBuildSkippedReason": runtime_smoke["runtimeBuildSkippedReason"],
        "runtimeSmokePassed": runtime_smoke["runtimeSmokePassed"],
        "runtimeEvidenceComplete": runtime_smoke["runtimeEvidenceComplete"],
        "runtimeSummary": runtime_smoke["runtimeSummary"],
        "runtimeChecks": runtime_smoke["runtimeChecks"],
        "staticVerificationPassed": static_verification_passed,
        "passed": static_verification_passed and runtime_smoke["runtimeSmokePassed"],
    }


def main() -> int:
    result = verify_docker_smoke()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
