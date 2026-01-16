"""OpenAI Provider 구현"""

from loguru import logger
from openai import AsyncOpenAI

from ...core.config import get_settings
from ..models import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionResponse,
    ChatMessage,
    Usage,
)
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI Provider"""

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        """OpenAI Provider 초기화

        Args:
            model_name: 모델 이름 (기본값: 설정에서 가져옴)
            api_key: API 키 (기본값: 설정에서 가져옴)
        """
        settings = get_settings()
        if model_name is None:
            model_name = settings.OPENAI_MODEL_NAME
        if api_key is None:
            api_key = settings.OPENAI_API_KEY

        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

        super().__init__(model_name=model_name)
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key)

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """OpenAI API를 사용하여 Chat completion 생성

        Args:
            messages: 메시지 배열
            temperature: 샘플링 온도
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터

        Returns:
            ChatCompletionResponse
        """
        provider_name = type(self).__name__
        logger.info(f"OpenAIProvider.chat_completion() 호출됨 - Provider: {provider_name}, Model: {self.model_name}")
        
        try:
            # ChatMessage를 OpenAI 형식으로 변환
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            # OpenAI API 호출
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # 응답을 ChatCompletionResponse로 변환
            choice = response.choices[0]
            content = choice.message.content or ""

            return ChatCompletionResponse(
                model=response.model,
                choices=[
                    ChatCompletionChoice(
                        index=choice.index,
                        message=ChatCompletionMessage(
                            role="assistant", content=content
                        ),
                        finish_reason=choice.finish_reason or "stop",
                    )
                ],
                usage=Usage(
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens
                    if response.usage
                    else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                )
                if response.usage
                else None,
            )

        except Exception as e:
            logger.exception(f"OpenAI API 호출 중 오류: {e}")
            raise RuntimeError(f"OpenAI API 호출 실패: {e}")
