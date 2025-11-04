"""대본 포맷팅"""

from typing import Dict, List


def format_transcript(transcript: List[Dict]) -> str:
    """대본 리스트를 하나의 문자열로 변환합니다."""
    return " ".join([entry["text"] for entry in transcript])
