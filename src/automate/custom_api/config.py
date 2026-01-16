"""Custom API 설정 관리"""

import os
import shutil
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


def _find_codex_command() -> str:
    """Codex 명령어 경로를 자동으로 찾습니다.

    환경 변수 CODEX_COMMAND가 설정되지 않은 경우에만 호출됩니다.

    Returns:
        Codex 명령어 경로 또는 "codex" (기본값)
    """
    # 일반적인 경로들 확인
    common_paths = [
        "/home/ubuntu/.npm-global/bin/codex",  # Ubuntu npm global 설치 경로
        os.path.expanduser("~/.npm-global/bin/codex"),  # 사용자 npm global 경로
        "/usr/local/bin/codex",  # 시스템 경로
        shutil.which("codex"),  # PATH에서 찾기
    ]

    for path in common_paths:
        if path and Path(path).exists():
            return path

    # 찾지 못한 경우 기본값 반환
    return "codex"


class CustomAPISettings:
    """Custom API 설정"""

    # 명령어 설정
    CODEX_COMMAND: str = os.getenv("CODEX_COMMAND", _find_codex_command())
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
