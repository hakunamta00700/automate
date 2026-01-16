"""설정 관리 모듈"""

import os
from typing import Optional

from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class Settings:
    """애플리케이션 설정"""

    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Airtable
    AIRTABLE_API_KEY: Optional[str] = os.getenv("AIRTABLE_API_KEY")
    AIRTABLE_BASE_NAME: Optional[str] = os.getenv("AIRTABLE_BASE_NAME")
    AIRTABLE_TABLE_NAME: Optional[str] = os.getenv("AIRTABLE_TABLE_NAME")

    # Telegram
    BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
    CHANNEL_CHAT_ID: Optional[str] = os.getenv("CHANNEL_CHAT_ID", "431464720")

    # Webhook
    WEBHOOK_DOMAIN: Optional[str] = os.getenv("WEBHOOK_DOMAIN")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")

    # OpenAI
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")
    OPENAI_MAX_INPUT_TOKENS: int = int(os.getenv("OPENAI_MAX_INPUT_TOKENS", "128000"))

    # AI Provider 설정
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "codex")

    # GitHub
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_OWNER: Optional[str] = os.getenv("GITHUB_OWNER")
    GITHUB_REPO: Optional[str] = os.getenv("GITHUB_REPO")

    # Custom API
    CODEX_COMMAND: str = os.getenv("CODEX_COMMAND", "codex")
    OPENCODE_COMMAND: str = os.getenv("OPENCODE_COMMAND", "opencode")
    CURSOR_COMMAND: str = os.getenv("CURSOR_COMMAND", "cursor")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    CUSTOM_API_HOST: str = os.getenv("CUSTOM_API_HOST", "0.0.0.0")
    CUSTOM_API_PORT: int = int(os.getenv("CUSTOM_API_PORT", "8001"))
    CUSTOM_API_TIMEOUT: int = int(os.getenv("CUSTOM_API_TIMEOUT", "300"))

    @property
    def webhook_url(self) -> str:
        """Webhook 전체 URL 반환"""
        if not self.WEBHOOK_DOMAIN:
            raise ValueError("WEBHOOK_DOMAIN is not set")
        return f"http://{self.WEBHOOK_DOMAIN}{self.WEBHOOK_PATH}"

    @property
    def bot_token_str(self) -> str:
        """Bot Token을 문자열로 반환"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set")
        return str(self.BOT_TOKEN)

    @property
    def channel_chat_id_int(self) -> int:
        """Channel Chat ID를 정수로 반환"""
        return int(self.CHANNEL_CHAT_ID)

    def validate_required(self, required_vars: list[str]) -> None:
        """필수 환경 변수 검증"""
        missing = [var for var in required_vars if not getattr(self, var, None)]
        if missing:
            raise ValueError(
                f"다음 환경 변수들이 설정되지 않았습니다: {', '.join(missing)}\n"
                ".env 파일을 확인해주세요."
            )

    def get_required_env_vars(self) -> list[str]:
        """필수 환경 변수 목록 반환"""
        return [
            "OPENAI_API_KEY",
            "AIRTABLE_API_KEY",
            "AIRTABLE_BASE_NAME",
            "AIRTABLE_TABLE_NAME",
            "BOT_TOKEN",
            "WEBHOOK_DOMAIN",
            "WEBHOOK_PATH",
        ]


# 전역 설정 인스턴스
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """설정 인스턴스 반환 (싱글톤 패턴)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
