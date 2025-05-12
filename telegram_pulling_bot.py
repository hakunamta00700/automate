import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from src.automate import extract_video_id, process_video

load_dotenv()
logger.info("Starting telegram_pulling_bot.py")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables.")

CHANNEL_CHAT_ID = os.getenv("CHANNEL_CHAT_ID")
if not CHANNEL_CHAT_ID:
    raise RuntimeError("CHANNEL_CHAT_ID is not set in environment variables.")
CHANNEL_CHAT_ID = int(CHANNEL_CHAT_ID)
TARGET_LLM_MODEL = os.getenv("TARGET_LLM_MODEL", "gemini")
print(f"TARGET_LLM_MODEL: {TARGET_LLM_MODEL}")
CMD_PREFIX = "요약|"
# 전역 큐
task_queue = asyncio.Queue()


async def send_message(application, text: str):
    await application.bot.send_message(chat_id=CHANNEL_CHAT_ID, text=text)


async def worker(application):
    while True:
        video_id = await task_queue.get()
        try:
            logger.info(f"[WORKER] 처리 시작: {video_id}")
            await send_message(application, f"요약 처리 시작: {video_id}")
            summary_text = await process_video(video_id)
            logger.info(f"[WORKER] 완료: {video_id}")
            await send_message(application, f"✅ 요약 처리 완료: {video_id}")
            await send_message(application, summary_text)
        except Exception:
            logger.exception(f"[WORKER] 오류 발생: {video_id}")
            await send_message(application, f"❌ 처리 중 오류 발생: {video_id}")
        finally:
            task_queue.task_done()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    logger.info(f"Received message: {text}")

    if text.startswith(CMD_PREFIX):
        try:
            video_url = text.split("|", 1)[1]
            video_id = extract_video_id(video_url)
            await task_queue.put(video_id)

            logger.info(f"✅ 작업 큐에 추가됨: {video_id}")
            await update.message.reply_text(
                f"✅ 요청이 큐에 추가되었습니다: {video_id}"
            )
        except Exception as e:
            logger.exception(f"Error handling message: {e}")
            await update.message.reply_text(f"❌ 오류 발생: {e}")
    else:
        logger.debug(f"무시된 메시지: {CMD_PREFIX} 로 시작하지 않음")


def main():
    # 1) 이벤트 루프가 완전히 돌기 직전(post_init) 실행될 콜백 정의
    async def on_startup(application):
        logger.info("🔧 워커 태스크 시작 (post_init)")
        # PTBUserWarning 없이 안전하게 스케줄
        asyncio.create_task(worker(application))

    # 2) ApplicationBuilder에 post_init 등록
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot polling 시작")
    app.run_polling()


if __name__ == "__main__":
    main()
