---
layout: page
title: 5분 첫 PR 가이드
---

# 5분 첫 PR 가이드

이 가이드는 로컬 설치 없이 GitHub 웹 에디터만으로 작은 첫 PR을 보내는
경로입니다. Expo, FastAPI, 로컬 STT/TTS 엔진, 생성 음성 파일, API key가
없어도 가능합니다.

먼저 웹 데모를 보고 앱의 방향을 확인할 수 있습니다:

`https://duct-tape2.github.io/ai-language-partner/demo/`

중복 작업을 피하고 싶으면 이슈에 `/claim`이라고 댓글을 남기세요. 자동
댓글이 첫 PR 체크리스트를 안내하고 maintainer triage용 `claimed` 라벨을
붙입니다.

Claude for OSS 기준에는 실제 외부 기여자의 유용한 merged PR만 count됩니다.
숫자를 채우기 위한 사소한 typo 쪼개기, bot, 중복 계정, maintainer PR은
count하지 않습니다.

## 가장 빠른 선택지

[현재 가능한 starter issue 목록](STARTER_ISSUE_INDEX.html)에서 이슈를 고르세요.
이 목록은 예약되었거나 담당자가 있는 이슈를 제외하므로, 중복 작업을 피할 수
있습니다. 한국어 문서, 일본어 자연스러움, dialogue content, 접근성, API 예시,
테스트 중에서 한 가지를 고르면 됩니다.

브라우저 편집이 가능한 후보의 전체 범위는 [설치 없이 가능한 첫 PR 목록](NO_INSTALL_FIRST_PRS.md)에
있지만, 시작하기 전에는 반드시 현재 가능한 목록을 먼저 확인하세요.
일본어/한국어/문화 메모 검수 범위를 고르기 어렵다면
[Language review first PR kit](LANGUAGE_REVIEW_FIRST_PR_KIT.md)을 보세요.

## PR 제목 예시

- `docs: improve Korean backend mock setup`
- `docs: add Korean learner notes for particles`
- `content: review yui Korean beginner dialogue`
- `docs: improve first PR walkthrough`

## PR 본문 템플릿

```text
Closes #ISSUE_NUMBER

What changed:
- 

Review/check:
- Docs/content/language review only; no local setup required.

Notes:
- I did not add generated audio, archives, SQLite files, screenshots, secrets,
  or local engine files.
```

## PR 보내기 전 체크

- 한 PR은 한 이슈 또는 한 주제에만 집중합니다.
- PR 본문에 `Closes #ISSUE_NUMBER`를 넣습니다.
- `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot, local engine,
  private note, token, API key를 커밋하지 않습니다.
- `story.json` 또는 `variants.csv`를 수정할 때는 기존 구조와 ID를 유지합니다.
  CI가 schema, ID, reference, safety를 자동 검증하므로 로컬 설치는 필요하지 않습니다.
- 무엇을 고를지 모르겠으면
  [첫 PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53)
  또는
  [한국어 contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ko.yml)을
  사용하세요.
