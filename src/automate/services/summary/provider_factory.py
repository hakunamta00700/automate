"""AI Provider 팩토리"""

from typing import Literal

from loguru import logger

from ...core.config import get_settings
from ...custom_api.providers import (
    BaseProvider,
    CodexProvider,
    CursorProvider,
    GeminiProvider,
    OpenAIProvider,
    OpenCodeProvider,
)

ProviderType = Literal["openai", "codex", "opencode", "gemini", "cursor"]


def create_provider(provider_type: str | None = None) -> BaseProvider:
    """설정 기반으로 AI Provider 인스턴스를 생성합니다.

    Args:
        provider_type: Provider 타입 (기본값: 설정에서 가져옴)
                      지원 타입: "openai", "codex", "opencode", "gemini", "cursor"

    Returns:
        BaseProvider 인스턴스

    Raises:
        ValueError: 지원하지 않는 Provider 타입인 경우
    """
    settings = get_settings()

    # Provider 타입 결정 (설정 또는 인자)
    if provider_type is None:
        # .env 파일에서 AI_PROVIDER를 가져오고, 없으면 기본값 "codex" 사용
        provider_type = settings.AI_PROVIDER or "codex"
        logger.debug(f".env에서 AI_PROVIDER 읽음: {provider_type}")

    provider_type = provider_type.lower()

    # Provider 타입에 따라 인스턴스 생성
    if provider_type == "openai":
        provider = OpenAIProvider()
    elif provider_type == "codex":
        provider = CodexProvider()
    elif provider_type == "opencode":
        provider = OpenCodeProvider()
    elif provider_type == "gemini":
        provider = GeminiProvider()
    elif provider_type == "cursor":
        provider = CursorProvider()
    else:
        raise ValueError(
            f"지원하지 않는 Provider 타입: {provider_type}. "
            f"지원 타입: openai, codex, opencode, gemini, cursor"
        )

    provider_name = type(provider).__name__
    logger.info(
        f"AI Provider 생성 완료 - Type: {provider_type}, Provider: {provider_name}, Model: {provider.model_name}"
    )

    return provider
