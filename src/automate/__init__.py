import os
import click
from dotenv import load_dotenv
from .youtube_lib import process_video, extract_video_id
from .cli import run as run_server

# 환경 변수 로드
load_dotenv()

# 필수 환경 변수 확인
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "AIRTABLE_API_KEY",
    "AIRTABLE_BASE_NAME",
    "AIRTABLE_TABLE_NAME",
    "BOT_TOKEN",
    "WEBHOOK_DOMAIN",
    "WEBHOOK_PATH"
]


def check_env_vars():
    """필수 환경 변수가 설정되어 있는지 확인합니다."""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise click.ClickException(
            f"다음 환경 변수들이 설정되지 않았습니다: {', '.join(missing_vars)}\n"
            ".env 파일을 확인해주세요."
        )


@click.group()
def cli():
    """YouTube 영상 대본 요약 및 Airtable 저장 도구"""
    pass


@cli.command()
@click.option("--video-id", required=True, help="YouTube 비디오 ID")
@click.option(
    "--language",
    default="ko",
    help="자막 언어 코드 (예: ko-한국어, en-영어, ja-일본어 등)",
    show_default=True,
)
def transcribe(video_id, language):
    """YouTube 영상의 대본을 요약하고 Airtable에 저장합니다.

    지원되는 주요 언어 코드:
    - ko: 한국어 (기본값)
    - en: 영어
    - ja: 일본어
    - zh-Hans: 중국어(간체)
    - zh-Hant: 중국어(번체)

    전체 지원 언어 목록은 오류 메시지에서 확인할 수 있습니다.
    """
    try:
        # 환경 변수 확인
        check_env_vars()

        # 처리 시작 메시지
        click.echo(f"🎬 비디오 ID '{video_id}' 처리를 시작합니다... (언어: {language})")

        # 대본 요약 및 저장 처리
        summary = process_video(video_id, language)

        # 성공 메시지 및 요약 내용 출력
        click.echo("\n✅ 성공적으로 처리되었습니다!")
        click.echo("\n📝 요약 내용:")
        click.echo("=" * 50)
        click.echo(summary)
        click.echo("=" * 50)

    except Exception as e:
        import traceback
        click.echo(f"\n❌ 오류가 발생했습니다: {str(e)}", err=True)
        click.echo("\n📍 오류 발생 위치:", err=True)
        click.echo(traceback.format_exc(), err=True)
        raise click.Abort()
    
@cli.command()
@click.argument("url", type=str)
@click.pass_context
def transcribe_from_url(ctx, url: str):
    video_id = extract_video_id(url)
    click.echo(f"🎬 비디오 ID: {video_id}")
    ctx.invoke(transcribe, video_id=video_id, language="ko")

@cli.command()
@click.argument("url", type=str)
def get_video_id_from_url(url: str):
    video_id = extract_video_id(url)
    click.echo(f"🎬 비디오 ID: {video_id}")
    

@cli.command()
@click.argument(
    "env",
    type=click.Choice(["dev", "prod"]),
    default="dev",
)
def serve(env):
    """서버를 실행합니다.

    실행 환경에 따라 다른 설정이 적용됩니다:

    - dev: 개발 환경 (기본값)

        - 디버그 모드 활성화

        - 자세한 로깅

    - prod: 운영 환경

        - 최적화된 성능

    """
    run_server(env)


if __name__ == "__main__":
    cli()
