"""텔레그램 관련 명령어"""

import asyncio

import click

from ...core.config import get_settings
from ...services.telegram import run_with_restart, send_to_channel_sync


@click.command()
def telegram_bot() -> None:
    """텔레그램 풀링 봇을 실행합니다.

    텔레그램 메시지를 수신하여 YouTube 영상 요약 및 쇼츠 처리를 수행합니다.
    오류 발생 시 자동으로 재시작됩니다.
    """
    run_with_restart()


@click.command()
@click.argument("message", type=str)
def send_telegram(message: str) -> None:
    """텔레그램 채널에 메시지를 전송합니다.

    Args:
        message: 전송할 메시지
    """
    settings = get_settings()
    if not settings.BOT_TOKEN:
        raise click.ClickException(
            "BOT_TOKEN is not set in environment variables or .env file."
        )

    try:
        send_to_channel_sync(message)
        click.echo(f"✅ Message sent to channel")
    except Exception as e:
        raise click.ClickException(f"Failed to send message: {e}")
