"""Gemini Provider 구현"""

import asyncio
import shlex

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


class GeminiProvider(BaseProvider):
    """Gemini Provider"""

    def __init__(self):
        """Gemini Provider 초기화"""
        settings = get_custom_api_settings()
        super().__init__(model_name="gemini")
        self.api_key = settings.GEMINI_API_KEY
        self.timeout = settings.COMMAND_TIMEOUT

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """Gemini를 사용하여 Chat completion 생성

        Args:
            messages: 메시지 배열
            temperature: 샘플링 온도
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터

        Returns:
            ChatCompletionResponse
        """
        provider_name = type(self).__name__
        logger.info(
            f"GeminiProvider.chat_completion() 호출됨 - "
            f"Provider: {provider_name}, Model: {self.model_name}"
        )

        # API 키가 있으면 API 사용, 없으면 CLI 사용
        if self.api_key:
            return await self._chat_completion_api(messages, temperature, max_tokens, **kwargs)
        else:
            return await self._chat_completion_cli(messages, temperature, max_tokens, **kwargs)

    async def _chat_completion_api(
        self,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int | None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """Gemini API를 사용하여 Chat completion 생성"""
        logger.info("GeminiProvider: API 모드 사용")
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-pro")

            # 메시지를 프롬프트로 변환
            prompt = self._format_messages(messages)

            # Generation config 설정
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # API 호출
            response = await asyncio.to_thread(
                model.generate_content, prompt, generation_config=generation_config
            )

            content = response.text

            # 토큰 사용량 추정
            prompt_tokens = self._estimate_tokens(prompt)
            completion_tokens = self._estimate_tokens(content)
            total_tokens = prompt_tokens + completion_tokens

            return ChatCompletionResponse(
                model=self.model_name,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatCompletionMessage(role="assistant", content=content),
                        finish_reason="stop" if content else "error",
                    )
                ],
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                ),
            )

        except ImportError:
            logger.warning(
                "google-generativeai 패키지가 설치되지 않았습니다. CLI 모드로 전환합니다."
            )
            return await self._chat_completion_cli(messages, temperature, max_tokens, **kwargs)
        except Exception as e:
            logger.exception(f"Gemini API 호출 중 오류: {e}")
            raise RuntimeError(f"Gemini API 호출 실패: {e}") from e

    async def _chat_completion_cli(
        self,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int | None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """Gemini CLI를 사용하여 Chat completion 생성

        주의: Gemini CLI 사용법은 공식 문서에서 명확하지 않습니다.
        이 메서드는 API 키가 없을 때 fallback으로 사용됩니다.
        실제 환경에 맞는 CLI 명령어가 있다면 설정에서 커스터마이징하거나
        이 메서드를 수정해야 할 수 있습니다.
        """
        logger.info("GeminiProvider: CLI 모드 사용")
        # 메시지를 프롬프트로 변환
        prompt = self._format_messages(messages)

        # Gemini CLI 명령어 구성
        # 주의: Gemini CLI의 실제 사용법은 환경에 따라 다를 수 있습니다.
        # 현재는 예시 명령어로 구현되어 있으며, 실제 CLI 도구가 있다면
        # 환경 변수나 설정을 통해 명령어를 커스터마이징할 수 있습니다.
        # stdin에서 프롬프트를 읽도록 구현되어 있습니다.
        command = "gemini chat"

        logger.info(f"Gemini CLI 명령어 실행: {command}")

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
                error_msg = f"Gemini CLI 실행 실패 (반환 코드: {process.returncode})"
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
                        message=ChatCompletionMessage(role="assistant", content=content),
                        finish_reason="stop" if content else "error",
                    )
                ],
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                ),
            )

        except TimeoutError as err:
            logger.error(f"Gemini CLI 실행 타임아웃 ({self.timeout}초)")
            raise RuntimeError(f"Gemini CLI 실행 타임아웃 ({self.timeout}초)") from err
        except Exception as e:
            logger.exception(f"Gemini CLI 실행 중 오류: {e}")
            raise
