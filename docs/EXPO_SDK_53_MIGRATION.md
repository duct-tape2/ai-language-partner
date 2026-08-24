# Expo SDK 53 migration record

This record documents the incremental upgrade for [issue #63](https://github.com/duct-tape2/ai-language-partner/issues/63).
It is intentionally limited to Expo SDK 52 → 53; it does not attempt a
multi-SDK migration or a forced dependency audit fix.

## Version and API changes

The mobile app now uses:

- Expo SDK 53.0.27
- React Native 0.79.6
- React 19.0.0
- TypeScript 5.8.3
- `expo-audio` 0.4.9 for recording and playback
- `expo-speech` for device text-to-speech fallback

The former `expo-av` recording and playback calls were migrated to the
`expo-audio` recorder/player APIs. The Expo config plugin now declares the
microphone permission, and TypeScript uses Expo 53's bundler module resolution.
Mock mode and the hosted web export remain unchanged in scope.

## Verification evidence

Run from `apps/mobile` on 2026-08-19:

| Command | Result |
| --- | --- |
| `npm run verify` | Passed: typecheck, frontend regression guards, and README script tests |
| `npx expo install --check` | Passed: dependencies are up to date |
| `npx expo-doctor` | Passed: 18/18 checks |
| `npx expo export --platform web` | Passed: web bundle exported to `dist` |

## Audit boundary

Issue #63 reports the SDK 52 baseline audit as 12 high and 5 moderate
transitive advisories from 2026-07-10. The post-migration command
`npm audit --omit=dev` reports 13 findings: 3 moderate, 9 high, and 1
critical. The findings are retained below rather than hidden or changed with
`npm audit fix --force`.

| Audit path | Reachability classification | Follow-up |
| --- | --- | --- |
| `@expo/cli`, `@expo/metro-config`, `metro`, `metro-config`, `metro-transform-worker`, `image-size`, `postcss`, and `tar` | Build/development tooling used by Expo CLI and Metro. These packages are not imported by the app source or included as application modules in the exported web bundle. | Re-audit with the next supported Expo SDK upgrade; do not force a cross-SDK downgrade or upgrade as part of this change. |
| `@react-native/community-cli-plugin` and its `react-native` dependency path | Native build integration/toolchain path reported by npm audit, not an application-level call site. A native device build is still required for final packaging evidence. | Re-audit with the next supported React Native/Expo release and add native build evidence before release. |

The audit result is therefore a documented residual for the SDK 53 step, not a
claim that all future native or build-time risk is resolved. No production
release is implied by this migration branch.

The advisory identifiers returned by npm for the residual paths were:

- `brace-expansion`: [GHSA-3jxr-9vmj-r5cp](https://github.com/advisories/GHSA-3jxr-9vmj-r5cp), [GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg), and [GHSA-rgw5-rvv9-x895](https://github.com/advisories/GHSA-rgw5-rvv9-x895).
- `image-size`: [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) and [GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq).
- `js-yaml`: [GHSA-5p4m-2wfm-xmqj](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj).
- `postcss`: [GHSA-6g55-p6wh-862q](https://github.com/advisories/GHSA-6g55-p6wh-862q), [GHSA-fxqj-rqcc-2cmp](https://github.com/advisories/GHSA-fxqj-rqcc-2cmp), and [GHSA-r28c-9q8g-f849](https://github.com/advisories/GHSA-r28c-9q8g-f849).
- `tar`: [GHSA-w8wr-v893-vjvp](https://github.com/advisories/GHSA-w8wr-v893-vjvp), [GHSA-23hp-3jrh-7fpw](https://github.com/advisories/GHSA-23hp-3jrh-7fpw), [GHSA-8x88-c5mf-7j5w](https://github.com/advisories/GHSA-8x88-c5mf-7j5w), [GHSA-gvwx-54wh-qm9j](https://github.com/advisories/GHSA-gvwx-54wh-qm9j), and [GHSA-r292-9mhp-454m](https://github.com/advisories/GHSA-r292-9mhp-454m).
