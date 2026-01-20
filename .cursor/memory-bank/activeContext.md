# activeContext.md

## 현재 작업 포커스
- `CodexProvider.chat_completion()`에서 subprocess 타임아웃이 나도 codex 실행이 “뒤에서 계속 도는” 현상(고아 프로세스)을 해결.

## 최근 변경(2026-01-20)
- `src/automate/custom_api/providers/codex.py`
  - timeout 또는 요청 취소 시 `terminate/kill`로 subprocess 정리 추가
  - Windows quoting 이슈를 줄이기 위해 “문자열 command 생성 후 split” 대신 “args 리스트”로 실행
  - stdin을 `DEVNULL`로 설정해 interactive 입력 대기 가능성을 차단

## 다음 단계(후보)
- 동일 패턴을 쓰는 다른 provider(`cursor`, `opencode`, `gemini` CLI 경로)도 타임아웃 시 subprocess 정리 로직을 적용해 일관성 확보.
- timeout 값(`CUSTOM_API_TIMEOUT`)과 클라이언트/프록시 타임아웃을 맞춰 운영 이슈 예방.

