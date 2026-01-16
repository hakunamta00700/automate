"""쇼츠 대본 생성 Task"""

import aiohttp
from loguru import logger
from telegram import Update
from telegram.ext import Application

from automate.core.constants import TaskKind, WebHook

from .base import BaseTask


class ShortsTask(BaseTask):
    """쇼츠 대본 생성 Task"""

    TASK_NAME = TaskKind.SHORTS
    COMMAND_PREFIX = "쇼츠|"

    async def parse_message(self, text: str, update: Update) -> str | None:
        """URL을 추출합니다."""
        return text.strip()

    async def execute(
        self,
        value: str,
        application: Application,
        chat_id: int | None = None,
        update: Update | None = None,
    ) -> None:
        """쇼츠 작업을 실행합니다."""
        page_url = value
        try:
            logger.info(f"[WORKER] 처리 시작: {page_url}")
            await self.send_message(application, f"쇼츠 대본생성 시작: {page_url}", chat_id=chat_id)

            target_url = f"{WebHook.shorts}?url={page_url}"
            await self._fetch_data(target_url)

            logger.info(f"[WORKER] 완료: {page_url}")
            await self.send_message(application, f"✅ 쇼츠 처리 완료: {page_url}", chat_id=chat_id)
        except Exception as e:
            logger.exception(f"[WORKER] 오류 발생: {page_url}")
            await self.send_message(
                application,
                f"❌ 처리 중 오류 발생: {page_url} - {e}",
                chat_id=chat_id,
            )

    async def _fetch_data(self, url: str) -> str | None:
        """주어진 URL로 GET 요청을 보내고 응답 텍스트를 반환합니다."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error: {response.status} - {response.reason}")
                    return None
