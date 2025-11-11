"""YouTube 비디오 처리"""

import asyncio
from dataclasses import asdict, dataclass
from typing import Dict, List

from loguru import logger

from ...utils.cache import get_cache
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
    cache = get_cache()

    # 1. 대본 가져오기 (캐시 확인)
    transcript_key = cache.get_transcript_key(video_id, language)
    transcript = cache.get(transcript_key)
    if transcript is None:
        logger.info(f"대본 캐시 미스: {video_id} ({language})")
        transcript = await get_transcript(video_id, language)
        cache.set(transcript_key, transcript)
    else:
        logger.info(f"대본 캐시 히트: {video_id} ({language})")

    # 2. 메타데이터 가져오기 (캐시 확인)
    metadata_key = cache.get_metadata_key(video_id)
    output = cache.get(metadata_key)
    if output is None:
        logger.info(f"메타데이터 캐시 미스: {video_id}")
        output = await get_youtube_metadata(video_id)
        cache.set(metadata_key, output)
    else:
        logger.info(f"메타데이터 캐시 히트: {video_id}")

    title = output["title"]
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"

    # 3. 요약 생성 (캐시 확인)
    summary_key = cache.get_summary_key(transcript)
    summary = cache.get(summary_key)
    if summary is None:
        logger.info(f"요약 캐시 미스: {video_id}")
        summary = await summarize(transcript)
        cache.set(summary_key, summary)
    else:
        logger.info(f"요약 캐시 히트: {video_id}")

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
