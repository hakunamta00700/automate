import asyncio
import os
import re
from dataclasses import asdict, dataclass
from typing import Dict, List
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pyairtable import Api
from youtube_transcript_api import YouTubeTranscriptApi

from .airtable_lib import get_base_from_aritable, get_table_from_base
from .async_lib import to_async

@dataclass
class Youtube:
    url: str
    title: str
    thumbnail_url: str
    thumbnail: List[Dict]
    transcript: str
    summary: str


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


@to_async
def get_transcript(video_id: str, language: str = "ko") -> List[Dict]:
    """YouTube 비디오의 대본을 가져옵니다.

    Args:
        video_id: YouTube 비디오 ID
        language: 자막 언어 코드 (기본값: 'ko' - 한국어)

    Returns:
        대본 목록
    """
    transcript = YouTubeTranscriptApi.get_transcript(
        video_id,
        languages=[language],
        preserve_formatting=True,
    )
    return transcript


def format_transcript(transcript: List[Dict]) -> str:
    """대본 리스트를 하나의 문자열로 변환합니다."""
    return " ".join([entry["text"] for entry in transcript])


@to_async
def summarize(transcript: List[Dict]) -> str:
    """OpenAI API를 사용하여 대본을 요약합니다."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    formatted_text = format_transcript(transcript)

    system_prompt: ChatCompletionMessageParam = {
        "role": "system",
        "content": """
다음은 유튜브 영상의 대본이다. 이 내용을 독자가 쉽게 이해할 수 있도록 핵심만 구조화된 요약문으로 정리해줘.

특히 다음의 요소를 중심으로 작성해줘:

1. ✅ 영상의 핵심 주제
2. 🧠 전달하고자 하는 주요 메시지
3. 📌 구체적인 핵심 내용 요약 (항목별로 정리)
   - 실험, 연구 결과, 주요 논리, 주장 등은 쉽게 풀어 써줘
   - 필요 시 도표나 수치의 의미도 설명해줘
4. 🚫 주의사항이나 오해할 수 있는 부분이 있다면 명확히 짚어줘
5. 💡 영상의 결론 및 실생활 적용 또는 시사점
6. ✍️ 마지막에 '이 내용을 기반으로 더 알고 싶은 주제'를 추천해줘

추가로, 아래 절차에 따라 유형을 인식하고 포맷을 맞춰:

① **영상 유형 자동 분류**: 정치시사 / 분석강의 / 브이로그 / 주장촉구 / 교육지식 / 리뷰 등  
② **유형에 따라 요약 포맷 조정**:  
- 뉴스·시사 → 타임라인 중심 정리  
- 주장·비판 → 논점 요약 + 반론 구조 포함  
- 강연·교육 → 개념-예시-적용 순  
- 리뷰 → 항목별 장단점 비교 등  

✍️ 블로그 글처럼 읽기 쉽게 구성해줘. 문어체 사용, 어려운 표현은 쉽게 풀어서 설명해줘.  
요약문 전체는 500~1000자 내외로, **가독성이 높은 문단과 항목별 구성**을 갖추고 있어야 해.

""",
    }
    user_prompt: ChatCompletionMessageParam = {
        "role": "user",
        "content": formatted_text,
    }
    messages: list[ChatCompletionMessageParam] = [system_prompt, user_prompt]

    full_response = ""
    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
        )
        chunk = response.choices[0].message.content or ""
        full_response += chunk
        finish_reason = getattr(response.choices[0], "finish_reason", None)
        if finish_reason != "length":
            break
        # 이어서 요청: 지금까지의 assistant 응답을 messages에 추가
        messages.append({"role": "assistant", "content": chunk})
    return full_response


async def save_to_airtable(video_id: str, record: dict) -> None:
    """요약된 내용을 Airtable에 저장합니다."""
    api_key = os.getenv("AIRTABLE_API_KEY")
    if api_key is None:
        raise ValueError("AIRTABLE_API_KEY is not set")
    base_name = os.getenv("AIRTABLE_BASE_NAME")
    if base_name is None:
        raise ValueError("AIRTABLE_BASE_NAME is not set")
    table_name = os.getenv("AIRTABLE_TABLE_NAME")
    if table_name is None:
        raise ValueError("AIRTABLE_TABLE_NAME is not set")
    print("api_key", api_key)
    print("base_name", base_name)
    print("table_name", table_name)
    api = Api(api_key)
    base = await asyncio.to_thread(get_base_from_aritable, api, base_name)
    table = await asyncio.to_thread(get_table_from_base, base, table_name)
    await asyncio.to_thread(table.create, record)


async def get_youtube_metadata(video_id: str) -> Dict:
    """YouTube 비디오의 메타데이터를 가져옵니다."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = await asyncio.to_thread(requests.get, url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("title").text
    thumbnail = soup.find("meta", {"property": "og:image"})["content"]
    return {"title": title, "thumbnail": thumbnail}


async def process_video(video_id: str, language: str = "ko"):
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
    return youtube
