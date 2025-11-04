"""상수 정의"""

from dataclasses import dataclass


class CmdPrefix:
    """텔레그램 봇 명령어 접두사"""

    SUMMARY = "요약|"
    SHORTS = "쇼츠|"


class WebHook:
    """Webhook URL 상수"""

    shorts = "http://pringles.iptime.org/webhook/eb917575-b39f-4197-b867-f0fcd72aaac6"
    summary = "http://pringles.iptime.org/webhook/e171b96e-3318-4cba-a2b9-60f9b353d406"


class TaskKind:
    """작업 종류"""

    SUMMARY = "summary"
    SHORTS = "shorts"


@dataclass
class Task:
    """작업 데이터 클래스"""

    kind: str
    value: str
