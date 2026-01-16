"""YouTube 대본 추출"""

from youtube_transcript_api import YouTubeTranscriptApi

from ...utils.async_utils import to_async


@to_async
def get_transcript(video_id: str, language: str = "ko") -> list[dict]:
    """YouTube 비디오의 대본을 가져옵니다.

    Args:
        video_id: YouTube 비디오 ID
        language: 자막 언어 코드 (기본값: 'ko' - 한국어)

    Returns:
        대본 목록 (각 항목은 {"text": str, "start": float, "duration": float})
    """
    api = YouTubeTranscriptApi()
    try:
        # 요청한 언어로 대본 가져오기
        transcript = api.fetch(video_id, languages=[language])
        return transcript.to_raw_data()
    except Exception as e:
        print(f"Error getting transcript in '{language}': {e}")
        try:
            # 영어로 폴백 시도
            transcript = api.fetch(video_id, languages=["en"])
            return transcript.to_raw_data()
        except Exception as e2:
            print(f"Error getting transcript in 'en': {e2}")
            raise Exception(
                "Failed to get transcript in both requested language and English."
            )
