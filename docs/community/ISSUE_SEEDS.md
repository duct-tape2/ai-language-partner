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
