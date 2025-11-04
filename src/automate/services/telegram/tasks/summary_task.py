"""YouTube 요약 Task"""

import asyncio

from loguru import logger
from telegram import Update
from telegram.ext import Application

from automate.core.constants import TaskKind
from automate.utils.youtube_utils import extract_video_id
from .base import BaseTask


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
            await self._run_command(command)

            logger.info(f"[WORKER] 완료: {video_id}")
            await self.send_message(application, f"✅ 요약 처리 완료: {video_id}")
        except Exception as err:
            logger.exception(f"[WORKER] 오류 발생: {video_id} - {err}")
            await self.send_message(application, f"❌ 처리 중 오류 발생: {video_id}")

    async def _run_command(self, command: str) -> None:
        """명령어를 실행합니다."""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        print("STDOUT:")
        print(stdout.decode())

        print("STDERR:")
        print(stderr.decode())

