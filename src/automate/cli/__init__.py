"""CLI 모듈"""

import click

from .commands.custom_api import custom_api
from .commands.dispatch import dispatch
from .commands.serve import serve_command
from .commands.telegram import send_telegram, telegram_bot
from .commands.transcribe import (
    get_video_id_from_url,
    transcribe,
    transcribe_from_url,
)


@click.group()
def cli() -> None:
    """YouTube 영상 대본 요약 및 Airtable 저장 도구"""
    pass


# 명령어 등록
cli.add_command(transcribe)
cli.add_command(transcribe_from_url)
cli.add_command(get_video_id_from_url)
cli.add_command(serve_command, name="serve")
cli.add_command(telegram_bot, name="telegram-bot")
cli.add_command(dispatch)
cli.add_command(send_telegram, name="send-telegram")
cli.add_command(custom_api, name="custom-api")


__all__ = ["cli"]
