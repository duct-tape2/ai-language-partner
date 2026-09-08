from __future__ import annotations

import ipaddress
import os
import sys
import tempfile
import urllib.parse
from pathlib import Path

import atheris
from fastapi import HTTPException

API_ROOT = Path(os.environ.get("AI_LANGUAGE_PARTNER_API_ROOT", Path(__file__).resolve().parents[1] / "apps" / "api"))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import main


def _invalid_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit((url or "").strip())
        port = parsed.port
        host = parsed.hostname
    except ValueError:
        return True
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
        return True
    try:
        address = ipaddress.ip_address(host) if host != "localhost" else ipaddress.ip_address("127.0.0.1")
    except ValueError:
        return True
    return not address.is_loopback


def _test_url(value: str) -> None:
    try:
        result = main._local_anki_connect_url(value)
    except HTTPException:
        return
    except Exception:
        raise

    if _invalid_url(value):
        raise AssertionError(f"accepted invalid AnkiConnect URL: {value!r}")
    parsed = urllib.parse.urlsplit(result)
    if parsed.scheme != "http" or parsed.port != 8765 or parsed.path != "/":
        raise AssertionError(f"returned non-canonical AnkiConnect URL: {result!r}")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AssertionError(f"returned URL with forbidden components: {result!r}")
    address = ipaddress.ip_address(parsed.hostname or "")
    if not address.is_loopback:
        raise AssertionError(f"returned non-loopback AnkiConnect URL: {result!r}")


def _test_segment(value: str) -> None:
    try:
        result = main._safe_path_segment(value, "fuzz identifier")
    except HTTPException:
        return
    except Exception:
        raise

    if result != value:
        raise AssertionError("safe path segment was changed")
    if not result or len(result) > 160 or result != result.strip():
        raise AssertionError(f"accepted unsafe path segment: {value!r}")
    if any(not (char.isalnum() or char in {"_", "-"}) for char in result):
        raise AssertionError(f"accepted forbidden path characters: {value!r}")


def _test_path(value: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "root"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        (outside / "payload.txt").write_text("sentinel", encoding="utf-8")

        escaped_by_symlink = root / "link"
        try:
            escaped_by_symlink.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            escaped_by_symlink = None

        segments = tuple(part for part in value.split("/") if part)
        if not segments:
            segments = ("safe",)
        if escaped_by_symlink is not None and segments[0] == "link":
            segments = ("link",) + segments[1:]

        try:
            result = main._resolve_contained_path(root, *segments)
        except HTTPException:
            return
        except Exception:
            raise

        root_resolved = root.resolve()
        try:
            result.relative_to(root_resolved)
        except ValueError as error:
            raise AssertionError(f"resolved path escaped root: {result}") from error


def TestOneInput(data: bytes) -> None:
    if not data:
        return
    mode = data[:1]
    value = data[1:].decode("utf-8", errors="replace")
    if mode == b"u":
        _test_url(value)
    elif mode == b"s":
        _test_segment(value)
    elif mode == b"p":
        _test_path(value)


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
