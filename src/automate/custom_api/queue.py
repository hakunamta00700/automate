"""Huey queue 설정.

Custom API 프로세스와 `automate worker` 프로세스가 동일한 SQLite 파일을 공유하여
작업을 enqueue/consume 할 수 있도록 `SqliteHuey` 인스턴스를 제공합니다.

환경 변수:
    CUSTOM_API_HUEY_DB_PATH: Huey SQLite DB 파일 경로 (절대/상대 경로 모두 가능)
"""

from __future__ import annotations

import os
from pathlib import Path

from huey import SqliteHuey
from loguru import logger


def _default_db_path() -> Path:
    """기본 Huey DB 경로를 반환합니다.

    기본값은 실행 디렉토리 기준 `.cache/huey/automate-huey.db` 입니다.
    (운영에서는 CUSTOM_API_HUEY_DB_PATH로 고정 경로 지정 권장)
    """

    return Path(".cache") / "huey" / "automate-huey.db"


def _resolve_db_path() -> Path:
    """환경 변수/기본값을 조합하여 DB 경로를 결정합니다."""

    raw = os.getenv("CUSTOM_API_HUEY_DB_PATH")
    if raw:
        return Path(raw)
    return _default_db_path()


def _ensure_parent_dir(db_path: Path) -> None:
    """DB 파일 상위 디렉토리를 생성합니다."""

    parent = db_path.expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


_db_path = _resolve_db_path()
try:
    _ensure_parent_dir(_db_path)
except Exception as e:
    # 디렉토리 생성 실패 시에도 Huey 초기화를 시도하되, 원인 파악이 쉽도록 로그를 남깁니다.
    logger.warning(f"Huey DB 디렉토리 생성 실패: path={_db_path!s}, err={e}")


# 전역 Huey 인스턴스
huey = SqliteHuey("automate", filename=str(_db_path))

