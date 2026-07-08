# UI Spec — Screen by Screen

## HomeTodayScreen

목표: 앱을 켜자마자 “오늘 뭐 하지?”를 없앤다.

필수 요소:
- 상단: `오늘의 3분 일본어`
- streak 표시
- 오늘의 미션 카드: `오늘 너무 피곤했어`
- 주요 CTA: `유이랑 연습하기`
- 보조 카드: `어제 복습`, `페르소나 선택`

## PersonaSelectScreen

필수 요소:
- 유이, 하루카, 렌 카드
- 역할/목소리/설명 스타일 표시
- 선택 시 selectedPersonaId 저장

## PracticeRoomScreen

필수 요소:
- 한국어 표현
- 일본어 표현
- 대안 표현
- 유이의 opening message
- `듣기` 버튼
- `따라 말하기` 버튼
- `대화 시작` 버튼

## VoicePracticeScreen

필수 요소:
- conversation bubble
- TTS 재생 버튼
- 녹음/따라 말하기 버튼
- mock STT 결과 표시
- 교정 카드
- 복습 카드 생성 버튼

## ReviewCardsScreen

필수 요소:
- front/back 카드
- tags
- 다시 듣기
- 오늘 저장한 카드 수

## ProgressScreen

필수 요소:
- streak
- spoken sentence count
- review card count
- weekly growth card placeholder

## SettingsScreen

필수 요소:
- API mode mock/real 표시
- API base URL 표시
- backend health check 버튼
- entitlement 표시
