"""서버 실행 명령어"""

import asyncio

import click
from hypercorn.asyncio import serve
from hypercorn.config import Config

from ...services.telegram.webhook import create_app


def get_config(env: str) -> Config:  # noqa: D103
    """환경별 설정을 반환합니다."""
    config = Config()

    if env == "dev":
        config.bind = ["127.0.0.1:8000"]
        config.use_reloader = True
        config.reload_dir = "src"
        config.loglevel = "debug"
    elif env == "prod":
        config.bind = ["0.0.0.0:8000"]
        config.workers = 4  # 멀티프로세스
        config.loglevel = "info"
        config.use_reloader = False

    return config


@click.command()
@click.argument(
    "env",
    type=click.Choice(["dev", "prod"]),
    default="dev",
)
def serve_command(env: str) -> None:
    """서버를 실행합니다.

    실행 환경에 따라 다른 설정이 적용됩니다:

    - dev: 개발 환경 (기본값)

        - 디버그 모드 활성화

        - 자세한 로깅

    - prod: 운영 환경

        - 최적화된 성능

    """
    app = create_app()
    config = get_config(env)
    print(f"mode: {env}")
    asyncio.run(serve(app, config))
