# Third-Party Notices

This repository contains application source code and small sample dialogue
source files only.

## Not Vendored

The following tools or assets are intentionally not distributed in this source
tree:

- AivisSpeech / VOICEVOX-compatible local voice engines
- whisper.cpp binaries and ggml model files
- generated voice clips
- generated dialogue pack archives
- local SQLite databases

Operators install or generate those assets separately and must follow the
licenses and attribution rules of the tools and voices they choose.

## Runtime Attribution

The backend voice catalog exposes `creditText` for voices. User interfaces that
play or preview a voice should display that credit text.

