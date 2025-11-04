"""YouTube 비디오 처리"""

import asyncio
from dataclasses import asdict, dataclass
from typing import Dict, List

from ..airtable.repository import save_to_airtable
from ..summary.formatter import format_transcript
from ..summary.generator import summarize
from .metadata import get_youtube_metadata
from .transcript import get_transcript


@dataclass
class Youtube:
    """YouTube 비디오 데이터 모델"""

    url: str
    title: str
    thumbnail_url: str
    thumbnail: List[Dict]
    transcript: str
    summary: str


async def process_video(video_id: str, language: str = "ko") -> str:
    """비디오 처리의 전체 과정을 실행합니다.

    Args:
        video_id: YouTube 비디오 ID
        language: 자막 언어 코드 (기본값: 'ko' - 한국어)

    Returns:
        요약된 내용
    """
    transcript = await get_transcript(video_id, language)
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
    output = await get_youtube_metadata(video_id)
    title = output["title"]
    summary = await summarize(transcript)
    youtube = Youtube(
        url=f"https://www.youtube.com/watch?v={video_id}",
        title=title,
        thumbnail_url=thumbnail_url,
        # thumbnail 필드는 thumbnail_url로 부터 이미지를 Attachment로 저장한다.
        thumbnail=[{"url": thumbnail_url}],
        transcript=format_transcript(transcript),
        summary=summary,
    )
    await save_to_airtable(video_id, asdict(youtube))
    return summary
