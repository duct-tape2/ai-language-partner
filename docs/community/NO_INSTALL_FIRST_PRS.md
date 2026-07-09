# No-Install First PR Board

These tasks can be started in the GitHub web editor. They are useful for
contributors who can review Korean/Japanese wording, learner notes, setup docs,
or beginner dialogue content but do not want to install Expo, FastAPI, local
STT/TTS engines, or generated voice assets.

Only real, useful PRs count for Claude for OSS evidence. Do not split trivial
typos into separate PRs just to increase the count.

## How To Send A Browser-Only PR

1. Pick one issue from the table below.
2. Comment `/claim` on the issue if you want to avoid duplicate work.
3. Open the linked source file.
4. Click the pencil icon on GitHub, or use the direct edit link.
5. Make one focused improvement.
6. Use a PR title like `docs: improve Korean backend mock quickstart`.
7. In the PR body, write `Closes #ISSUE_NUMBER` and mention that the change is
   docs/content review.

No command-line check is required for plain wording review. If you edit JSON,
CSV, YAML, or TypeScript data, keep the existing structure unchanged.

Useful issue searches:

- `first-timers-only`: `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Afirst-timers-only`
- `up-for-grabs`: `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Aup-for-grabs`

The generated issue-comment text is tracked in
[`NO_INSTALL_FIRST_PR_COMMENTS.md`](NO_INSTALL_FIRST_PR_COMMENTS.md).

For the shortest path with PR title/body examples, use the
[five-minute first PR guide](FIVE_MINUTE_FIRST_PR.md).
For Japanese/Korean wording, dialogue, or cultural-safety review, use the
[language review first PR kit](LANGUAGE_REVIEW_FIRST_PR_KIT.md).

## Best Browser-Only Issues

| Issue | Good PR shape | Source file | Direct edit link |
|---|---|---|---|
| [#1: Korean quick-start for backend mock mode](https://github.com/duct-tape2/ai-language-partner/issues/1) | Add or clarify Korean setup notes for running the backend in mock mode | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#2: Japanese quick-start for mobile mock mode](https://github.com/duct-tape2/ai-language-partner/issues/2) | Add Japanese notes for running the mobile app without local engines | `docs/ja/index.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ja/index.md) |
| [#3: whisper.cpp setup on macOS](https://github.com/duct-tape2/ai-language-partner/issues/3) | Clarify ffmpeg, model path, env vars, and fallback behavior for local STT setup | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#4: AivisSpeech and VOICEVOX-compatible setup](https://github.com/duct-tape2/ai-language-partner/issues/4) | Clarify local TTS engine process setup, licensing boundaries, and the `/speakers` probe | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#5: architecture glossary for dialogue-bank terms](https://github.com/duct-tape2/ai-language-partner/issues/5) | Define learner-facing terms such as dialogue bank, pack, node, line, fallback | `docs/ARCHITECTURE.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ARCHITECTURE.md) |
| [#6: API curl examples for Daily Talk endpoints](https://github.com/duct-tape2/ai-language-partner/issues/6) | Add curl examples for packs, match, unmatched, voices, and provider status | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#7: yui v1 Korean translation review](https://github.com/duct-tape2/ai-language-partner/issues/7) | Review beginner Korean translations without touching generated audio | `packs/yui/v1/story.json` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| [#8: yui v1 Japanese naturalness review](https://github.com/duct-tape2/ai-language-partner/issues/8) | Review Japanese dialogue for natural beginner-safe wording while keeping line IDs stable | `packs/yui/v1/story.json` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| [#11: Korean learner notes on particle mistakes](https://github.com/duct-tape2/ai-language-partner/issues/11) | Add concise Korean notes about common Japanese particle mistakes | `docs/ko/index.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| [#12: cultural note review checklist](https://github.com/duct-tape2/ai-language-partner/issues/12) | Add a short checklist for reviewing cultural notes without stereotypes or overgeneralization | `docs/community/CONTRIBUTOR_LANDING.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/CONTRIBUTOR_LANDING.md) |
| [#16: mock mode indicators](https://github.com/duct-tape2/ai-language-partner/issues/16) | Document how fixture-backed mock mode differs from live API-backed mode | `docs/ARCHITECTURE.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ARCHITECTURE.md) |
| [#18: Korean UI string consistency](https://github.com/duct-tape2/ai-language-partner/issues/18) | Review Korean labels and suggest consistent wording | `apps/mobile/src/i18n.ts` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/i18n.ts) |
| [#19: provider-status example response](https://github.com/duct-tape2/ai-language-partner/issues/19) | Add example `/v1/providers/status` responses for mock, fallback, and local engine modes | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#20: dialogue match threshold explanation](https://github.com/duct-tape2/ai-language-partner/issues/20) | Explain match, confirm, and fallback thresholds in learner-friendly language | `docs/ARCHITECTURE.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ARCHITECTURE.md) |
| [#23: Redis rate-limit optional setup](https://github.com/duct-tape2/ai-language-partner/issues/23) | Document optional Redis rate-limit setup for local and production use without exposing secrets | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#24: OpenAPI examples for auth device trust](https://github.com/duct-tape2/ai-language-partner/issues/24) | Add or improve OpenAPI examples for self-attested and public-key device trust flows | `contracts/openapi_v0.yaml` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/contracts/openapi_v0.yaml) |
| [#29: issue-label taxonomy document](https://github.com/duct-tape2/ai-language-partner/issues/29) | Clarify when to use each public issue label | `docs/community/LABELS.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/LABELS.md) |
| [#31: no-runtime-LLM FAQ](https://github.com/duct-tape2/ai-language-partner/issues/31) | Add a short FAQ answer explaining the local-first dialogue-bank design | `docs/index.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/index.md) |
| [#34: Korean backend dependency troubleshooting](https://github.com/duct-tape2/ai-language-partner/issues/34) | Add Korean troubleshooting notes for Python dependency install failures | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#35: Japanese no-runtime-LLM design explanation](https://github.com/duct-tape2/ai-language-partner/issues/35) | Add neutral Japanese explanation of cost, privacy, latency, and quality-control tradeoffs | `docs/ja/index.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ja/index.md) |
| [#36: restaurant preference examples](https://github.com/duct-tape2/ai-language-partner/issues/36) | Add beginner-safe examples for expressing restaurant preferences | `packs/yui/v1/variants.csv` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) |
| [#41: provider fallback labels](https://github.com/duct-tape2/ai-language-partner/issues/41) | Explain honest provider labels such as `mock` and `voicevox_compat_fallback_*` | `docs/backend/API_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| [#44: first PR walkthrough](https://github.com/duct-tape2/ai-language-partner/issues/44) | Improve this repo's first-PR instructions for new contributors | `docs/community/FIRST_PR_WALKTHROUGH.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/FIRST_PR_WALKTHROUGH.md) |
| [#45: maintainer review checklist](https://github.com/duct-tape2/ai-language-partner/issues/45) | Improve the checklist maintainers use before merging counted external PRs | `docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md) |
| [#46: Korean notes for sentence-final particles](https://github.com/duct-tape2/ai-language-partner/issues/46) | Add beginner-safe Korean explanations for よ, ね, よね, and かな | `docs/ko/index.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| [#47: cultural-safety review examples](https://github.com/duct-tape2/ai-language-partner/issues/47) | Add examples of stereotype-prone or context-sensitive wording to review carefully | `apps/mobile/src/culture/cultureNotes.ts` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/culture/cultureNotes.ts) |
| [#50: dialogue-bank pack roadmap](https://github.com/duct-tape2/ai-language-partner/issues/50) | Add a public roadmap for persona, topic, JLPT, and language-review pack areas | `docs/community/CONTRIBUTOR_GROWTH_PLAN.md` | [edit](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/CONTRIBUTOR_GROWTH_PLAN.md) |

## Review Notes

- Keep changes small and issue-linked.
- Do not add `.wav`, `.zip`, `.npy`, `.sqlite`, screenshots, local engines, or
  private files.
- Avoid generated text dumps. Human language review and clear docs are the
  point of this lane.
- If a file looks too technical, ask in the
  [First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53).
