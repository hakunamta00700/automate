"""AI 요약 생성"""

from typing import Dict, List

import google.genai as genai
import google.genai.types as types
from loguru import logger

from ...core.config import get_settings
from .formatter import format_transcript
from .prompt import load_prompt


async def summarize(
    transcript: List[Dict],
    model_name: str | None = None,
) -> str:
    """
    Gemini API를 사용하여 대본을 요약합니다. (비동기 실행)
    """
    settings = get_settings()
    if model_name is None:
        model_name = settings.GEMINI_MODEL_NAME

    logger.info(f"대본 요약 시작 (모델: {model_name})")
    formatted_text = format_transcript(transcript)

    system_prompt_text = load_prompt()
    prompt = system_prompt_text + "\n\n---\n\n대본:\n" + formatted_text

    client = genai.Client()
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT"],
        ),
    )
    return response.text
