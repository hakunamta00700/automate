"""Task 베이스 클래스"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from telegram import Update

if TYPE_CHECKING:
    from telegram.ext import Application


class BaseTask(ABC):
    """모든 Task의 기본 클래스"""

    # 각 Task 클래스에서 반드시 정의해야 하는 클래스 변수
    TASK_NAME: str  # Task 고유 이름 (예: "summary", "shorts")
    COMMAND_PREFIX: str  # 명령어 접두사 (예: "요약|", "쇼츠|")

    @abstractmethod
    async def parse_message(self, text: str, update: Update) -> str | None:
        """
        메시지를 파싱하여 Task 값(value)을 추출합니다.

        Args:
            text: 파싱할 텍스트 (COMMAND_PREFIX 제외)
            update: Telegram Update 객체

        Returns:
            Task 값 문자열 또는 None (파싱 실패 시)
        """
        pass

    @abstractmethod
    async def execute(
        self,
        value: str,
        application: "Application",
        chat_id: int | None = None,
        update: Update | None = None,
    ) -> None:
        """
        Task를 실행합니다.

        Args:
            value: Task 값 (parse_message에서 추출된 값)
            application: Telegram Application 객체
            update: Telegram Update 객체 (선택사항)
        """
        pass

    async def send_message(
        self, application: "Application", text: str, chat_id: int | None = None
    ) -> None:
        """텔레그램 메시지를 전송합니다."""
        from automate.core.config import get_settings

        settings = get_settings()
        target_chat_id = chat_id if chat_id is not None else settings.channel_chat_id_int
        await application.bot.send_message(chat_id=target_chat_id, text=text)

