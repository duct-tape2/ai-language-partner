from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from fastapi.routing import APIRoute

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_ROOT.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.main import create_app


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _path_params(path: str) -> set[str]:
    return set(re.findall(r"{([^}]+)}", path))


def validate_contract() -> dict[str, Any]:
    contract_path = PROJECT_ROOT / "contracts" / "openapi_v0.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    app = create_app(":memory:")

    routes: dict[tuple[str, str], APIRoute] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or set():
            lowered = method.lower()
            if lowered in HTTP_METHODS:
                routes[(route.path, lowered)] = route

    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for path, item in contract["paths"].items():
        for method, operation in item.items():
            if method not in HTTP_METHODS:
                continue
            route = routes.get((path, method))
            route_found = route is not None
            contract_params = {
                param["name"]
                for param in operation.get("parameters", [])
                if param.get("in") == "path"
            }
            route_params = _path_params(path)
            params_match = contract_params == route_params
            responses = operation.get("responses", {})
            response_success = any(str(code).startswith("2") for code in responses)
            request_body_required = bool(operation.get("requestBody", {}).get("required"))
            route_has_body_model = bool(getattr(route, "body_field", None)) if route else False
            manual_request_body = operation.get("x-manualRequestBody") is True
            body_shape_ok = (not request_body_required) or route_has_body_model or manual_request_body
            ok = route_found and params_match and response_success and body_shape_ok
            if not ok:
                errors.append(f"{method.upper()} {path}")
            checks.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "operationId": operation.get("operationId"),
                    "routeFound": route_found,
                    "pathParams": sorted(route_params),
                    "contractPathParams": sorted(contract_params),
                    "pathParamsMatch": params_match,
                    "responseSuccessDeclared": response_success,
                    "requestBodyRequired": request_body_required,
                    "routeHasBodyModel": route_has_body_model,
                    "manualRequestBody": manual_request_body,
                    "ok": ok,
                }
            )

    extra_routes = sorted(
        {" ".join((method.upper(), path)) for (path, method) in routes}
        - {" ".join((check["method"], check["path"])) for check in checks}
    )
    for route in extra_routes:
        errors.append(f"UNDOCUMENTED {route}")

    return {
        "contractPath": str(contract_path),
        "projectId": "ai-language-partner-mobile-shared-20260629-v1",
        "checkedOperations": len(checks),
        "allContractOperationsImplemented": not errors,
        "errors": errors,
        "extraBackendRoutes": extra_routes,
        "undocumentedBackendRoutes": extra_routes,
        "checks": checks,
    }


def main() -> int:
    result = validate_contract()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["allContractOperationsImplemented"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
