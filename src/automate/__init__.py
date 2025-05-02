import os
import click
from dotenv import load_dotenv
from .youtube_lib import process_video

# 환경 변수 로드
load_dotenv()

# 필수 환경 변수 확인
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "AIRTABLE_API_KEY",
    "AIRTABLE_BASE_ID",
    "AIRTABLE_TABLE_NAME"
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
@click.option('--video-id', required=True, help='YouTube 비디오 ID')
def transcribe(video_id):
    """YouTube 영상의 대본을 요약하고 Airtable에 저장합니다."""
    try:
        # 환경 변수 확인
        check_env_vars()
        
        # 처리 시작 메시지
        click.echo(f"🎬 비디오 ID '{video_id}' 처리를 시작합니다...")
        
        # 대본 요약 및 저장 처리
        summary = process_video(video_id)
        
        # 성공 메시지 및 요약 내용 출력
        click.echo(f"\n✅ 성공적으로 처리되었습니다!")
        click.echo("\n📝 요약 내용:")
        click.echo("=" * 50)
        click.echo(summary)
        click.echo("=" * 50)
        
    except Exception as e:
        click.echo(f"\n❌ 오류가 발생했습니다: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
