---
layout: page
title: Contributor Share Kit
---

# Contributor Share Kit

Use this when you are inviting a real community that could care about the
project: Korean Japanese learners, Japanese reviewers, Expo/React Native
contributors, FastAPI users, accessibility reviewers, local-first builders, or
education OSS maintainers.

Do not mass-post identical messages. Do not imply that a post, star, comment,
or listing counts as Claude for OSS evidence. Only useful merged PRs from real
external contributors count.

## Core Links

| Need | Link |
|---|---|
| Try the app in a browser | `https://duct-tape2.github.io/ai-language-partner/demo/` |
| Pick by skill/time | `https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html` |
| Browser-only first PR | `https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html` |
| Korean first PR guide | `https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR_KO.html` |
| Japanese first PR guide | `https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR_JA.html` |
| No-install issue board | `https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html` |
| Help desk | `https://github.com/duct-tape2/ai-language-partner/discussions/53` |
| Contributor call | `https://github.com/duct-tape2/ai-language-partner/discussions/55` |

## 30-Second Posts

### Korean

```text
한국어권 일본어 학습자를 위한 local-first OSS에 작은 첫 PR을 도와주실 분을 찾고 있습니다.

브라우저 데모:
https://duct-tape2.github.io/ai-language-partner/demo/

30초 이슈 매처:
https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html

설치 없이 가능한 첫 PR:
https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html

문서, 한국어 설명, 일본어 자연스러움 검수, 접근성, API 예제 모두 환영합니다. 생성 음성, private data, API key는 필요 없습니다.
```

### Japanese

```text
韓国語話者向けの日本語学習アプリ OSS で、小さな first PR を募集しています。

ブラウザデモ:
https://duct-tape2.github.io/ai-language-partner/demo/

30秒で issue を選ぶ:
https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html

インストール不要の first PR:
https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html

日本語の自然さ、初級者向け表現、韓国語説明、アクセシビリティ、API docs の改善を歓迎します。生成音声や private data は不要です。
```

### English

```text
I am looking for small first PRs on ai-language-partner, a local-first Japanese speaking practice app for Korean learners.

Try the hosted demo:
https://duct-tape2.github.io/ai-language-partner/demo/

Pick an issue in 30 seconds:
https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html

No-install first PR board:
https://duct-tape2.github.io/ai-language-partner/community/NO_INSTALL_FIRST_PRS.html

Docs, language review, accessibility, API examples, and focused tests all help. No generated audio, private data, local engines, or API keys are needed.
```

## Direct DM Version

Use this only for people you know or communities where direct collaboration is
normal.

```text
I opened a local-first Japanese learning OSS project and I am trying to make the first contribution path genuinely easy.

Could you take one small issue that fits your skill set?

First issue matcher:
https://duct-tape2.github.io/ai-language-partner/community/FIRST_ISSUE_MATCHER.html

Five-minute first PR:
https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html

If none of the issues fit, ask here and I will suggest one:
https://github.com/duct-tape2/ai-language-partner/discussions/53
```

## Community-Specific Routes

| Community | Lead with | Best link |
|---|---|---|
| Korean Japanese-learning groups | Korean learner notes and docs review | `https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR_KO.html` |
| Japanese reviewers | Naturalness and beginner-safe wording | `https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR_JA.html` |
| Language teachers/tutors | Dialogue-bank examples and cultural-safety review | `https://duct-tape2.github.io/ai-language-partner/community/LANGUAGE_REVIEW_FIRST_PR_KIT.html` |
| Expo/React Native contributors | Mobile accessibility and mock-mode UI polish | `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Aaccessibility` |
| FastAPI/OpenAPI contributors | Local STT/TTS setup notes and API examples | `https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3Abackend+label%3Adocs` |
| Local-first builders | No-runtime-LLM architecture explanation | `https://github.com/duct-tape2/ai-language-partner/issues/31` |

## After Posting

1. Record the public post URL in `docs/community/OUTREACH_QUEUE.json`.
2. Set the item status to `posted`, `responded`, `pr-open`, or
   `merged-counted` only after that state is true.
3. Run:

```bash
python3 scripts/verify_outreach_queue.py
python3 scripts/render_outreach_messages.py
```

4. If someone claims an issue, ask them to comment `/claim` on the issue so the
   repo can add the `claimed` label and keep the maintainer funnel visible.
5. If someone opens a PR, respond within 24 hours when possible and use
   `docs/community/PR_REVIEW_AND_COUNTING_POLICY.md` before counting it.

## Review Promise

When inviting contributors, make the promise concrete:

- clear acceptance criteria
- no private context required
- docs/content/language review valued when it helps learners
- first maintainer response within 24 hours when possible
- no generated audio, private data, local engines, or secrets in PRs
