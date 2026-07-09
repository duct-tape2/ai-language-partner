---
layout: page
title: 한국어 기여자 안내
---

# AI Language Partner에 첫 PR 보내기

`ai-language-partner`는 한국어권 일본어 학습자를 위한 local-first 일본어
회화 연습 앱입니다. Expo 모바일 앱, FastAPI 백엔드, 사전 검수된 dialogue
bank, 로컬 STT/TTS 흐름을 사용합니다.

Daily Talk의 핵심 대화 흐름은 런타임 LLM 호출에 의존하지 않습니다. 학습자
음성을 로컬로 인식하고, 검수된 dialogue-bank 문장과 매칭한 뒤, 로컬 TTS
또는 사전 준비된 음성 자산으로 응답하는 구조입니다.

## 처음 기여하기

로컬 음성 엔진, 생성 음성, private data, API key가 없어도 의미 있는 첫 PR을
보낼 수 있습니다.

시작 링크:

- [5분 첫 PR 가이드](../community/FIVE_MINUTE_FIRST_PR.md)
- [starter issue index](../community/STARTER_ISSUE_INDEX.md)
- [no-install first PR board](../community/NO_INSTALL_FIRST_PRS.md)
- [contributor landing](../community/CONTRIBUTOR_LANDING.md)
- [first PR walkthrough](../community/FIRST_PR_WALKTHROUGH.md)
- [installable demo release plan](../community/INSTALLABLE_DEMO_RELEASE_PLAN.md)
- [첫 PR help desk discussion](https://github.com/duct-tape2/ai-language-partner/discussions/53)
- [contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml)

## 추천 기여 분야

| 분야 | 좋은 첫 PR 예시 |
|---|---|
| 한국어 문서 | 설치 설명, 오류 해결 노트, 학습자용 설명 개선 |
| 일본어 자연스러움 검수 | 초급자에게 안전한 표현, 어조 일관성, 문화적 안전성 검수 |
| dialogue content | `story.json` 또는 `variants.csv`의 문장/번역 검수 |
| 모바일 접근성 | accessibility label, 터치 영역, 대비, 작은 화면 레이아웃 |
| FastAPI/OpenAPI 문서 | curl 예시, provider-status 설명, 로컬 STT/TTS 설정 노트 |
| 테스트/도구 | 작은 fixture test, repo check, CI에서 돌 수 있는 검증 스크립트 |

## Claude for OSS 기준

이 repo는 Claude for OSS의 community-builder route를 목표로 합니다:
최근 12개월 안에 20명 이상의 unique external contributors가 useful merged PR을
가진 repo가 되는 것입니다.

중요한 원칙:

- 실제 외부 기여자의 유용한 merged PR만 count합니다.
- maintainer가 만든 PR, bot, 중복 계정, 숫자를 채우기 위한 무의미한 PR은
  count하지 않습니다.
- docs-only PR도 실제 사용자/기여자 경험을 개선하면 환영합니다.

관련 문서:

- [Claude for OSS application evidence](../CLAUDE_FOR_OSS_APPLICATION.md)
- [PR review and counting policy](../community/PR_REVIEW_AND_COUNTING_POLICY.md)
- [20 contributor sprint](../community/CONTRIBUTOR_SPRINT.md)

## 무엇을 커밋하면 안 되나요?

다음은 Git에 넣지 마세요:

- 생성된 `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot 파일
- 로컬 speech engine 폴더
- private notes, handoff 파일, 개인 경로
- token, API key, secret, private dataset

공개 repo는 source-only로 유지합니다.
