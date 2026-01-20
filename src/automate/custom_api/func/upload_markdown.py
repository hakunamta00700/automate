"""Markdown 업로드 기능 예시"""

import asyncio
import re

from fastapi import HTTPException, Request
from loguru import logger

from ..config import get_custom_api_settings


async def get_method(request: Request, *args, **kwargs):
    """GET 메서드 핸들러 예시

    Args:
        request: FastAPI Request 객체
        *args: 추가 위치 인자
        **kwargs: 추가 키워드 인자

    Returns:
        응답 데이터
    """
    logger.info("GET /v1/func/upload_markdown 호출됨")
    return {
        "message": "Markdown 업로드 GET 엔드포인트",
        "method": "GET",
        "path": str(request.url.path),
    }


def _get_content_type(request: Request) -> str:
    """요청의 Content-Type을 반환합니다."""
    return (request.headers.get("content-type") or "").lower()


async def _try_parse_json(request: Request) -> dict | None:
    """JSON body를 파싱합니다. JSON이 아니거나 파싱 실패 시 None을 반환합니다."""
    if not _get_content_type(request).startswith("application/json"):
        return None

    try:
        body = await request.json()
    except Exception as e:
        logger.warning(f"JSON 파싱 실패: {e}")
        return None

    if not isinstance(body, dict):
        return None
    return body


def _extract_source(request: Request, body: dict | None) -> str | None:
    """source(from) 값을 쿼리 또는 JSON에서 추출합니다."""
    source = request.query_params.get("from")
    if source:
        return source
    if body and isinstance(body.get("from"), str):
        return body["from"]
    return None


def _extract_row_id(body: dict | None) -> str | None:
    """요청 JSON에서 row_id를 추출합니다.

    기대하는 형태(유연하게 지원):
    - {"row_id": "..."}
    - {"data": {"row_id": "..."}}
    """
    if not body:
        return None

    if isinstance(body.get("row_id"), str):
        return body["row_id"]

    data = body.get("data")
    if isinstance(data, dict) and isinstance(data.get("row_id"), str):
        return data["row_id"]

    return None


def _validate_row_id(row_id: str) -> None:
    """row_id를 검증합니다(명령 인자 주입 방지용)."""
    # Airtable record id 예: recXXXXXXXXXXXXXXX (대개 영숫자)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", row_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 row_id 형식입니다.")


async def _run_command(args: list[str], timeout: int) -> dict:
    """외부 명령을 비동기로 실행하고 stdout/stderr/exit code를 반환합니다.

    타임아웃/요청 취소 시에도 subprocess가 남지 않도록 정리합니다.
    """
    process: asyncio.subprocess.Process | None = None
    try:
        logger.info(f"명령 실행: {' '.join(args)}")
        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        stdout_text = stdout.decode("utf-8", errors="ignore") if stdout else ""
        stderr_text = stderr.decode("utf-8", errors="ignore") if stderr else ""

        return {
            "returncode": process.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
        }
    except TimeoutError as err:
        logger.error(f"명령 실행 타임아웃 ({timeout}초)")
        raise HTTPException(status_code=504, detail=f"명령 실행 타임아웃 ({timeout}초)") from err
    except asyncio.CancelledError:
        logger.warning("요청 취소됨: subprocess 정리 진행")
        raise
    except FileNotFoundError as err:
        logger.error(f"명령 실행 실패: 실행 파일을 찾을 수 없습니다. args={args}")
        raise HTTPException(
            status_code=500,
            detail="서버에서 mdb 실행 파일을 찾을 수 없습니다(PATH 또는 설치 상태 확인 필요).",
        ) from err
    except Exception as err:
        logger.exception(f"명령 실행 중 오류: {err}")
        raise HTTPException(status_code=500, detail=f"명령 실행 중 오류: {err}") from err
    finally:
        # 타임아웃/취소/예외 시에도 고아 프로세스 방지
        if process and process.returncode is None:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=3)
            except Exception:
                try:
                    process.kill()
                    await asyncio.wait_for(process.wait(), timeout=3)
                except Exception as e:
                    logger.warning(f"subprocess 정리 실패: {e}")


async def post_method(request: Request, *args, **kwargs):
    """POST /v1/func/upload_markdown

    - `from=airtable|googlesp` (쿼리 또는 JSON)
    - JSON body의 `data.row_id`(또는 `row_id`)를 사용
    - 현재는 `from=airtable`만 구현: `mdb generate_post_from_airtable --row_id <row_id>` 실행

    Args:
        request: FastAPI Request 객체
        *args: 추가 위치 인자
        **kwargs: 추가 키워드 인자

    Returns:
        응답 데이터
    """
    logger.info("POST /v1/func/upload_markdown 호출됨")
    body = await _try_parse_json(request)
    source = _extract_source(request, body)

    if source not in {"airtable", "googlesp"}:
        raise HTTPException(
            status_code=400,
            detail="from 파라미터는 'airtable' 또는 'googlesp'만 지원합니다.",
        )

    if source == "googlesp":
        raise HTTPException(status_code=501, detail="from=googlesp는 아직 미구현입니다.")

    # source == "airtable"
    row_id = _extract_row_id(body)
    if not row_id:
        raise HTTPException(status_code=400, detail="요청 JSON에 row_id가 필요합니다.")
    _validate_row_id(row_id)

    settings = get_custom_api_settings()
    timeout = settings.COMMAND_TIMEOUT
    args = ["mdb", "generate_post_from_airtable", "--row_id", row_id, "--codex"]

    result = await _run_command(args=args, timeout=timeout)
    ok = result["returncode"] == 0

    return {
        "ok": ok,
        "from": source,
        "row_id": row_id,
        "command": " ".join(args),
        "timeout_seconds": timeout,
        **result,
    }
