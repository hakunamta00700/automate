# projectbrief.md

## 프로젝트 개요
`automate`는 로컬/외부 AI 도구와 여러 서비스(예: 요약, Airtable, Telegram 등)를 연결해 자동화 워크플로우를 제공하는 Python 프로젝트입니다.

## 핵심 목표
- CLI 및 FastAPI 서버를 통해 자동화 작업을 실행한다.
- 다양한 AI Provider(OpenAI/Gemini/Codex/OpenCode/Cursor 등)를 동일한 인터페이스로 호출한다.
- 비밀값(API 키/토큰)은 `.env`로 관리하고 저장소에 커밋하지 않는다.

## 범위(현재 파악)
- 소스: `src/automate/`
- Custom API(FastAPI): `src/automate/custom_api/`
- Providers: `src/automate/custom_api/providers/`

## 성공 기준
- `automate serve dev`로 서버가 동작하고 `/v1/chat/completions`에서 provider별 응답이 안정적으로 반환된다.
- provider 실행(외부 CLI 호출)에서 타임아웃/요청취소 시에도 고아 프로세스가 남지 않는다.

