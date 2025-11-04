"""텔레그램 풀링 봇"""

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from ...core.config import get_settings
from .tasks import get_task_by_command_prefix

if TYPE_CHECKING:
    from telegram.ext import Application

# 전역 큐
task_queue = asyncio.Queue()


@dataclass
class QueuedTask:
    """큐에 들어갈 Task 정보"""

    task_name: str
    value: str


async def worker(application: "Application") -> None:
    """작업 처리 워커"""
    from .tasks import get_task_by_name

    while True:
        try:
            queued_task: QueuedTask = await task_queue.get()
            task_cls = get_task_by_name(queued_task.task_name)

            if not task_cls:
                logger.error(f"[WORKER] 등록되지 않은 Task: {queued_task.task_name}")
                continue

            # Task 인스턴스 생성 및 실행
            task_instance = task_cls()
            await task_instance.execute(queued_task.value, application)

        except Exception as e:
            logger.exception(f"[WORKER] 작업 처리 중 오류: {e}")
            try:
                # 에러 메시지 전송을 위한 헬퍼 함수
                from ...core.config import get_settings

                settings = get_settings()
                await application.bot.send_message(
                    chat_id=settings.channel_chat_id_int, text=f"❌ 워커 오류: {e}"
                )
            except Exception:
                pass
        finally:
            task_queue.task_done()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """메시지 핸들러"""
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        logger.info(f"Received message: {text}")

        if "|" not in text:
            logger.info(f"무시된 메시지: {text}")
            return

        cmd_prefix = text.split("|")[0].strip()
        remain_text = text.split("|", 1)[1].strip()

        # Task 레지스트리에서 명령어 접두사로 Task 찾기
        task_cls = get_task_by_command_prefix(f"{cmd_prefix}|")

        if not task_cls:
            logger.info(f"무시된 메시지 (등록되지 않은 명령어): {text}")
            return

        logger.info(f"{task_cls.TASK_NAME} 요청: {text}")

        # Task 인스턴스 생성 및 메시지 파싱
        task_instance = task_cls()
        parsed_value = await task_instance.parse_message(remain_text, update)

        if parsed_value is None:
            # parse_message에서 이미 에러 메시지를 보냈으므로 여기서는 로깅만
            logger.warning(f"메시지 파싱 실패: {text}")
            return

        # 큐에 Task 추가
        await task_queue.put(QueuedTask(task_name=task_cls.TASK_NAME, value=parsed_value))
        logger.info(f"✅ 작업 큐에 추가됨: {task_cls.TASK_NAME} - {parsed_value}")
        await update.message.reply_text(
            f"✅ 요청이 큐에 추가되었습니다: {parsed_value}"
        )

    except Exception as e:
        logger.exception(f"메시지 처리 중 오류: {e}")
        if update.message:
            await update.message.reply_text(
                f"❌ 메시지 처리 중 오류가 발생했습니다: {e}"
            )


def main() -> None:
    """봇 메인 함수"""
    logger.info("Starting telegram_pulling_bot.py")
    settings = get_settings()
    bot_token = settings.bot_token_str

    # 1) 이벤트 루프가 완전히 돌기 직전(post_init) 실행될 콜백 정의
    async def on_startup(application: "Application") -> None:
        logger.info("🔧 워커 태스크 시작 (post_init)")
        # PTBUserWarning 없이 안전하게 스케줄
        asyncio.create_task(worker(application))

    # 2) ApplicationBuilder에 post_init 등록
    app = ApplicationBuilder().token(bot_token).post_init(on_startup).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot polling 시작")
    app.run_polling()


def run_with_restart() -> None:
    """봇을 실행하고 오류 발생 시 자동 재시작"""
    retry_count = 0
    max_retries = 5  # 최대 재시도 횟수
    base_delay = 5  # 기본 대기 시간 (초)

    while True:
        try:
            logger.info(f"🚀 봇 시작 중... (시도 #{retry_count + 1})")
            main()
            break  # 정상 종료 시 루프 탈출

        except KeyboardInterrupt:
            logger.info("⏹️ 사용자에 의한 종료")
            break

        except Exception as e:
            retry_count += 1
            delay = min(base_delay * (2**retry_count), 300)  # 최대 5분 대기

            logger.error(f"❌ 봇 오류 발생 (시도 #{retry_count}): {e}")
            logger.exception("전체 스택 트레이스:")

            if retry_count >= max_retries:
                logger.error(f"💀 최대 재시도 횟수({max_retries}) 초과. 봇 종료.")
                break

            logger.info(f"⏳ {delay}초 후 재시작...")
            time.sleep(delay)


if __name__ == "__main__":
    run_with_restart()
