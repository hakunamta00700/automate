"""upload_markdown 관련 background task들."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from typing import Any

from loguru import logger

from ..config import get_custom_api_settings
from ..queue import huey


def _preview(text: str, limit: int = 800) -> str:
    """로그용 미리보기 문자열을 생성합니다."""

    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"...(truncated, total={len(text)})"


def _env_flag(name: str, default: str = "0") -> bool:
    """환경변수 boolean 파서."""

    val = (os.getenv(name, default) or "").strip().lower()
    return val in {"1", "true", "yes", "y", "on"}


def _run_command(args: list[str], timeout_seconds: int) -> dict[str, Any]:
    """외부 명령을 실행하고 stdout/stderr/exit code를 반환합니다.

    워커 프로세스에서 실행되므로 동기 함수로 구현합니다.
    타임아웃/예외 상황에서도 고아 프로세스가 남지 않도록 terminate/kill 정리를 수행합니다.
    """

    process: subprocess.Popen[str] | None = None
    started = time.time()

    try:
        cmd = " ".join(args)
        stream_logs = _env_flag("CUSTOM_API_WORKER_STREAM_LOGS", default="1")
        # 너무 큰 출력은 저장만 제한하고(읽기는 계속), 로그도 과도해질 수 있으니 필요 시 env로 제어
        max_capture_chars = int(os.getenv("CUSTOM_API_WORKER_MAX_CAPTURE_CHARS", "2000000"))
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        stdout_chars = 0
        stderr_chars = 0
        stdout_truncated = False
        stderr_truncated = False

        def _consume(stream: Any, parts: list[str], which: str) -> None:
            nonlocal stdout_chars, stderr_chars, stdout_truncated, stderr_truncated

            try:
                for line in iter(stream.readline, ""):
                    # line includes trailing newline
                    if which == "stdout":
                        if stdout_chars < max_capture_chars:
                            parts.append(line)
                            stdout_chars += len(line)
                        else:
                            stdout_truncated = True
                        if stream_logs:
                            logger.info("[worker] STDOUT {}", line.rstrip("\n"))
                    else:
                        if stderr_chars < max_capture_chars:
                            parts.append(line)
                            stderr_chars += len(line)
                        else:
                            stderr_truncated = True
                        if stream_logs:
                            # stderr는 warning으로 남겨도 좋지만 info로 통일
                            logger.info("[worker] STDERR {}", line.rstrip("\n"))
            except Exception as e:
                logger.debug("[worker] stream reader error: which={} err={}", which, e)
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

        logger.info(
            f"[worker] COMMAND_START pid={os.getpid()} timeout={timeout_seconds}s cmd={cmd}"
        )
        process = subprocess.Popen(  # noqa: S603
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffering (text mode)
        )

        if process.stdout is None or process.stderr is None:
            raise RuntimeError("subprocess stdout/stderr pipe 초기화 실패")

        t_out = threading.Thread(
            target=_consume, args=(process.stdout, stdout_parts, "stdout"), daemon=True
        )
        t_err = threading.Thread(
            target=_consume, args=(process.stderr, stderr_parts, "stderr"), daemon=True
        )
        t_out.start()
        t_err.start()

        deadline = started + timeout_seconds
        timed_out = False
        while True:
            rc = process.poll()
            if rc is not None:
                break
            if time.time() >= deadline:
                timed_out = True
                break
            time.sleep(0.1)

        if timed_out:
            duration = round(time.time() - started, 3)
            logger.error(
                "[worker] COMMAND_TIMEOUT pid={} duration={}s timeout={}s cmd={}",
                os.getpid(),
                duration,
                timeout_seconds,
                cmd,
            )
            try:
                process.terminate()
            except Exception:
                pass
            # 조금 기다렸다가 여전히 살아있으면 kill
            try:
                process.wait(timeout=3)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
                try:
                    process.wait(timeout=3)
                except Exception:
                    pass

        # reader thread 정리(너무 오래 기다리지는 않음)
        t_out.join(timeout=2)
        t_err.join(timeout=2)

        stdout_text = "".join(stdout_parts)
        stderr_text = "".join(stderr_parts)
        duration = round(time.time() - started, 3)

        if timed_out:
            return {
                "ok": False,
                "returncode": None,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
                "error": f"timeout({timeout_seconds}s)",
                "duration_seconds": duration,
            }

        logger.info(
            "[worker] COMMAND_END pid={} rc={} ok={} duration={}s stdout_len={} stderr_len={} "
            "stdout_truncated={} stderr_truncated={}",
            os.getpid(),
            process.returncode,
            process.returncode == 0,
            duration,
            len(stdout_text or ""),
            len(stderr_text or ""),
            stdout_truncated,
            stderr_truncated,
        )
        return {
            "ok": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout_text or "",
            "stderr": stderr_text or "",
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "duration_seconds": duration,
        }
    except FileNotFoundError as err:
        duration = round(time.time() - started, 3)
        logger.error(
            "[worker] COMMAND_NOT_FOUND pid={} duration={}s exe={} err={}",
            os.getpid(),
            duration,
            args[0],
            err,
        )
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": f"file_not_found: {err}",
            "duration_seconds": duration,
        }
    except Exception as err:
        duration = round(time.time() - started, 3)
        logger.exception(
            "[worker] COMMAND_ERROR pid={} duration={}s err={}",
            os.getpid(),
            duration,
            err,
        )
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": str(err),
            "duration_seconds": duration,
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

    task_started = time.time()
    cmd = " ".join(args)
    logger.info(
        "[worker] TASK_START kind=upload_markdown_airtable pid={} row_id={} "
        "use_codex={} timeout={}s cmd={}",
        os.getpid(),
        row_id,
        use_codex,
        timeout,
        cmd,
    )

    result = _run_command(args=args, timeout_seconds=timeout)
    result.update(
        {
            "row_id": row_id,
            "command": " ".join(args),
            "timeout_seconds": timeout,
        }
    )

    task_duration = round(time.time() - task_started, 3)
    ok = bool(result.get("ok"))
    rc = result.get("returncode")
    err_value = result.get("error")
    err = str(err_value) if err_value else None
    stdout_preview = _preview(str(result.get("stdout") or ""))
    stderr_preview = _preview(str(result.get("stderr") or ""))

    # 실패인데 error 필드가 비어있으면(예: returncode != 0) 요약 에러를 생성합니다.
    if not ok and not err:
        err = f"returncode({rc})" if rc is not None else "unknown_error"
        result["error"] = err

    if ok:
        logger.info(
            "[worker] TASK_END kind=upload_markdown_airtable pid={} row_id={} ok=True "
            "rc={} duration={}s",
            os.getpid(),
            row_id,
            rc,
            task_duration,
        )
    else:
        logger.warning(
            "[worker] TASK_END kind=upload_markdown_airtable pid={} row_id={} ok=False "
            "rc={} duration={}s "
            "error={} stderr_preview={}",
            os.getpid(),
            row_id,
            rc,
            task_duration,
            err,
            stderr_preview,
        )
        # 성공일 때 stdout 전체를 로그로 남기면 너무 커질 수 있어,
        # 실패 시에만 미리보기 로그를 남깁니다.
        if stdout_preview:
            logger.debug(
                "[worker] TASK_STDOUT_PREVIEW kind=upload_markdown_airtable row_id={} {}",
                row_id,
                stdout_preview,
            )

    return result

