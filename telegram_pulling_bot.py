import asyncio
import os
import re
from urllib.parse import urlparse, parse_qs
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

address_dict = {
    "요약":"http://pringles.iptime.org/webhook/e171b96e-3318-4cba-a2b9-60f9b353d406"
}


def extract_youtube_video_id(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    path = parsed_url.path

    # 1. youtu.be short URL
    if hostname in ['youtu.be']:
        return path.lstrip('/')

    # 2. youtube.com/watch?v=VIDEO_ID
    if 'youtube.com' in hostname:
        if path == '/watch':
            query = parse_qs(parsed_url.query)
            return query.get('v', [None])[0]

        # 3. youtube.com/embed/VIDEO_ID or /shorts/VIDEO_ID
        match = re.match(r'^/(embed|shorts)/([^/?]+)', path)
        if match:
            return match.group(2)

    return None

async def send_message(application, text: str):
    await application.bot.send_message(chat_id=CHANNEL_CHAT_ID, text=text)

async def run_command(*command_args):
    process = await asyncio.create_subprocess_exec(
        *command_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    print("STDOUT:")
    print(stdout.decode())

    print("STDERR:")
    print(stderr.decode())    

def get_summary_text(video_id: str):
    with open(f"/root/tempyt/{video_id}.ko.txt", "r") as f:
        return f.read()

async def worker(application):
    while True:
        video_id = await task_queue.get()
        try:
            logger.info(f"[WORKER] 처리 시작: {video_id}")
            await send_message(application, f"요약 처리 시작: {video_id}")
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            await run_command("~/iscripts/summary_yt.sh", video_url, "/root/tempyt")
            logger.info(f"[WORKER] 완료: {video_id}")

            await send_message(application, f"✅ 요약 처리 완료: {video_id}")
            await send_message(application, get_summary_text(video_id))
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

    cmd_prefix = text.split("|")[0].strip()
    match cmd_prefix:
        case "요약":
            logger.info(f"요약 요청: {text}")
            video_url = text.split("|", 1)[1]
            video_id = extract_youtube_video_id(video_url)
            await task_queue.put(video_id)
            await update.message.reply_text(
                f"✅ 요청이 큐에 추가되었습니다: {video_id}"
            )
        case "포스팅":
            logger.info(f"포스팅 요청: {text}")
        case _:
            logger.info(f"무시된 메시지: {text}")

    # if text.startswith(CMD_PREFIX):
    #     try:
    #         video_url = text.split("|", 1)[1]
    #         video_id = extract_video_id(video_url)
    #         await task_queue.put(video_id)

    #         logger.info(f"✅ 작업 큐에 추가됨: {video_id}")
    #         await update.message.reply_text(
    #             f"✅ 요청이 큐에 추가되었습니다: {video_id}"
    #         )
    #     except Exception as e:
    #         logger.exception(f"Error handling message: {e}")
    #         await update.message.reply_text(f"❌ 오류 발생: {e}")
    # else:
    #     logger.debug(f"무시된 메시지: {CMD_PREFIX} 로 시작하지 않음")


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
