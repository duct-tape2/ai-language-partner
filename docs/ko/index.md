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

- [브라우저에서 데모 보기](../demo/)
- [한국어 기여자 모집](../community/CALL_FOR_CONTRIBUTORS_KO.html)
- [한국어 5분 첫 PR 가이드](../community/FIVE_MINUTE_FIRST_PR_KO.html)
- [Language review first PR kit](../community/LANGUAGE_REVIEW_FIRST_PR_KIT.html)
- [5분 첫 PR 가이드](../community/FIVE_MINUTE_FIRST_PR.html)
- [현재 가능한 starter issue 목록 - 예약/할당 이슈 제외](../community/STARTER_ISSUE_INDEX.html)
- [브라우저 편집 후보 목록 - 시작 전 현재 목록 확인](../community/NO_INSTALL_FIRST_PRS.html)
- [contributor landing](../community/CONTRIBUTOR_LANDING.html)
- [first PR walkthrough](../community/FIRST_PR_WALKTHROUGH.html)
- [installable demo release plan](../community/INSTALLABLE_DEMO_RELEASE_PLAN.html)
- [첫 PR help desk discussion](https://github.com/duct-tape2/ai-language-partner/discussions/53)
- [한국어 contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ko.yml)

## 추천 기여 분야

| 분야 | 좋은 첫 PR 예시 |
|---|---|
| 한국어 문서 | 설치 설명, 오류 해결 노트, 학습자용 설명 개선 |
| 일본어 자연스러움 검수 | 초급자에게 안전한 표현, 어조 일관성, 문화적 안전성 검수 |
| dialogue content | `story.json` 또는 `variants.csv`의 문장/번역 검수 |
| 모바일 접근성 | accessibility label, 터치 영역, 대비, 작은 화면 레이아웃 |
| FastAPI/OpenAPI 문서 | curl 예시, provider-status 설명, 로컬 STT/TTS 설정 노트 |
| 테스트/도구 | 작은 fixture test, repo check, CI에서 돌 수 있는 검증 스크립트 |

## 도움이 되는 첫 기여

학습자의 일본어 연습을 더 명확하고 안전하며 접근하기 쉽게 만들거나, 프로젝트를 더
쉽게 유지할 수 있게 하는 개선을 환영합니다. docs-only PR도 실제 학습자나 기여자의
경험을 좋게 만든다면 가치가 있습니다.

하나의 issue나 문제에 집중하고 PR 본문에서 링크해 주세요. 실행한 최소한의 check도
적으면 maintainer가 더 쉽게 리뷰할 수 있습니다.

## 무엇을 커밋하면 안 되나요?

다음은 Git에 넣지 마세요:

- 생성된 `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot 파일
- 로컬 speech engine 폴더
- private notes, handoff 파일, 개인 경로
- token, API key, secret, private dataset

공개 repo는 source-only로 유지합니다.
