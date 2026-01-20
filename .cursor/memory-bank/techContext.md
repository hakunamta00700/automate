# techContext.md

## 기술 스택
- **Python**: 3.12+
- **서버**: FastAPI 기반 Custom API (`src/automate/custom_api/`)
- **CLI/프로세스 실행**: `asyncio.create_subprocess_exec`
- **로깅**: `loguru`
- **패키지 관리**: `uv` (`uv.lock` 존재)

## 개발/운영 유의사항
- Windows 환경(경로/인자 quoting)에 주의: 외부 CLI 실행 시 “문자열 커맨드 -> split”보다 “args 리스트”가 안전하다.
- 비밀값은 `.env`에서 관리하고 저장소에 커밋하지 않는다.

