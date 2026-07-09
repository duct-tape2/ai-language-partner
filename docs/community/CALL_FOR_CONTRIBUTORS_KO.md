---
layout: page
title: 한국어 기여자 모집
---

# 한국어 기여자 모집

`ai-language-partner`는 한국어권 일본어 학습자를 위한 local-first 일본어
회화 연습 앱입니다. 지금은 작은 첫 PR을 보내줄 한국어/일본어 리뷰어,
문서 기여자, 모바일 접근성 리뷰어, FastAPI/API 문서 기여자를 찾고
있습니다.

공유 링크:

`https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS_KO.html`

## 먼저 보기

- 웹 데모: `https://duct-tape2.github.io/ai-language-partner/demo/`
- GitHub repo: `https://github.com/duct-tape2/ai-language-partner`
- 첫 PR help desk: `https://github.com/duct-tape2/ai-language-partner/discussions/53`
- 공개 기여자 discussion: `https://github.com/duct-tape2/ai-language-partner/discussions/55`
- 한국어 contributor guide: `https://duct-tape2.github.io/ai-language-partner/ko/`

웹 데모는 mock provider로 동작합니다. 로컬 음성 엔진, 생성 음성 파일,
private data, API key가 없어도 앱의 흐름을 보고 첫 PR을 만들 수 있습니다.

## 좋은 첫 PR

| 내가 도울 수 있는 것 | 시작 이슈 | 좋은 PR 모양 |
|---|---|---|
| 한국어 setup/docs | `https://github.com/duct-tape2/ai-language-partner/issues/1` | backend mock-mode 설명을 더 자연스럽게 정리 |
| 일본어 setup/docs | `https://github.com/duct-tape2/ai-language-partner/issues/2` | mobile mock-mode 설명을 일본어로 보강 |
| 일본어 자연스러움 | `https://github.com/duct-tape2/ai-language-partner/issues/8` | 초급자에게 안전한 대화 표현 검수 |
| 한국어 학습자 노트 | `https://github.com/duct-tape2/ai-language-partner/issues/46` | 종조사/말투 차이를 한국어로 설명 |
| dialogue content | `https://github.com/duct-tape2/ai-language-partner/issues/36` | 식당/취향 대화 예문 보강 |
| API 문서 | `https://github.com/duct-tape2/ai-language-partner/issues/19` | provider-status 응답 예시 추가 |
| community docs | `https://github.com/duct-tape2/ai-language-partner/issues/50` | dialogue-bank roadmap 설명 개선 |

더 고르기 쉬운 링크:

- First issue matcher: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md`
- 한국어 5분 첫 PR: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR_KO.md`
- 5분 첫 PR: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md`
- 설치 없이 가능한 첫 PR 목록: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md`
- Starter issue index: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/STARTER_ISSUE_INDEX.md`

## 진행 방법

1. 이슈 하나를 고릅니다.
2. 중복 작업을 피하고 싶으면 이슈에 `/claim`이라고 댓글을 남깁니다.
3. 한 가지 파일 또는 한 가지 주제에 집중해서 수정합니다.
4. PR 본문에 `Closes #이슈번호`를 넣습니다.
5. 실행한 check를 적거나, 문서/언어 검수만 했다고 명확히 적습니다.

## 지켜야 할 것

다음 파일은 Git에 넣지 마세요:

- 생성된 `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot 파일
- 로컬 speech engine 폴더
- private notes, handoff 파일, 개인 경로
- token, API key, secret, private dataset

Daily Talk 흐름은 런타임 LLM/API 호출에 의존하지 않습니다. 학습자 음성을
로컬로 인식하고, 검수된 dialogue-bank 문장과 매칭한 뒤, local TTS 또는
사전 준비된 음성 자산으로 응답합니다. 기여도 이 local-first 설계를
유지하는 방향이면 좋습니다.

## Claude for OSS 메모

이 repo는 Claude for OSS community-builder route를 목표로 합니다. 기준은
최근 12개월 안에 20명 이상의 unique external contributors가 useful merged
PR을 가진 repo가 되는 것입니다.

실제 외부 기여자의 유용한 merged PR만 count합니다. maintainer PR, bot,
중복 계정, 숫자를 채우기 위한 무의미한 PR은 count하지 않습니다.
