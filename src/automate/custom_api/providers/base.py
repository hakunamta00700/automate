"""AI Provider 추상 베이스 클래스"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List

from ..models import ChatCompletionResponse, ChatMessage


class BaseProvider(ABC):
    """AI Provider 추상 베이스 클래스"""

    def __init__(self, model_name: str):
        """Provider 초기화

        Args:
            model_name: 모델 이름
        """
        self.model_name = model_name

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """Chat completion 생성

        Args:
            messages: 메시지 배열
            temperature: 샘플링 온도
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터

        Returns:
            ChatCompletionResponse
        """
        raise NotImplementedError

    async def stream_chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatCompletionResponse]:
        """스트리밍 Chat completion 생성

        Args:
            messages: 메시지 배열
            temperature: 샘플링 온도
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터

        Yields:
            ChatCompletionResponse 청크
        """
        # 기본 구현: 비스트리밍 응답을 한 번에 반환
        response = await self.chat_completion(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        yield response

    def _format_messages(self, messages: List[ChatMessage]) -> str:
        """메시지 배열을 프롬프트 문자열로 변환

        Args:
            messages: 메시지 배열

        Returns:
            포맷된 프롬프트 문자열
        """
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                parts.append(f"Assistant: {msg.content}")

        return "\n\n".join(parts)

    def _estimate_tokens(self, text: str) -> int:
        """텍스트의 대략적인 토큰 수를 추정

        Args:
            text: 토큰 수를 추정할 텍스트

        Returns:
            추정된 토큰 수
        """
        # 보수적인 추정: 1 토큰 ≈ 3 문자
        return len(text) // 3
