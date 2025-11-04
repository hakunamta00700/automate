"""YouTube 관련 유틸리티"""

import re
from urllib.parse import parse_qs, urlparse


def extract_video_id(url: str) -> str | None:
    """
    YouTube URL에서 video ID(11자)를 추출한다.

    지원하는 URL 형식:
      - https://www.youtube.com/watch?v=ID
      - https://youtu.be/ID
      - https://www.youtube.com/shorts/ID
      - 위에 &t=, &list=, &index= 등 추가 파라미터 포함 URL
    """
    parsed = urlparse(url)
    # 1) 표준 watch URL (?v=ID)
    if parsed.path == "/watch":
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]

    # 2) youtu.be/ID
    if parsed.netloc.endswith("youtu.be"):
        m = re.match(r"^/([\w-]{11})", parsed.path)
        if m:
            return m.group(1)

    # 3) youtube.com/shorts/ID
    if parsed.netloc.endswith("youtube.com"):
        m = re.match(r"^/shorts/([\w-]{11})", parsed.path)
        if m:
            return m.group(1)

    # 4) 그 외 파라미터·경로 조합에 대해 fallback
    #    - "v=ID", "youtu.be/ID", "/shorts/ID" 패턴 전역 검색
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
    if m:
        return m.group(1)

    return None
