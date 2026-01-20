"""Codex Provider 구현"""

import asyncio
import os
import re
import shlex
import tempfile
from pathlib import Path

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
        messages: list[ChatMessage],
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
        provider_name = type(self).__name__
        logger.info(
            f"CodexProvider.chat_completion() 호출됨 - "
            f"Provider: {provider_name}, Model: {self.model_name}"
        )

        # 메시지를 프롬프트로 변환
        prompt = self._format_messages(messages)

        # 임시 파일 경로 생성
        temp_dir = Path(tempfile.gettempdir())
        output_file = temp_dir / f"codex_output_{os.getpid()}_{asyncio.get_event_loop().time()}.md"
        output_file_str = str(output_file)

        # 프롬프트에 파일 저장 요청 추가
        enhanced_prompt = f"{prompt}\n\n결과를 '{output_file_str}' 파일에 저장해줘."

        # Codex 명령어 구성
        # codex exec --model gpt-5.2 --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox [PROMPT]
        command_parts = [
            self.command,
            "exec",
            "--model", "gpt-5.2",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            shlex.quote(enhanced_prompt),  # 프롬프트를 stdin 아니라 직접 인자에 전달
        ]
        command = " ".join(command_parts)

        logger.info(f"Codex 명령어 실행: {command}")
        logger.debug(f"출력 파일 경로: {output_file_str}")
        logger.debug(f"프롬프트(인자): {enhanced_prompt:200}")
        try:
            # subprocess 실행 (더 이상 stdin 사용하지 않음)
            process = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 결과 대기 (stdin 인풋 없음)
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
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

            # 파일이 생성되었는지 확인하고 읽기
            content = ""
            if output_file.exists():
                logger.info(f"출력 파일 발견: {output_file_str}")
                try:
                    content = await asyncio.to_thread(output_file.read_text, encoding="utf-8")
                    logger.info(f"파일에서 내용 읽기 완료: {len(content)}자")
                    # 파일 삭제 (정리)
                    try:
                        output_file.unlink()
                        logger.debug(f"임시 파일 삭제: {output_file_str}")
                    except Exception as e:
                        logger.warning(f"임시 파일 삭제 실패: {e}")
                except Exception as e:
                    logger.warning(f"파일 읽기 실패: {e}, stdout 사용")
                    content = stdout_text.strip()
            else:
                # 파일이 없으면 stdout에서 파일 경로 추출 시도
                logger.info("출력 파일이 없습니다. stdout에서 파일 경로 추출 시도")
                file_paths = self._extract_file_paths(stdout_text)
                if file_paths:
                    # 첫 번째 파일 경로 시도
                    for file_path in file_paths:
                        path = Path(file_path)
                        if path.exists():
                            logger.info(f"추출된 파일 경로에서 읽기: {file_path}")
                            try:
                                content = await asyncio.to_thread(path.read_text, encoding="utf-8")
                                logger.info(f"파일에서 내용 읽기 완료: {len(content)}자")
                                break
                            except Exception as e:
                                logger.warning(f"파일 읽기 실패 ({file_path}): {e}")
                                continue

                # 파일을 찾지 못한 경우 stdout 사용
                if not content:
                    logger.info("파일을 찾지 못했습니다. stdout 사용")
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
            logger.error(f"Codex 실행 타임아웃 ({self.timeout}초)")
            raise RuntimeError(f"Codex 실행 타임아웃 ({self.timeout}초)") from err
        except Exception as e:
            logger.exception(f"Codex 실행 중 오류: {e}")
            raise

    def _extract_file_paths(self, text: str) -> list[str]:
        """텍스트에서 파일 경로를 추출합니다.

        Args:
            text: 파일 경로를 추출할 텍스트

        Returns:
            추출된 파일 경로 리스트
        """
        # 일반적인 파일 경로 패턴 (Windows 및 Unix 경로)
        # 지원 파일 확장자
        ext_pattern = r"(?:md|txt|json|py|js|ts|html|css|yaml|yml)"
        patterns = [
            # 따옴표로 감싸진 파일 경로
            rf'["\']([^"\']+\.{ext_pattern})["\']',
            # Windows 절대 경로
            rf"([A-Za-z]:[\\/][^\s\n]+\.{ext_pattern})",
            # Unix 절대 경로
            rf"(/[^\s\n]+\.{ext_pattern})",
            # 상대 경로
            rf"([^\s\n]+\.{ext_pattern})",
        ]

        file_paths: list[str] = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            file_paths.extend(matches)

        # 중복 제거 및 정리
        unique_paths = list(dict.fromkeys(file_paths))
        return unique_paths
