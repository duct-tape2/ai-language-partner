# Roadmap

This document lists planned dialogue-bank packs and related milestones.
It is a living document and changes as packs are authored, reviewed, and released.

## Dialogue-bank packs

| Persona | Pack version | Status | Notes |
|---------|--------------|--------|-------|
| yui | v1 | live | Greetings and self-introduction topics, N5 level |
| haruka | v1 | authoring | Companion persona for daily conversation |
| ren | v1 | authoring | Casual conversation style |
| akari | v1 | backlog | Polite workplace style |
| takeshi | v1 | backlog | Formal instruction style |
| sachiko | v1 | backlog | Soft explanatory style |
| kota | v1 | backlog | Junior learner peer style |
| shiro | v1 | backlog | Calm reflective style |

Status values: live, authoring, backlog.

A pack is live when story.json, manifest.json, and variants.csv are
committed under packs/{persona}/{version}/ and served through
GET /v1/dialogue/packs/{personaId}/{packVersion}.zip.

## Related milestones

- Expand JLPT coverage beyond N4 sample content.
- Add cultural-safety review examples per pack.
- Keep pack source-only in git (no generated audio, archives, or databases).

## How to propose a pack

Open an issue labeled content and describe persona, topics, level,
and sample lines. Maintainers add accepted proposals to the table above.
