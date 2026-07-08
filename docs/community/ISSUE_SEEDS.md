# Issue Seeds

Create these as GitHub issues after the repository is public. Keep each issue
small enough for one contributor to finish without needing private context.

## Docs and Setup

1. `docs: add Korean quick-start for backend mock mode`
   Labels: `good first issue`, `docs`, `help wanted`
   Acceptance: backend setup works without STT/TTS engines; Korean instructions
   include Python venv, install, run, and health check.

2. `docs: add Japanese quick-start for mobile mock mode`
   Labels: `good first issue`, `docs`, `help wanted`
   Acceptance: mobile setup covers npm install, Expo web, and mock API defaults.

3. `docs: clarify local whisper.cpp setup on macOS`
   Labels: `docs`, `stt`, `help wanted`
   Acceptance: explains ffmpeg, model path, env vars, and fallback behavior.

4. `docs: clarify AivisSpeech and VOICEVOX-compatible setup`
   Labels: `docs`, `tts`, `help wanted`
   Acceptance: explains separate-process licensing and `/speakers` probe.

5. `docs: add architecture glossary for dialogue-bank terms`
   Labels: `good first issue`, `docs`
   Acceptance: defines persona, pack, node, lineId, variants, match, confirm,
   fallback, and global intent.

6. `docs: add API curl examples for Daily Talk endpoints`
   Labels: `docs`, `backend`, `help wanted`
   Acceptance: examples cover packs, match, unmatched, voices, and provider
   status.

## Korean/Japanese Content Review

7. `content: review yui v1 beginner dialogue Korean translations`
   Labels: `content`, `language-review`, `good first issue`
   Acceptance: PR fixes unnatural Korean explanations without changing line IDs.

8. `content: review yui v1 Japanese naturalness`
   Labels: `content`, `language-review`, `help wanted`
   Acceptance: PR improves Japanese dialogue while preserving beginner level.

9. `content: review haruka v1 polite-tone consistency`
   Labels: `content`, `language-review`
   Acceptance: confirms or fixes tone drift across assistant lines.

10. `content: review ren v1 casual-tone consistency`
    Labels: `content`, `language-review`
    Acceptance: confirms or fixes casual Japanese wording and Korean notes.

11. `content: add notes for Korean learners on particle mistakes`
    Labels: `content`, `docs`, `good first issue`
    Acceptance: adds concise examples for は/が, を/に, and で/に.

12. `content: add beginner-safe cultural note review checklist`
    Labels: `content`, `docs`
    Acceptance: checklist avoids stereotypes and flags context-sensitive terms.

## Accessibility and Mobile UX

13. `mobile: audit touch target sizes in bottom tabs`
    Labels: `mobile`, `accessibility`, `good first issue`
    Acceptance: identifies and fixes any tab target below common mobile guidance.

14. `mobile: add accessibility labels to voice preview controls`
    Labels: `mobile`, `accessibility`
    Acceptance: voice buttons have useful screen-reader labels.

15. `mobile: improve empty state copy for Daily Talk pack loading`
    Labels: `mobile`, `good first issue`
    Acceptance: no technical jargon; tells learner what to do next.

16. `mobile: document mock mode indicators`
    Labels: `mobile`, `docs`
    Acceptance: explains when UI is fixture-backed versus live API-backed.

17. `mobile: add regression check for duplicate screen labels`
    Labels: `mobile`, `tests`, `help wanted`
    Acceptance: script fails when two screen registry labels collide.

18. `mobile: review Korean UI strings for consistency`
    Labels: `mobile`, `language-review`, `good first issue`
    Acceptance: consistent honorifics and app terminology.

## Backend and API

19. `backend: add provider-status example response to docs`
    Labels: `backend`, `docs`, `good first issue`
    Acceptance: includes mock, fallback, and local engine examples.

20. `backend: add dialogue match threshold explanation`
    Labels: `backend`, `docs`
    Acceptance: explains match/confirm/fallback thresholds in learner terms.

21. `backend: add tests for malformed dialogue pack metadata`
    Labels: `backend`, `tests`, `help wanted`
    Acceptance: invalid manifest JSON does not crash pack listing.

22. `backend: add tests for path traversal rejection on pack zip route`
    Labels: `backend`, `tests`, `good first issue`
    Acceptance: `..` and slash injection return 400/404 safely.

23. `backend: document Redis rate-limit optional setup`
    Labels: `backend`, `docs`
    Acceptance: covers local dev, production env var, and secret redaction.

24. `backend: add OpenAPI examples for auth device trust`
    Labels: `backend`, `docs`
    Acceptance: examples cover self-attested and public-key modes.

## Tests and Tooling

25. `tests: add public tree forbidden-file scan`
    Labels: `tests`, `good first issue`
    Acceptance: CI fails if generated engines, databases, zip, wav, or npy files
    are committed.

26. `tests: add README command smoke script`
    Labels: `tests`, `docs`
    Acceptance: validates documented backend commands remain current.

27. `tests: add mobile package script inventory check`
    Labels: `tests`, `mobile`
    Acceptance: fails if README references missing npm scripts.

28. `tests: add pack source schema check`
    Labels: `tests`, `backend`, `help wanted`
    Acceptance: validates `story.json`, `manifest.json`, and `variants.csv`.

29. `chore: add issue-label taxonomy document`
    Labels: `docs`, `community`, `good first issue`
    Acceptance: documents labels and when maintainers apply them.

30. `chore: add release checklist for generated voice assets`
    Labels: `docs`, `release`
    Acceptance: checklist separates source release from generated asset release.

31. `docs: add FAQ about why no runtime LLM is used`
    Labels: `docs`, `good first issue`
    Acceptance: explains cost, latency, privacy, and quality-control tradeoffs.

32. `docs: add comparison table for dialogue bank versus chatbot tutor`
    Labels: `docs`, `help wanted`
    Acceptance: neutral comparison; no vendor attacks or unsupported claims.

33. `mobile: plan Expo SDK upgrade for transitive security advisories`
    Labels: `mobile`, `security`, `help wanted`
    Acceptance: documents current `npm audit` advisories, proposes a target Expo
    SDK upgrade path, and lists compatibility checks required before any forced
    dependency upgrade is merged.

34. `docs: add Korean troubleshooting notes for backend dependency install`
    Labels: `docs`, `backend`, `good first issue`
    Acceptance: covers common Python venv, pip, and macOS command-line tools
    failures without assuming private maintainer context.

35. `docs: add Japanese explanation of the no-runtime-LLM design`
    Labels: `docs`, `language-review`, `help wanted`
    Acceptance: Japanese text explains cost, privacy, latency, and quality
    control tradeoffs neutrally.

36. `content: add beginner examples for giving restaurant preferences`
    Labels: `content`, `language-review`, `good first issue`
    Acceptance: adds beginner-safe Japanese examples with Korean notes and does
    not introduce generated audio or binary assets.

37. `content: review honorific consistency in onboarding examples`
    Labels: `content`, `language-review`
    Acceptance: flags or fixes mismatched speech levels and explains the choice
    in the PR summary.

38. `mobile: add accessibility label audit for Daily Talk controls`
    Labels: `mobile`, `accessibility`, `help wanted`
    Acceptance: record, stop, replay, hint, and suggested-reply controls expose
    useful labels for screen-reader users.

39. `mobile: improve small-screen layout for Voice Gallery cards`
    Labels: `mobile`, `accessibility`
    Acceptance: verifies long Korean/Japanese voice names do not overlap or
    overflow on narrow mobile widths.

40. `backend: add OpenAPI example for dialogue pack listing`
    Labels: `backend`, `docs`, `good first issue`
    Acceptance: `contracts/openapi_v0.yaml` includes a realistic response
    example for `GET /v1/dialogue/packs`.

41. `backend: document provider fallback labels`
    Labels: `backend`, `docs`
    Acceptance: explains `mock`, `whisper_cpp_fallback_mock`,
    `voicevox_compat_fallback_*`, and why honest provider labels matter.

42. `tests: add script check that issue seed count stays above 30`
    Labels: `tests`, `community`, `good first issue`
    Acceptance: CI or a repo script fails if `docs/community/ISSUE_SEEDS.md`
    parses fewer than 30 issues.

43. `tests: add contributor evidence script fixture test`
    Labels: `tests`, `community`
    Acceptance: tests contributor de-duplication, maintainer exclusion, and bot
    exclusion without calling the GitHub API.

44. `docs: improve first PR walkthrough`
    Labels: `docs`, `community`, `good first issue`
    Acceptance: improves `docs/community/FIRST_PR_WALKTHROUGH.md` with clearer
    first-time contributor steps or localized Korean/Japanese notes.

45. `docs: add maintainer review checklist`
    Labels: `docs`, `community`
    Acceptance: summarizes useful-review requirements before merging counted
    external PRs.

46. `content: add Korean notes for Japanese sentence-final particles`
    Labels: `content`, `language-review`
    Acceptance: covers よ, ね, よね, かな at a beginner-safe level with Korean
    explanations.

47. `content: add cultural-safety review examples`
    Labels: `content`, `docs`
    Acceptance: includes examples of stereotypes to avoid and context-sensitive
    wording to review carefully.

48. `mobile: add regression guard for missing accessibility labels`
    Labels: `mobile`, `tests`, `accessibility`
    Acceptance: extends frontend regression checks to catch unlabeled key
    controls where practical.

49. `backend: add malformed multipart upload test for STT endpoint`
    Labels: `backend`, `tests`
    Acceptance: malformed or missing audio upload returns a clear 4xx response
    without leaking tracebacks.

50. `docs: add public roadmap for dialogue-bank packs`
    Labels: `docs`, `community`, `help wanted`
    Acceptance: lists planned persona/topic/JLPT pack areas and names which
    items are suitable for external language review.
