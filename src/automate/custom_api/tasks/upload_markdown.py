"""upload_markdown 관련 background task들."""

from __future__ import annotations

import subprocess
import time
from typing import Any

from loguru import logger

from ..config import get_custom_api_settings
from ..queue import huey


def _run_command(args: list[str], timeout_seconds: int) -> dict[str, Any]:
    """외부 명령을 실행하고 stdout/stderr/exit code를 반환합니다.

    워커 프로세스에서 실행되므로 동기 함수로 구현합니다.
    타임아웃/예외 상황에서도 고아 프로세스가 남지 않도록 terminate/kill 정리를 수행합니다.
    """

    process: subprocess.Popen[str] | None = None
    started = time.time()

    try:
        logger.info(f"[worker] 명령 실행: {' '.join(args)}")
        process = subprocess.Popen(  # noqa: S603
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout_text, stderr_text = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            logger.error(f"[worker] 명령 실행 타임아웃 ({timeout_seconds}초)")
            # 타임아웃 시 terminate → kill 순서로 정리
            try:
                process.terminate()
            except Exception:
                pass
            try:
                stdout_text, stderr_text = process.communicate(timeout=3)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
                try:
                    stdout_text, stderr_text = process.communicate(timeout=3)
                except Exception:
                    stdout_text, stderr_text = "", ""
            return {
                "ok": False,
                "returncode": None,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "error": f"timeout({timeout_seconds}s)",
                "duration_seconds": round(time.time() - started, 3),
            }

        return {
            "ok": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout_text or "",
            "stderr": stderr_text or "",
            "duration_seconds": round(time.time() - started, 3),
        }
    except FileNotFoundError as err:
        logger.error(f"[worker] 실행 파일을 찾을 수 없습니다: {args[0]}")
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": f"file_not_found: {err}",
            "duration_seconds": round(time.time() - started, 3),
        }
    except Exception as err:
        logger.exception(f"[worker] 명령 실행 중 오류: {err}")
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": str(err),
            "duration_seconds": round(time.time() - started, 3),
        }
    finally:
        # 예외/취소 등 어떤 케이스에서도 프로세스가 남지 않도록 최종 확인
        if process is not None and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=3)
            except Exception:
                try:
                    process.kill()
                    process.wait(timeout=3)
                except Exception:
                    pass


@huey.task()
def generate_post_from_airtable(row_id: str, use_codex: bool = True) -> dict[str, Any]:
    """Airtable row_id로 `mdb generate_post_from_airtable` 작업을 수행합니다.

    Returns:
        stdout/stderr/returncode 및 메타정보를 포함한 dict
    """

    settings = get_custom_api_settings()
    timeout = int(settings.COMMAND_TIMEOUT)

    args = ["mdb", "generate_post_from_airtable", "--row_id", row_id]
    if use_codex:
        args.append("--codex")

    result = _run_command(args=args, timeout_seconds=timeout)
    result.update(
        {
            "row_id": row_id,
            "command": " ".join(args),
            "timeout_seconds": timeout,
        }
    )
    return result

