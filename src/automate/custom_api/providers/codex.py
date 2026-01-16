"""Codex Provider 구현"""

import asyncio
import shlex
from typing import List

from loguru import logger

from ..config import get_custom_api_settings
from ..models import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionResponse,
    ChatMessage,
    Usage,
)
from .base import BaseProvider


class CodexProvider(BaseProvider):
    """Codex Provider"""

    def __init__(self):
        """Codex Provider 초기화"""
        settings = get_custom_api_settings()
        super().__init__(model_name="codex")
        self.command = settings.CODEX_COMMAND
        self.timeout = settings.COMMAND_TIMEOUT


    async def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """Codex를 사용하여 Chat completion 생성

        Args:
            messages: 메시지 배열
            temperature: 샘플링 온도 (사용되지 않음)
            max_tokens: 최대 토큰 수 (사용되지 않음)
            **kwargs: 추가 파라미터

        Returns:
            ChatCompletionResponse
        """
        # 메시지를 프롬프트로 변환
        prompt = self._format_messages(messages)

        # Codex 명령어 구성
        # codex exec - 형식으로 실행 (stdin에서 프롬프트 읽기)
        command_parts = [self.command, "exec", "-"]
        # 프롬프트를 안전하게 전달하기 위해 stdin 사용
        command = " ".join(command_parts)

        logger.info(f"Codex 명령어 실행: {command}")

        try:
            # subprocess 실행
            process = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 프롬프트를 stdin으로 전송하고 결과 대기
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=prompt.encode("utf-8")),
                timeout=self.timeout,
            )

            stdout_text = stdout.decode("utf-8", errors="ignore") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="ignore") if stderr else ""

            if process.returncode != 0:
                error_msg = f"Codex 실행 실패 (반환 코드: {process.returncode})"
                if stderr_text:
                    error_msg += f"\n에러: {stderr_text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            # 응답 생성
            content = stdout_text.strip()

            # 토큰 사용량 추정
            prompt_tokens = self._estimate_tokens(prompt)
            completion_tokens = self._estimate_tokens(content)
            total_tokens = prompt_tokens + completion_tokens

            return ChatCompletionResponse(
                model=self.model_name,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatCompletionMessage(
                            role="assistant", content=content
                        ),
                        finish_reason="stop" if content else "error",
                    )
                ],
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                ),
            )

        except asyncio.TimeoutError:
            logger.error(f"Codex 실행 타임아웃 ({self.timeout}초)")
            raise RuntimeError(f"Codex 실행 타임아웃 ({self.timeout}초)")
        except Exception as e:
            logger.exception(f"Codex 실행 중 오류: {e}")
            raise
