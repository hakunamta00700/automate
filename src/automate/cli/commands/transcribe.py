"""전사 명령어"""

import click

from ..utils import check_env_vars
from ...services.youtube import extract_video_id, process_video


@click.command()
@click.option("--video-id", required=True, help="YouTube 비디오 ID")
@click.option(
    "--language",
    default="ko",
    help="자막 언어 코드 (예: ko-한국어, en-영어, ja-일본어 등)",
    show_default=True,
)
def transcribe(video_id: str, language: str) -> None:
    """YouTube 영상의 대본을 요약하고 Airtable에 저장합니다.

    지원되는 주요 언어 코드:
    - ko: 한국어 (기본값)
    - en: 영어
    - ja: 일본어
    - zh-Hans: 중국어(간체)
    - zh-Hant: 중국어(번체)

    전체 지원 언어 목록은 오류 메시지에서 확인할 수 있습니다.
    """
    import asyncio

    try:
        # 환경 변수 확인
        check_env_vars()

        # 처리 시작 메시지
        click.echo(f"🎬 비디오 ID '{video_id}' 처리를 시작합니다... (언어: {language})")

        # 대본 요약 및 저장 처리
        summary = asyncio.run(process_video(video_id, language))

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


@click.command()
@click.argument("url", type=str)
@click.pass_context
def transcribe_from_url(ctx: click.Context, url: str) -> None:
    """URL에서 비디오 ID를 추출하여 전사합니다."""
    video_id = extract_video_id(url)
    if not video_id:
        click.echo(f"❌ 유효하지 않은 YouTube URL입니다: {url}", err=True)
        raise click.Abort()
    click.echo(f"🎬 비디오 ID: {video_id}")
    ctx.invoke(transcribe, video_id=video_id, language="ko")


@click.command()
@click.argument("url", type=str)
def get_video_id_from_url(url: str) -> None:
    """URL에서 비디오 ID를 추출합니다."""
    video_id = extract_video_id(url)
    if not video_id:
        click.echo(f"❌ 유효하지 않은 YouTube URL입니다: {url}", err=True)
        raise click.Abort()
    click.echo(f"🎬 비디오 ID: {video_id}")
