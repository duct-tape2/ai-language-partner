# API Contract Notes

Claude와 Codex는 `openapi_v0.yaml`을 단일 진실 공급원으로 사용한다.

## 중요한 명명 고정

```text
practiceRoomId = tired_today
personaId = yui
conversation turn endpoint = POST /v1/conversations/{conversationId}/turns
TTS endpoint = POST /v1/tts/synthesize
progress endpoint = GET /v1/progress/today
```

## 프론트 fallback 규칙

Backend가 아직 없으면 Claude는 `packages/shared/src/fixtures.ts`의 mock 데이터를 사용한다.  
그러나 화면과 API client 함수명은 실제 backend 계약과 동일해야 한다.

## 백엔드 fallback 규칙

실제 LLM/TTS/STT API 키가 없으면 Codex는 mock provider를 반환한다.  
그러나 response shape는 반드시 OpenAPI와 동일해야 한다.
