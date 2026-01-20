# systemPatterns.md

## 구조 패턴
- **Provider 패턴**: `BaseProvider`(추상 클래스) + 구현체(`CodexProvider`, `OpenCodeProvider`, `CursorProvider`, `GeminiProvider`, `OpenAIProvider` 등).
- **FastAPI 라우팅**: `/v1/chat/completions`에서 `model`에 따라 provider를 선택해 `chat_completion()` 호출.

## 외부 CLI 호출 패턴(중요)
- `asyncio.create_subprocess_exec()` + `process.communicate()` 형태로 stdout/stderr를 수집한다.
- **타임아웃/요청 취소 시 subprocess 정리(terminate/kill)가 필수**. 정리가 없으면 “API는 timeout인데 CLI는 뒤에서 계속 실행” 문제가 발생한다.

