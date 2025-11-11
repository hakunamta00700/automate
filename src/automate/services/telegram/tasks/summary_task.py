"""YouTube 요약 Task"""

import asyncio

from loguru import logger
from telegram import Update
from telegram.ext import Application

from automate.core.constants import TaskKind
from automate.utils.youtube_utils import extract_video_id
from .base import BaseTask


class ResourceExhaustedError(Exception):
    """429 에러 (Resource Exhausted)를 나타내는 예외 클래스"""

    pass


class SummaryTask(BaseTask):
    """YouTube 영상 요약 Task"""

    TASK_NAME = TaskKind.SUMMARY
    COMMAND_PREFIX = "요약|"

    async def parse_message(self, text: str, update: Update) -> str | None:
        """YouTube URL에서 video_id를 추출합니다."""
        video_id = extract_video_id(text)
        if not video_id:
            await update.message.reply_text("❌ 유효하지 않은 YouTube URL입니다.")
            return None
        return video_id

    async def execute(
        self, value: str, application: Application, update: Update | None = None
    ) -> None:
        """요약 작업을 실행합니다."""
        video_id = value
        try:
            logger.info(f"[WORKER] 처리 시작: {video_id}")
            await self.send_message(application, f"요약 처리 시작: {video_id}")

            # video_url = f'"https://www.youtube.com/watch?v={video_id}"'
            command = f"automate transcribe --video-id {video_id}"
            await self._run_command(command, video_id, application)

            logger.info(f"[WORKER] 완료: {video_id}")
            await self.send_message(application, f"✅ 요약 처리 완료: {video_id}")
        except ResourceExhaustedError:
            # 429 에러 (Resource Exhausted) 처리 - 이미 _run_command에서 처리됨
            pass
        except Exception as err:
            logger.exception(f"[WORKER] 오류 발생: {video_id} - {err}")
            await self.send_message(application, f"❌ 처리 중 오류 발생: {video_id}")

    async def _run_command(
        self, command: str, video_id: str, application: Application
    ) -> None:
        """명령어를 실행합니다.
        
        Args:
            command: 실행할 명령어
            video_id: YouTube 비디오 ID (에러 처리용)
            application: Telegram Application 객체 (에러 처리용)
        
        Raises:
            ResourceExhaustedError: 429 에러가 발생한 경우
            RuntimeError: 명령어 실행이 실패한 경우 (반환 코드가 0이 아님)
        """
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()
        
        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""

        logger.debug(f"명령어 실행 결과 - 반환 코드: {process.returncode}")
        if stdout_text:
            logger.debug(f"STDOUT:\n{stdout_text}")
        if stderr_text:
            logger.debug(f"STDERR:\n{stderr_text}")

        # 429 에러 감지 (stdout 또는 stderr에 429 또는 RESOURCE_EXHAUSTED가 포함된 경우)
        combined_output = f"{stdout_text}\n{stderr_text}"
        if (
            "429" in combined_output
            or "RESOURCE_EXHAUSTED" in combined_output
            or "Resource exhausted" in combined_output
        ):
            logger.warning(
                f"[WORKER] 429 에러 발생 (리소스 소진): {video_id} - 10분 후 재시도 예약"
            )
            await self.send_message(
                application,
                f"❌ 처리 중 오류 발생 (리소스 소진): {video_id}\n⏳ 10분 후 자동 재시도 예약됨",
            )
            # 10분(600초) 후에 Task를 다시 큐에 추가
            await self._schedule_retry(video_id, application, delay_seconds=600)
            raise ResourceExhaustedError(f"429 에러 발생: {video_id}")

        # 반환 코드가 0이 아니면 에러로 처리
        if process.returncode != 0:
            error_msg = f"명령어 실행 실패 (반환 코드: {process.returncode})"
            if stderr_text:
                error_msg += f"\n에러 출력:\n{stderr_text}"
            raise RuntimeError(error_msg)

    async def _schedule_retry(
        self, video_id: str, application: Application, delay_seconds: int = 600
    ) -> None:
        """지정된 시간 후에 Task를 다시 큐에 추가합니다.

        Args:
            video_id: YouTube 비디오 ID
            application: Telegram Application 객체
            delay_seconds: 재시도까지 대기할 시간 (초, 기본값: 600 = 10분)
        """
        from ..bot import QueuedTask, task_queue

        async def _retry_task():
            """지정된 시간 후에 Task를 큐에 추가하는 내부 함수"""
            await asyncio.sleep(delay_seconds)
            await task_queue.put(QueuedTask(task_name=self.TASK_NAME, value=video_id))
            logger.info(f"[WORKER] 재시도 Task 큐에 추가: {video_id} (10분 후)")
            await self.send_message(
                application, f"🔄 재시도 시작: {video_id}"
            )

        # 백그라운드에서 재시도 태스크 실행
        asyncio.create_task(_retry_task())

