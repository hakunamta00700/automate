import os
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from pyairtable import Api
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

def get_transcript(video_id: str) -> List[Dict]:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return transcript

def format_transcript(transcript: List[Dict]) -> str:
    """대본 리스트를 하나의 문자열로 변환합니다."""
    return " ".join([entry["text"] for entry in transcript])

def summarize(transcript: List[Dict]) -> str:
    """OpenAI API를 사용하여 대본을 요약합니다."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    formatted_text = format_transcript(transcript)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "YouTube 영상의 대본을 간단하게 요약해주세요."},
            {"role": "user", "content": formatted_text}
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content

def save_to_airtable(video_id: str, summary: str) -> None:
    """요약된 내용을 Airtable에 저장합니다."""
    airtable = Api(os.getenv("AIRTABLE_API_KEY"))
    table = airtable.table(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_TABLE_NAME"))
    
    record = {
        "video_id": video_id,
        "summary": summary
    }
    
    table.create(record)

def process_video(video_id: str) -> str:
    """비디오 처리의 전체 과정을 실행합니다."""
    # 대본 가져오기
    transcript = get_transcript(video_id)
    
    # 대본 요약
    summary = summarize(transcript)
    
    # Airtable에 저장
    save_to_airtable(video_id, summary)
    
    return summary