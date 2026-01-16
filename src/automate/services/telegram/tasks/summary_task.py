"""YouTube 요약 Task"""

import asyncio

from loguru import logger
from telegram import Update
from telegram.ext import Application

from automate.core.constants import TaskKind
from automate.utils.youtube_utils import extract_video_id
from .base import BaseTask


class ResourceExhaustedError(Exception):
    """429 에러 (Resource Exhausted)를 나타내는 예외 클래스"""

    pass


class SummaryTask(BaseTask):
    """YouTube 영상 요약 Task"""

    TASK_NAME = TaskKind.SUMMARY
    COMMAND_PREFIX = "요약|"

    async def parse_message(self, text: str, update: Update) -> str | None:
        """YouTube URL에서 video_id를 추출합니다."""
        video_id = extract_video_id(text)
        if not video_id:
            await update.message.reply_text("❌ 유효하지 않은 YouTube URL입니다.")
            return None
        return video_id

    async def execute(
        self,
        value: str,
        application: Application,
        chat_id: int | None = None,
        update: Update | None = None,
    ) -> None:
        """요약 작업을 실행합니다."""
        video_id = value
        try:
            logger.info(f"[WORKER] 처리 시작: {video_id}")
            await self.send_message(
                application, f"요약 처리 시작: {video_id}", chat_id=chat_id
            )

            # video_url = f'"https://www.youtube.com/watch?v={video_id}"'
            command = f"automate transcribe --video-id {video_id}"
            summary = await self._run_command(
                command, video_id, application, chat_id=chat_id
            )

            logger.info(f"[WORKER] 완료: {video_id}")
            await self.send_message(
                application, f"✅ 요약 처리 완료: {video_id}", chat_id=chat_id
            )

            # 요약 텍스트를 텔레그램으로 전송
            if summary:
                # 텔레그램 메시지 길이 제한 (4096자)을 고려하여 분할 전송
                await self._send_summary(
                    application, summary, video_id, chat_id=chat_id
                )
            else:
                logger.warning(f"요약 텍스트를 추출할 수 없습니다: {video_id}")

        except ResourceExhaustedError:
            # 429 에러 (Resource Exhausted) 처리 - 이미 _run_command에서 처리됨
            pass
        except Exception as err:
            logger.exception(f"[WORKER] 오류 발생: {video_id} - {err}")
            await self.send_message(
                application, f"❌ 처리 중 오류 발생: {video_id}", chat_id=chat_id
            )

    async def _send_summary(
        self,
        application: Application,
        summary: str,
        video_id: str,
        chat_id: int | None = None,
    ) -> None:
        """요약 텍스트를 텔레그램으로 전송합니다.

        텔레그램 메시지 길이 제한(4096자)을 고려하여 필요시 분할 전송합니다.

        Args:
            application: Telegram Application 객체
            summary: 전송할 요약 텍스트
            video_id: YouTube 비디오 ID
        """
        # 텔레그램 메시지 최대 길이 (안전 마진 포함)
        MAX_MESSAGE_LENGTH = 4000

        if len(summary) <= MAX_MESSAGE_LENGTH:
            # 한 번에 전송 가능한 경우
            message = f"📝 요약 내용:\n\n{summary}"
            await self.send_message(application, message, chat_id=chat_id)
        else:
            # 분할 전송
            logger.info(f"요약이 길어서 분할 전송합니다: {len(summary)}자")
            parts = self._split_text(summary, MAX_MESSAGE_LENGTH)

            for i, part in enumerate(parts, 1):
                message = f"📝 요약 내용 ({i}/{len(parts)}):\n\n{part}"
                await self.send_message(application, message, chat_id=chat_id)
                # 메시지 간 짧은 지연 (rate limit 방지)
                if i < len(parts):  # 마지막 메시지가 아니면 지연
                    await asyncio.sleep(0.5)

    def _split_text(self, text: str, max_length: int) -> list[str]:
        """텍스트를 지정된 길이로 분할합니다.

        문장 단위로 분할하여 자연스럽게 나눕니다.

        Args:
            text: 분할할 텍스트
            max_length: 각 부분의 최대 길이

        Returns:
            분할된 텍스트 리스트
        """
        if len(text) <= max_length:
            return [text]

        parts: list[str] = []
        current_part = ""

        # 문장 단위로 분할 (줄바꿈 또는 마침표 기준)
        sentences = text.split("\n\n")  # 단락 단위로 먼저 분할

        for sentence in sentences:
            # 현재 부분에 문장을 추가했을 때 길이 확인
            test_part = current_part + ("\n\n" if current_part else "") + sentence

            if len(test_part) <= max_length:
                current_part = test_part
            else:
                # 현재 부분을 저장하고 새 부분 시작
                if current_part:
                    parts.append(current_part)
                current_part = sentence

                # 문장 자체가 너무 긴 경우 강제로 분할
                if len(current_part) > max_length:
                    # 문장을 강제로 분할
                    while len(current_part) > max_length:
                        parts.append(current_part[:max_length])
                        current_part = current_part[max_length:]

        # 마지막 부분 추가
        if current_part:
            parts.append(current_part)

        return parts

    async def _run_command(
        self,
        command: str,
        video_id: str,
        application: Application,
        chat_id: int | None = None,
    ) -> str | None:
        """명령어를 실행하고 요약 텍스트를 반환합니다.

        Args:
            command: 실행할 명령어
            video_id: YouTube 비디오 ID (에러 처리용)
            application: Telegram Application 객체 (에러 처리용)

        Returns:
            추출된 요약 텍스트 또는 None (요약을 찾을 수 없는 경우)

        Raises:
            ResourceExhaustedError: 429 에러가 발생한 경우
            RuntimeError: 명령어 실행이 실패한 경우 (반환 코드가 0이 아님)
        """
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""

        logger.debug(f"명령어 실행 결과 - 반환 코드: {process.returncode}")
        if stdout_text:
            logger.debug(f"STDOUT:\n{stdout_text}")
        if stderr_text:
            logger.debug(f"STDERR:\n{stderr_text}")

        # 429 에러 감지 (stdout 또는 stderr에 429 또는 RESOURCE_EXHAUSTED가 포함된 경우)
        combined_output = f"{stdout_text}\n{stderr_text}"
        if (
            "429" in combined_output
            or "RESOURCE_EXHAUSTED" in combined_output
            or "Resource exhausted" in combined_output
        ):
            logger.warning(
                f"[WORKER] 429 에러 발생 (리소스 소진): {video_id} - 10분 후 재시도 예약"
            )
            await self.send_message(
                application,
                f"❌ 처리 중 오류 발생 (리소스 소진): {video_id}\n⏳ 10분 후 자동 재시도 예약됨",
                chat_id=chat_id,
            )
            # 10분(600초) 후에 Task를 다시 큐에 추가
            await self._schedule_retry(
                video_id, application, chat_id=chat_id, delay_seconds=600
            )
            raise ResourceExhaustedError(f"429 에러 발생: {video_id}")

        # 반환 코드가 0이 아니면 에러로 처리
        if process.returncode != 0:
            error_msg = f"명령어 실행 실패 (반환 코드: {process.returncode})"
            if stderr_text:
                error_msg += f"\n에러 출력:\n{stderr_text}"
            raise RuntimeError(error_msg)

        # stdout에서 요약 텍스트 추출
        summary = self._extract_summary_from_output(stdout_text)
        return summary

    def _extract_summary_from_output(self, output: str) -> str | None:
        """명령어 출력에서 요약 텍스트를 추출합니다.

        Args:
            output: 명령어의 stdout 출력

        Returns:
            추출된 요약 텍스트 또는 None
        """
        if not output:
            return None

        # "📝 요약 내용:" 다음의 "=" * 50 사이의 내용 추출
        lines = output.split("\n")
        summary_start_marker = "📝 요약 내용:"
        separator = "=" * 50

        try:
            # 요약 시작 마커 찾기
            start_idx = None
            for i, line in enumerate(lines):
                if summary_start_marker in line:
                    start_idx = i + 1
                    break

            if start_idx is None:
                logger.warning("요약 시작 마커를 찾을 수 없습니다.")
                return None

            # 첫 번째 구분선 찾기
            first_separator_idx = None
            for i in range(start_idx, len(lines)):
                if lines[i].strip() == separator:
                    first_separator_idx = i
                    break

            if first_separator_idx is None:
                logger.warning("첫 번째 구분선을 찾을 수 없습니다.")
                return None

            # 두 번째 구분선 찾기
            second_separator_idx = None
            for i in range(first_separator_idx + 1, len(lines)):
                if lines[i].strip() == separator:
                    second_separator_idx = i
                    break

            if second_separator_idx is None:
                logger.warning("두 번째 구분선을 찾을 수 없습니다.")
                # 구분선이 하나만 있어도 요약 추출 시도
                summary_lines = lines[first_separator_idx + 1 :]
            else:
                summary_lines = lines[first_separator_idx + 1 : second_separator_idx]

            summary = "\n".join(summary_lines).strip()
            return summary if summary else None

        except Exception as e:
            logger.warning(f"요약 추출 중 오류 발생: {e}")
            return None

    async def _schedule_retry(
        self,
        video_id: str,
        application: Application,
        chat_id: int | None = None,
        delay_seconds: int = 600,
    ) -> None:
        """지정된 시간 후에 Task를 다시 큐에 추가합니다.

        Args:
            video_id: YouTube 비디오 ID
            application: Telegram Application 객체
            delay_seconds: 재시도까지 대기할 시간 (초, 기본값: 600 = 10분)
        """
        from ..bot import QueuedTask, task_queue

        async def _retry_task():
            """지정된 시간 후에 Task를 큐에 추가하는 내부 함수"""
            await asyncio.sleep(delay_seconds)
            from automate.core.config import get_settings

            settings = get_settings()
            target_chat_id = (
                chat_id if chat_id is not None else settings.channel_chat_id_int
            )
            await task_queue.put(
                QueuedTask(
                    task_name=self.TASK_NAME, value=video_id, chat_id=target_chat_id
                )
            )
            logger.info(f"[WORKER] 재시도 Task 큐에 추가: {video_id} (10분 후)")
            await self.send_message(
                application, f"🔄 재시도 시작: {video_id}", chat_id=chat_id
            )

        # 백그라운드에서 재시도 태스크 실행
        asyncio.create_task(_retry_task())
