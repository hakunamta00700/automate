"""Markdown 업로드 기능 예시"""

import re

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger

from ..tasks.upload_markdown import generate_post_from_airtable


async def get_method(request: Request):
    """GET 메서드 핸들러 예시

    Args:
        request: FastAPI Request 객체

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


async def post_method(request: Request):
    """POST /v1/func/upload_markdown

    - `from=airtable|googlesp` (쿼리 또는 JSON)
    - JSON body의 `data.row_id`(또는 `row_id`)를 사용
    - 현재는 `from=airtable`만 구현: `mdb generate_post_from_airtable --row_id <row_id>` 실행

    Args:
        request: FastAPI Request 객체

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

    # Huey 큐에 작업 enqueue (즉시 반환)
    result_handle = generate_post_from_airtable(row_id=row_id, use_codex=True)
    raw_task_id = getattr(result_handle, "id", None)
    task_id = str(raw_task_id) if raw_task_id is not None else None

    return JSONResponse(
        status_code=202,
        content={
            "ok": True,
            "from": source,
            "row_id": row_id,
            "task_id": task_id,
        },
    )
