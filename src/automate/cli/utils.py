"""CLI 공통 유틸리티"""


from ..core.config import get_settings


def check_env_vars(required_vars: list[str] | None = None) -> None:
    """필수 환경 변수가 설정되어 있는지 확인합니다."""
    settings = get_settings()
    if required_vars is None:
        required_vars = settings.get_required_env_vars()
    settings.validate_required(required_vars)
