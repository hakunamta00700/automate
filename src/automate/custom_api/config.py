"""Custom API 설정 관리"""

import os
from typing import Optional

from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class CustomAPISettings:
    """Custom API 설정"""

    # 명령어 설정
    CODEX_COMMAND: str = os.getenv("CODEX_COMMAND", "codex")
    OPENCODE_COMMAND: str = os.getenv("OPENCODE_COMMAND", "opencode")
    CURSOR_COMMAND: str = os.getenv("CURSOR_COMMAND", "cursor")

    # Gemini 설정
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

    # 서버 설정
    CUSTOM_API_HOST: str = os.getenv("CUSTOM_API_HOST", "0.0.0.0")
    CUSTOM_API_PORT: int = int(os.getenv("CUSTOM_API_PORT", "8001"))

    # 타임아웃 설정 (초)
    COMMAND_TIMEOUT: int = int(os.getenv("CUSTOM_API_TIMEOUT", "300"))


# 전역 설정 인스턴스
_settings: Optional[CustomAPISettings] = None


def get_custom_api_settings() -> CustomAPISettings:
    """Custom API 설정 인스턴스 반환 (싱글톤 패턴)"""
    global _settings
    if _settings is None:
        _settings = CustomAPISettings()
    return _settings
