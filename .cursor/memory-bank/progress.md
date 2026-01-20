# progress.md

## 현재 상태
- Custom API(FastAPI)에서 provider 기반 `/v1/chat/completions` 엔드포인트가 존재.
- `CodexProvider`의 타임아웃/요청취소 시 고아 subprocess 가능성을 차단하는 수정이 반영됨.

## 남은 작업(우선순위)
- 다른 CLI provider들도 타임아웃 시 subprocess를 정리하도록 통일(원인 동일).
- 운영 시나리오에서 타임아웃 정책 정리(서버 timeout vs 클라이언트 timeout vs reverse proxy).

## 알려진 이슈/메모
- 타임아웃이 “에러”가 아니라 “처리 중단 + 백그라운드 계속 실행”처럼 보일 수 있으므로, 타임아웃 시 반드시 프로세스 종료가 필요.

