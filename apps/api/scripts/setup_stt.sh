#!/usr/bin/env bash
set -euo pipefail

BIN="${AI_LANGUAGE_PARTNER_WHISPER_CPP_BIN:-/opt/homebrew/bin/whisper-cli}"
MODEL="${AI_LANGUAGE_PARTNER_WHISPER_CPP_MODEL:-$HOME/whisper-models/ggml-medium.bin}"

python3 - "$BIN" "$MODEL" <<'PY'
import json
import shutil
import sys
from pathlib import Path

binary = Path(sys.argv[1]).expanduser()
model = Path(sys.argv[2]).expanduser()
result = {
    "ok": binary.exists() and model.exists() and shutil.which("ffmpeg") is not None,
    "binary": str(binary),
    "binaryPresent": binary.exists(),
    "model": str(model),
    "modelPresent": model.exists(),
    "ffmpegPresent": shutil.which("ffmpeg") is not None,
    "providerEnv": "AI_LANGUAGE_PARTNER_STT_PROVIDER=whisper_cpp",
}
print(json.dumps(result, ensure_ascii=False))
if not result["ok"]:
    raise SystemExit(1)
PY
