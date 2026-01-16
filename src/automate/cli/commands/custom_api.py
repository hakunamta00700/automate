"""Custom API 서버 실행 명령어"""

import asyncio

import click
from hypercorn.asyncio import serve
from hypercorn.config import Config

from ...custom_api.app import create_app
from ...custom_api.config import get_custom_api_settings


def get_config(env: str) -> Config:
    """환경별 설정을 반환합니다.

    Args:
        env: 환경 (dev 또는 prod)

    Returns:
        Hypercorn Config 객체
    """
    settings = get_custom_api_settings()
    config = Config()

    if env == "dev":
        config.bind = [f"127.0.0.1:{settings.CUSTOM_API_PORT}"]
        config.use_reloader = True
        config.reload_dir = "src"
        config.loglevel = "debug"
    elif env == "prod":
        config.bind = [f"{settings.CUSTOM_API_HOST}:{settings.CUSTOM_API_PORT}"]
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
def custom_api(env: str) -> None:
    """Custom API 서버를 실행합니다.

    실행 환경에 따라 다른 설정이 적용됩니다:

    - dev: 개발 환경 (기본값)
        - 디버그 모드 활성화
        - 자세한 로깅
        - 자동 리로드

    - prod: 운영 환경
        - 최적화된 성능
        - 멀티프로세스 워커

    환경 변수:
        CUSTOM_API_HOST: 서버 호스트 (기본값: 0.0.0.0)
        CUSTOM_API_PORT: 서버 포트 (기본값: 8001)
    """
    app = create_app()
    config = get_config(env)
    settings = get_custom_api_settings()
    click.echo(
        f"🚀 Custom API 서버 시작 (환경: {env}, "
        f"호스트: {settings.CUSTOM_API_HOST}, "
        f"포트: {settings.CUSTOM_API_PORT})"
    )
    asyncio.run(serve(app, config))
