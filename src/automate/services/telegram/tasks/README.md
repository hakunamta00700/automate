# Task 추가 가이드

새로운 Task를 추가하려면 이 디렉토리에 새로운 파일을 만들고 `BaseTask`를 상속받는 클래스를 작성하면 됩니다.

## 예시

```python
"""새로운 Task 예시"""

from loguru import logger
from telegram import Update
from telegram.ext import Application

from .base import BaseTask


class ExampleTask(BaseTask):
    """예시 Task"""
    
    # 필수: Task 고유 이름
    TASK_NAME = "example"
    
    # 필수: 명령어 접두사 (예: "예시|" 형식)
    COMMAND_PREFIX = "예시|"
    
    async def parse_message(self, text: str, update: Update) -> str | None:
        """
        메시지를 파싱하여 Task 값(value)을 추출합니다.
        
        Args:
            text: 파싱할 텍스트 (COMMAND_PREFIX 제외)
            update: Telegram Update 객체
            
        Returns:
            Task 값 문자열 또는 None (파싱 실패 시)
        """
        # 여기에 파싱 로직 작성
        parsed_value = text.strip()
        
        if not parsed_value:
            await update.message.reply_text("❌ 유효하지 않은 값입니다.")
            return None
        
        return parsed_value
    
    async def execute(
        self, value: str, application: Application, update: Update | None = None
    ) -> None:
        """
        Task를 실행합니다.
        
        Args:
            value: Task 값 (parse_message에서 추출된 값)
            application: Telegram Application 객체
            update: Telegram Update 객체 (선택사항)
        """
        try:
            logger.info(f"[WORKER] 처리 시작: {value}")
            await self.send_message(application, f"처리 시작: {value}")
            
            # 여기에 실제 작업 로직 작성
            # ...
            
            logger.info(f"[WORKER] 완료: {value}")
            await self.send_message(application, f"✅ 처리 완료: {value}")
        except Exception as e:
            logger.exception(f"[WORKER] 오류 발생: {value}")
            await self.send_message(application, f"❌ 처리 중 오류 발생: {value} - {e}")
```

## 사용 방법

1. 위 예시를 참고하여 새로운 파일을 만듭니다 (예: `example_task.py`)
2. `BaseTask`를 상속받는 클래스를 작성합니다
3. `TASK_NAME`과 `COMMAND_PREFIX`를 정의합니다
4. `parse_message`와 `execute` 메서드를 구현합니다
5. 파일을 저장하면 자동으로 등록됩니다

## 주의사항

- `TASK_NAME`은 고유해야 합니다 (중복 시 경고가 발생하고 무시됩니다)
- `COMMAND_PREFIX`는 "명령어|" 형식이어야 합니다
- `parse_message`에서 파싱 실패 시 `None`을 반환하고 에러 메시지를 보내야 합니다
- `execute`에서 예외 발생 시 적절히 처리하고 로그를 남겨야 합니다

