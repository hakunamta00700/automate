"""Huey worker 실행 명령어."""

from __future__ import annotations

import sys

import click
from huey.consumer import Consumer
from loguru import logger

from ...custom_api.queue import huey


@click.command()
@click.option(
    "--workers",
    type=int,
    default=1,
    show_default=True,
    help="동시 실행 워커 수",
)
@click.option(
    "--worker-type",
    type=click.Choice(["thread", "process", "greenlet"]),
    default="thread",
    show_default=True,
    help="워커 타입",
)
@click.option(
    "--no-periodic",
    is_flag=True,
    default=False,
    help="periodic task 스케줄링 비활성화",
)
def worker(workers: int, worker_type: str, no_periodic: bool) -> None:
    """Huey consumer를 실행합니다.

    Custom API 프로세스가 enqueue한 작업을 SQLite(Huey) 큐에서 받아 실행합니다.
    """

    # task 등록 보장 (import 시점에 데코레이터가 Huey 인스턴스에 등록됨)
    import automate.custom_api.tasks  # noqa: F401

    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    logger.info("=" * 60)
    logger.info("Huey worker 시작")
    logger.info(f"DB: {getattr(huey, 'filename', None) or 'sqlite'}")
    logger.info(f"workers: {workers}, worker_type: {worker_type}, periodic: {not no_periodic}")
    logger.info("=" * 60)

    consumer = Consumer(huey, workers=workers, worker_type=worker_type, periodic=not no_periodic)
    consumer.run()

