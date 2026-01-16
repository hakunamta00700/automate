"""AI Provider 팩토리"""

from typing import Literal

from loguru import logger

from ...core.config import get_settings
from ...custom_api.providers import (
    BaseProvider,
    CodexProvider,
    CursorProvider,
    GeminiProvider,
    OpenCodeProvider,
    OpenAIProvider,
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
        # 환경 변수에서 Provider 타입 가져오기 (기본값: openai)
        provider_type = getattr(settings, "AI_PROVIDER", "openai")

    provider_type = provider_type.lower()

    logger.info(f"AI Provider 생성: {provider_type}")

    # Provider 타입에 따라 인스턴스 생성
    if provider_type == "openai":
        return OpenAIProvider()
    elif provider_type == "codex":
        return CodexProvider()
    elif provider_type == "opencode":
        return OpenCodeProvider()
    elif provider_type == "gemini":
        return GeminiProvider()
    elif provider_type == "cursor":
        return CursorProvider()
    else:
        raise ValueError(
            f"지원하지 않는 Provider 타입: {provider_type}. "
            f"지원 타입: openai, codex, opencode, gemini, cursor"
        )
