import os
from typing import Dict, List

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatGoogleGenerativeAI

from .async_lib import to_async

TARGET_LLM_MODEL = os.getenv("TARGET_LLM_MODEL", "openai")


def format_transcript(transcript: List[Dict]) -> str:
    """대본 리스트를 하나의 문자열로 변환합니다."""
    return " ".join([entry["text"] for entry in transcript])


from loguru import logger

def get_llm(model_name: str, api_key: str = None):
    logger.info(f"LLM 모델 초기화: {model_name}")
    if model_name == "openai":
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            logger.debug("OpenAI API 키를 환경변수에서 로드")
        return ChatOpenAI(openai_api_key=api_key, model="gpt-4o")
    elif model_name == "gemini":
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY") 
            logger.debug("Gemini API 키를 환경변수에서 로드")
        return ChatGoogleGenerativeAI(google_api_key=api_key)
    else:
        logger.error(f"지원하지 않는 모델: {model_name}")
        raise ValueError("지원하지 않는 모델입니다. (openai, gemini만 지원)")


@to_async
def summarize(
    transcript: List[Dict], model_name: str = "openai", api_key: str = None
) -> str:
    """
    OpenAI 또는 Gemini API를 사용하여 대본을 요약합니다.
    """
    logger.info(f"대본 요약 시작 (모델: {model_name})")
    formatted_text = format_transcript(transcript)

    system_prompt = """
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
"""
    prompt = PromptTemplate(
        input_variables=["transcript"],
        template=system_prompt + "\n\n---\n\n{transcript}",
    )
    llm = get_llm(TARGET_LLM_MODEL, api_key)
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(transcript=formatted_text)
    return result
