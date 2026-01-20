"""Custom API background tasks.

이 패키지의 목적:
- Huey consumer(= `automate worker`)가 시작될 때 task들이 자동으로 등록되도록
  task 모듈들을 import 합니다.

주의:
- task 데코레이터가 적용된 함수는 import 시점에 Huey 인스턴스에 등록됩니다.
"""

from __future__ import annotations

# Task 등록을 보장하기 위한 import
from . import upload_markdown as upload_markdown  # noqa: F401

