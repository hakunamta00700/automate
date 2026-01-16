"""Markdown 업로드 기능 예시"""

from fastapi import Request
from loguru import logger


async def get_method(request: Request, *args, **kwargs):
    """GET 메서드 핸들러 예시

    Args:
        request: FastAPI Request 객체
        *args: 추가 위치 인자
        **kwargs: 추가 키워드 인자

    Returns:
        응답 데이터
    """
    logger.info(f"GET /v1/func/upload_markdown 호출됨")
    return {
        "message": "Markdown 업로드 GET 엔드포인트",
        "method": "GET",
        "path": str(request.url.path),
    }


async def post_method(request: Request, *args, **kwargs):
    """POST 메서드 핸들러 예시

    Args:
        request: FastAPI Request 객체
        *args: 추가 위치 인자
        **kwargs: 추가 키워드 인자

    Returns:
        응답 데이터
    """
    logger.info(f"POST /v1/func/upload_markdown 호출됨")
    body = await request.json() if request.headers.get("content-type") == "application/json" else None
    return {
        "message": "Markdown 업로드 POST 엔드포인트",
        "method": "POST",
        "path": str(request.url.path),
        "body": body,
    }
