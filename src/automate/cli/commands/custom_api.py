"""Custom API 서버 실행 명령어"""

import asyncio
import signal
import sys

import click
from hypercorn.asyncio import serve
from hypercorn.config import Config
from loguru import logger

from ...custom_api.app import create_app
from ...custom_api.config import get_custom_api_settings


def get_config(env: str, host: str | None = None, port: int | None = None) -> Config:
    """환경별 설정을 반환합니다.

    Args:
        env: 환경 (dev 또는 prod)
        host: 서버 호스트 (기본값: 환경 변수 또는 기본값)
        port: 서버 포트 (기본값: 환경 변수 또는 기본값)

    Returns:
        Hypercorn Config 객체
    """
    settings = get_custom_api_settings()
    config = Config()

    # 파라미터가 제공되면 우선 사용, 없으면 환경 변수 또는 기본값 사용
    server_host = host or settings.CUSTOM_API_HOST
    server_port = port or settings.CUSTOM_API_PORT

    if env == "dev":
        config.bind = [f"127.0.0.1:{server_port}"]
        config.use_reloader = True
        config.reload_dir = "src"
        config.loglevel = "debug"
    elif env == "prod":
        config.bind = [f"{server_host}:{server_port}"]
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
@click.option(
    "--host",
    type=str,
    default=None,
    help="서버 호스트 (기본값: 환경 변수 CUSTOM_API_HOST 또는 0.0.0.0)",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="서버 포트 (기본값: 환경 변수 CUSTOM_API_PORT 또는 8001)",
)
def custom_api(env: str, host: str | None, port: int | None) -> None:
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

    예시:
        automate custom-api prod --host 0.0.0.0 --port 8080
        automate custom-api prod --port 9000
    """
    # 로깅 설정
    log_level = "DEBUG" if env == "dev" else "INFO"
    logger.remove()  # 기본 핸들러 제거
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # dev 환경일 때 기본 provider를 codex로 설정
    default_provider = "codex" if env == "dev" else "codex"
    # prod 환경일 때만 인증 활성화
    require_auth = env == "prod"
    app = create_app(default_provider=default_provider, require_auth=require_auth)
    settings = get_custom_api_settings()

    # 파라미터가 제공되면 우선 사용, 없으면 환경 변수 또는 기본값 사용
    server_host = host or settings.CUSTOM_API_HOST
    server_port = port or settings.CUSTOM_API_PORT

    config = get_config(env, host=server_host, port=server_port)

    # 서버 시작 로깅
    logger.info("=" * 60)
    logger.info("Custom API 서버 초기화 시작")
    logger.info(f"환경: {env}")
    logger.info(f"호스트: {server_host}")
    logger.info(f"포트: {server_port}")
    logger.info(f"로그 레벨: {log_level}")
    logger.info(f"기본 Provider: {default_provider}")

    if env == "prod":
        logger.info(f"워커 수: {config.workers}")
        logger.info("Production 모드: 최적화된 성능 설정 적용")
        if require_auth:
            if settings.CUSTOM_API_KEY:
                logger.info("인증 활성화: API Key 인증이 필요합니다")
            else:
                logger.warning(
                    "인증이 활성화되었지만 CUSTOM_API_KEY가 설정되지 않았습니다. "
                    ".env 파일에 CUSTOM_API_KEY를 설정하세요."
                )

    logger.info("=" * 60)
    click.echo(
        f"🚀 Custom API 서버 시작 (환경: {env}, "
        f"호스트: {server_host}, "
        f"포트: {server_port})"
    )

    # Graceful shutdown을 위한 시그널 핸들러
    def signal_handler(sig, frame):
        logger.info("종료 시그널 수신, 서버 종료 중...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("서버 시작 중...")
        asyncio.run(serve(app, config))
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버 종료 요청됨")
    except Exception as e:
        logger.exception(f"서버 실행 중 오류 발생: {e}")
        raise
    finally:
        logger.info("Custom API 서버 종료")
