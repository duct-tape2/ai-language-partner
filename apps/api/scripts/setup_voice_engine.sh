#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AI_LANGUAGE_PARTNER_VOICE_ENGINE_URL:-http://127.0.0.1:10101}"

echo "voice_engine_base_url=${BASE_URL}"
if curl -fsS "${BASE_URL}/speakers" >/tmp/ai_language_partner_speakers.json 2>/dev/null; then
  python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/tmp/ai_language_partner_speakers.json").read_text(encoding="utf-8"))
styles = sum(len(s.get("styles") or []) for s in data)
print(json.dumps({"ok": True, "speakers": len(data), "styles": styles, "catalogSource": "live_speakers"}, ensure_ascii=False))
PY
  exit 0
fi

cat <<'TXT'
{"ok":false,"reason":"voice_engine_not_running","next":"Start VOICEVOX or AivisSpeech engine on 127.0.0.1:10101. The API will honestly return voicevox_compat_fallback_* until /speakers responds."}
TXT
