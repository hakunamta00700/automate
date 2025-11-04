"""대본 포맷팅 유틸리티"""

from typing import Dict, List


def format_transcript_with_timestamps(transcript: List[Dict]) -> List[str]:
    """대본을 시간 포맷을 포함한 문자열 리스트로 변환합니다."""

    def seconds_to_hms(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02}:{m:02}:{s:02}"

    lines = []
    for entry in transcript:
        start = entry["start"]
        end = start + entry["duration"]
        start_str = seconds_to_hms(start)
        end_str = seconds_to_hms(end)
        text = entry["text"].replace("\n", " ")
        lines.append(f"[{start_str} - {end_str}] {text}")
    return lines
