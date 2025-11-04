"""대본 추출 스크립트"""

import asyncio
import sys

from ..services.youtube import extract_video_id, get_transcript
from ..utils.transcript_utils import format_transcript_with_timestamps


async def main() -> None:
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python -m automate.scripts.get_transcript <YOUTUBE_URL>")
        sys.exit(1)

    url = sys.argv[1]
    video_id = extract_video_id(url)

    if not video_id:
        print(f"❌ 유효하지 않은 YouTube URL입니다: {url}")
        sys.exit(1)

    language = "ko"
    transcript = await get_transcript(video_id, language)
    formatted_transcript = format_transcript_with_timestamps(transcript)
    print("\n".join(formatted_transcript))
    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(formatted_transcript))


if __name__ == "__main__":
    asyncio.run(main())
