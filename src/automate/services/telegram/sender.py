"""텔레그램 메시지 전송"""

import asyncio

from telegram import Bot

from ...core.config import get_settings


async def send_message(chat_id: str | int, text: str) -> None:
    """텔레그램 메시지를 전송합니다.

    Args:
        chat_id: 채널 또는 채팅 ID
        text: 전송할 메시지
    """
    settings = get_settings()
    bot_token = settings.bot_token_str

    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=text)


async def send_to_channel(text: str) -> None:
    """설정된 채널에 메시지를 전송합니다.

    Args:
        text: 전송할 메시지
    """
    settings = get_settings()
    channel_id = settings.channel_chat_id_int
    await send_message(channel_id, text)


# 동기 래퍼 (CLI에서 사용)
def send_message_sync(chat_id: str | int, text: str) -> None:
    """텔레그램 메시지를 동기적으로 전송합니다."""
    asyncio.run(send_message(chat_id, text))


def send_to_channel_sync(text: str) -> None:
    """설정된 채널에 메시지를 동기적으로 전송합니다."""
    asyncio.run(send_to_channel(text))
