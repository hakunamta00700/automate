"""텔레그램 봇 Task 모듈

이 디렉토리에 새로운 Task 파일을 추가하면 자동으로 등록됩니다.
Task 클래스는 BaseTask를 상속받고 TASK_NAME과 COMMAND_PREFIX를 정의해야 합니다.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, Type

from loguru import logger

from .base import BaseTask

# Task 레지스트리
_task_registry: Dict[str, Type[BaseTask]] = {}


def _load_tasks() -> None:
    """tasks 디렉토리에서 모든 Task 클래스를 자동으로 로드합니다."""
    tasks_dir = Path(__file__).parent

    # 현재 디렉토리의 모든 Python 파일을 순회
    for file_path in tasks_dir.glob("*.py"):
        # __init__.py와 base.py는 제외
        if file_path.name in ("__init__.py", "base.py"):
            continue

        module_name = file_path.stem
        try:
            # 모듈 동적 임포트 (상대 경로 사용)
            from . import base as _base_module

            package_name = _base_module.__package__
            module = importlib.import_module(f".{module_name}", package=package_name)
            # 모듈에서 BaseTask를 상속받은 모든 클래스 찾기
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BaseTask)
                    and obj is not BaseTask
                    and hasattr(obj, "TASK_NAME")
                    and hasattr(obj, "COMMAND_PREFIX")
                ):
                    task_name = obj.TASK_NAME
                    if task_name in _task_registry:
                        logger.warning(
                            f"Task '{task_name}'가 이미 등록되어 있습니다. "
                            f"{obj.__name__}은(는) 무시됩니다."
                        )
                        continue
                    _task_registry[task_name] = obj
                    logger.info(f"✅ Task 등록됨: {task_name} ({obj.__name__})")
        except Exception as e:
            logger.error(f"❌ Task 모듈 로드 실패 ({module_name}): {e}")


def get_task_by_command_prefix(command_prefix: str) -> Type[BaseTask] | None:
    """명령어 접두사로 Task 클래스를 찾습니다."""
    for task_cls in _task_registry.values():
        if task_cls.COMMAND_PREFIX == command_prefix:
            return task_cls
    return None


def get_task_by_name(task_name: str) -> Type[BaseTask] | None:
    """Task 이름으로 Task 클래스를 찾습니다."""
    return _task_registry.get(task_name)


def get_all_tasks() -> Dict[str, Type[BaseTask]]:
    """등록된 모든 Task를 반환합니다."""
    return _task_registry.copy()


# 모듈 로드 시 자동으로 Task 로드
_load_tasks()

