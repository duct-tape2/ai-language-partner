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

| 내가 할 수 있는 것 | 이슈 | 바로 수정 |
|---|---|---|
| 한국어 backend setup 설명 개선 | [#1](https://github.com/duct-tape2/ai-language-partner/issues/1) | [API runbook 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 한국어 학습자 노트 추가 | [#11](https://github.com/duct-tape2/ai-language-partner/issues/11) | [한국어 guide 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| 한국어 UI 문구 일관성 검수 | [#18](https://github.com/duct-tape2/ai-language-partner/issues/18) | [i18n 파일 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/i18n.ts) |
| 한국어 dependency troubleshooting 추가 | [#34](https://github.com/duct-tape2/ai-language-partner/issues/34) | [API runbook 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/backend/API_RUNBOOK.md) |
| 일본어 종조사 한국어 설명 추가 | [#46](https://github.com/duct-tape2/ai-language-partner/issues/46) | [한국어 guide 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ko/index.md) |
| 일본어 자연스러움 검수 | [#8](https://github.com/duct-tape2/ai-language-partner/issues/8) | [story source 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| 식당 취향 예문 보강 | [#36](https://github.com/duct-tape2/ai-language-partner/issues/36) | [variants CSV 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) |
| 첫 PR 안내문 개선 | [#44](https://github.com/duct-tape2/ai-language-partner/issues/44) | [walkthrough 편집](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/community/FIRST_PR_WALKTHROUGH.md) |

더 많은 선택지는 [설치 없이 가능한 첫 PR 목록](NO_INSTALL_FIRST_PRS.md)에
있습니다.

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
- JSON/CSV/YAML을 수정할 때는 기존 구조와 ID를 유지합니다.
- 무엇을 고를지 모르겠으면
  [첫 PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53)
  또는
  [contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml)을
  사용하세요.
