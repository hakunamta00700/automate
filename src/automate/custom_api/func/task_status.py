"""Huey task 상태 조회 기능.

동적 func 라우팅에 의해 `/v1/func/task_status`로 노출됩니다.
"""

from __future__ import annotations

from fastapi import HTTPException, Request
from loguru import logger

from ..queue import huey


async def get_method(request: Request):
    """GET /v1/func/task_status?task_id=..."""

    task_id = (request.query_params.get("task_id") or "").strip()
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id 쿼리 파라미터가 필요합니다.")

    try:
        result = huey.result(task_id, preserve=True)
    except Exception as e:
        logger.warning(f"Huey result 조회 실패: task_id={task_id}, err={e}")
        raise HTTPException(status_code=400, detail="유효하지 않은 task_id 입니다.") from e

    done = result is not None
    return {"task_id": task_id, "done": done, "result": result}

