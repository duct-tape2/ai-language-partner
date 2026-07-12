from __future__ import annotations

import ast
import base64
import contextlib
import hashlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import verify_external_provider_readiness as external_provider  # noqa: E402
from scripts import verify_redis_rate_limit_readiness as redis_readiness  # noqa: E402
import check_public_tree  # noqa: E402

try:
    from scripts import backend_benchmark_105 as benchmark  # noqa: E402
except ModuleNotFoundError:
    benchmark = None


OUTPUT_SECRET = "ci-output-secret-value"
OUTPUT_URL = f"redis://ci-user:{OUTPUT_SECRET}@redis.example:6379/0?token={OUTPUT_SECRET}"


def _benchmark_pkce_s256_challenge():
    """Load the exact helper source without requiring benchmark-only FastAPI dependencies."""
    source_path = API_ROOT / "scripts" / "backend_benchmark_105.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "pkce_s256_challenge")
    namespace = {"base64": base64, "hashlib": hashlib}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace["pkce_s256_challenge"]


class SecurityOutputBoundariesTest(unittest.TestCase):
    def test_local_oidc_mock_detection_parses_the_exact_host(self) -> None:
        self.assertTrue(external_provider._is_local_oidc_mock_issuer("https://local-oidc.example"))
        self.assertTrue(external_provider._is_local_oidc_mock_issuer("https://local-oidc.example:443/issuer"))
        self.assertFalse(external_provider._is_local_oidc_mock_issuer("https://local-oidc.example.attacker.test"))
        self.assertFalse(external_provider._is_local_oidc_mock_issuer("https://local-oidc.example@attacker.test"))
        self.assertFalse(external_provider._is_local_oidc_mock_issuer("https://local-oidc.example:invalid"))

    def test_pkce_s256_matches_the_rfc_7636_appendix_b_vector(self) -> None:
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        challenge = benchmark.pkce_s256_challenge if benchmark is not None else _benchmark_pkce_s256_challenge()
        self.assertEqual(
            challenge(verifier),
            "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        )

    def test_json_entrypoints_exclude_credentials_but_keep_ci_evidence(self) -> None:
        reports = [
            (external_provider, "verify_external_provider_readiness", {"passed": True, "checks": {"smoke": "passed"}}),
            (redis_readiness, "verify_redis_rate_limit_readiness", {"passed": True, "checks": {"redis": "passed"}}),
        ]
        if benchmark is not None:
            reports.append((benchmark, "run_benchmark", {"score": 105, "target": 105, "passed": True, "checks": {"smoke": True}}))
        for module, report_function, report in reports:
            report = {
                **report,
                "accessToken": OUTPUT_SECRET,
                "providerUrl": OUTPUT_URL,
                "diagnostic": f"Bearer {OUTPUT_SECRET}",
            }
            stdout = io.StringIO()
            with (
                mock.patch.object(module, report_function, return_value=report),
                mock.patch.dict(os.environ, {"CI_OUTPUT_SECRET": OUTPUT_SECRET}),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(module.main(), 0)
            output = stdout.getvalue()
            self.assertNotIn(OUTPUT_SECRET, output)
            self.assertNotIn("ci-user", output)
            self.assertIn('"passed": true', output)
            if module is external_provider:
                self.assertIn("redis.example:6379/0", output)
            else:
                self.assertNotIn("redis.example", output)

    def test_benchmark_entrypoint_outputs_only_the_public_summary(self) -> None:
        source = (API_ROOT / "scripts" / "backend_benchmark_105.py").read_text(encoding="utf-8")
        self.assertIn("print(json.dumps(_public_benchmark_result(result)", source)

    def test_public_tree_forbidden_path_diagnostics_redact_credentials_and_tokens(self) -> None:
        token = "ghp_" + ("A" * 36)
        unsafe_path = f"artifacts/redis://ci-user:{OUTPUT_SECRET}@redis.example/0/{token}.log"
        stderr = io.StringIO()
        with mock.patch.object(check_public_tree, "tracked_files", return_value=[unsafe_path]), contextlib.redirect_stderr(stderr):
            self.assertEqual(check_public_tree.main(), 1)
        output = stderr.getvalue()
        self.assertNotIn(OUTPUT_SECRET, output)
        self.assertNotIn("ci-user", output)
        self.assertNotIn(token, output)
        self.assertIn("redis.example", output)

    def test_public_tree_secret_hits_withhold_paths_from_ci_output(self) -> None:
        token = "ghp_" + ("A" * 36)
        stderr = io.StringIO()
        with (
            mock.patch.object(check_public_tree, "tracked_files", return_value=["docs/private-token-note.txt"]),
            mock.patch("builtins.open", mock.mock_open(read_data=token)),
            contextlib.redirect_stderr(stderr),
        ):
            self.assertEqual(check_public_tree.main(), 1)
        output = stderr.getvalue()
        self.assertNotIn(token, output)
        self.assertNotIn("private-token-note", output)
        self.assertIn("1 tracked file(s)", output)


if __name__ == "__main__":
    unittest.main()
