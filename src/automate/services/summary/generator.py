"""AI 요약 생성"""

from typing import Dict, List

from openai import AsyncOpenAI
from loguru import logger

from ...core.config import get_settings
from .formatter import format_transcript
from .prompt import load_prompt


def estimate_tokens(text: str) -> int:
    """텍스트의 대략적인 토큰 수를 추정합니다.
    
    보수적으로 1 토큰 ≈ 3 문자로 추정합니다.
    
    Args:
        text: 토큰 수를 추정할 텍스트
        
    Returns:
        추정된 토큰 수
    """
    # 보수적인 추정: 한국어와 영어 혼합을 고려하여 1 토큰 ≈ 3 문자로 계산
    return len(text) // 3


def split_transcript(transcript: List[Dict], max_tokens: int) -> List[List[Dict]]:
    """대본을 토큰 제한에 맞춰 여러 청크로 분할합니다.
    
    Args:
        transcript: 분할할 대본 리스트
        max_tokens: 각 청크의 최대 토큰 수
        
    Returns:
        분할된 대본 청크 리스트
    """
    if not transcript:
        return []
    
    chunks: List[List[Dict]] = []
    current_chunk: List[Dict] = []
    current_tokens = 0
    
    for entry in transcript:
        entry_text = entry.get("text", "")
        entry_tokens = estimate_tokens(entry_text)
        
        # 현재 청크에 추가했을 때 제한을 초과하는지 확인
        if current_tokens + entry_tokens > max_tokens and current_chunk:
            # 현재 청크를 저장하고 새 청크 시작
            chunks.append(current_chunk)
            current_chunk = [entry]
            current_tokens = entry_tokens
        else:
            # 현재 청크에 추가
            current_chunk.append(entry)
            current_tokens += entry_tokens
    
    # 마지막 청크 추가
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


async def _summarize_chunk(
    chunk_transcript: List[Dict],
    system_prompt: str,
    model_name: str,
    chunk_index: int,
    total_chunks: int,
    client: AsyncOpenAI,
) -> str:
    """대본 청크 하나를 요약합니다.
    
    Args:
        chunk_transcript: 요약할 대본 청크
        system_prompt: 시스템 프롬프트
        model_name: 사용할 모델 이름
        chunk_index: 현재 청크 인덱스 (0부터 시작)
        total_chunks: 전체 청크 수
        
    Returns:
        요약된 텍스트
    """
    formatted_text = format_transcript(chunk_transcript)
    
    # 청크 정보를 포함한 프롬프트 생성
    chunk_info = f"\n\n[참고: 이것은 전체 대본의 {chunk_index + 1}/{total_chunks} 부분입니다.]"
    user_prompt = chunk_info + "\n\n---\n\n대본:\n" + formatted_text

    response = await client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


async def summarize(
    transcript: List[Dict],
    model_name: str | None = None,
) -> str:
    """
    OpenAI API를 사용하여 대본을 요약합니다. (비동기 실행)
    
    대본이 토큰 제한을 초과하는 경우 자동으로 분할하여 요약합니다.
    
    Args:
        transcript: 요약할 대본 리스트
        model_name: 사용할 모델 이름 (기본값: 설정에서 가져옴)
        
    Returns:
        요약된 내용
    """
    settings = get_settings()
    if model_name is None:
        model_name = settings.OPENAI_MODEL_NAME

    logger.info(f"대본 요약 시작 (모델: {model_name})")
    system_prompt_text = load_prompt()
    formatted_text = format_transcript(transcript)
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    safe_token_limit = max(settings.OPENAI_MAX_INPUT_TOKENS - 2000, 1)
    
    # 전체 프롬프트의 토큰 수 계산
    full_user_prompt = "\n\n---\n\n대본:\n" + formatted_text
    total_tokens = estimate_tokens(system_prompt_text + full_user_prompt)
    system_prompt_tokens = estimate_tokens(system_prompt_text)
    
    # 시스템 프롬프트를 제외한 대본만의 최대 토큰 수
    max_transcript_tokens = safe_token_limit - system_prompt_tokens
    
    logger.info(f"전체 토큰 수: {total_tokens}, 시스템 프롬프트 토큰: {system_prompt_tokens}")
    
    # 토큰 제한을 초과하지 않으면 일반 요약
    if total_tokens <= safe_token_limit:
        logger.info("토큰 제한 내 - 단일 요약 실행")
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt_text},
                {"role": "user", "content": full_user_prompt},
            ],
        )
        return response.choices[0].message.content or ""
    
    # 토큰 제한 초과 - 분할 요약
    logger.warning(
        f"토큰 제한 초과 ({total_tokens} > {safe_token_limit}) - 대본을 분할하여 요약합니다."
    )
    
    # 대본을 청크로 분할
    chunks = split_transcript(transcript, max_transcript_tokens)
    logger.info(f"대본을 {len(chunks)}개 청크로 분할했습니다.")
    
    # 각 청크를 요약
    chunk_summaries: List[str] = []
    for i, chunk in enumerate(chunks):
        logger.info(f"청크 {i + 1}/{len(chunks)} 요약 중...")
        chunk_summary = await _summarize_chunk(
            chunk, system_prompt_text, model_name, i, len(chunks), client
        )
        chunk_summaries.append(chunk_summary)
    
    # 모든 청크 요약을 합쳐서 최종 요약 생성
    logger.info("청크 요약들을 종합하여 최종 요약 생성 중...")
    combined_summaries = "\n\n---\n\n".join(
        [f"[{i+1}번째 부분 요약]\n{summary}" for i, summary in enumerate(chunk_summaries)]
    )
    
    # 최종 요약 프롬프트
    final_prompt = (
        "다음은 긴 대본을 여러 부분으로 나누어 요약한 결과입니다. "
        "이 요약들을 종합하여 전체 대본의 통합된 요약을 작성해주세요.\n\n"
        "각 부분의 요약:\n"
        f"{combined_summaries}\n\n"
        "위의 부분별 요약들을 바탕으로 전체 대본의 핵심 내용을 담은 통합 요약을 작성해주세요."
    )
    
    final_response = await client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "당신은 영상 대본 요약 전문가입니다."},
            {"role": "user", "content": final_prompt},
        ],
    )
    
    logger.info("최종 요약 완료")
    return final_response.choices[0].message.content or ""
