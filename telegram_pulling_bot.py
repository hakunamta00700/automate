import asyncio
import os
import re
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

load_dotenv()
logger.info("Starting telegram_pulling_bot.py")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables.")

CHANNEL_CHAT_ID = os.getenv("CHANNEL_CHAT_ID")
if not CHANNEL_CHAT_ID:
    raise RuntimeError("CHANNEL_CHAT_ID is not set in environment variables.")
CHANNEL_CHAT_ID = int(CHANNEL_CHAT_ID)


class CmdPrefix:
    SUMMARY = "요약|"
    SHORTS = "쇼츠|"


class WebHook:
    shorts = "http://pringles.iptime.org/webhook/eb917575-b39f-4197-b867-f0fcd72aaac6"


# 전역 큐
task_queue = asyncio.Queue()

address_dict = {
    "요약": "http://pringles.iptime.org/webhook/e171b96e-3318-4cba-a2b9-60f9b353d406"
}


def extract_youtube_video_id(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    path = parsed_url.path

    # 1. youtu.be short URL
    if hostname in ["youtu.be"]:
        return path.lstrip("/")

    # 2. youtube.com/watch?v=VIDEO_ID
    if "youtube.com" in hostname:
        if path == "/watch":
            query = parse_qs(parsed_url.query)
            return query.get("v", [None])[0]

        # 3. youtube.com/embed/VIDEO_ID or /shorts/VIDEO_ID
        match = re.match(r"^/(embed|shorts)/([^/?]+)", path)
        if match:
            return match.group(2)

    return None


class TaskKind:
    SUMMARY = "summary"
    SHORTS = "shorts"


@dataclass
class Task:
    kind: TaskKind
    value: str


async def send_message(application, text: str):
    await application.bot.send_message(chat_id=CHANNEL_CHAT_ID, text=text)


async def run_command(command: str):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    print("STDOUT:")
    print(stdout.decode())

    print("STDERR:")
    print(stderr.decode())


def get_summary_text(video_id: str):
    with open(f"/root/tempyt/{video_id}.ko.txt", "r") as f:
        return f.read()


async def fetch_data(url):
    """
    주어진 URL로 GET 요청을 보내고 응답 텍스트를 반환합니다.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # 응답 상태 코드 확인
            if response.status == 200:
                # 응답 본문을 텍스트로 읽기
                return await response.text()
            else:
                print(f"Error: {response.status} - {response.reason}")
                return None


async def worker(application):
    while True:
        try:
            task: Task = await task_queue.get()
            if task.kind == TaskKind.SUMMARY:
                try:
                    video_id = task.value
                    logger.info(f"[WORKER] 처리 시작: {video_id}")
                    await send_message(application, f"요약 처리 시작: {video_id}")
                    video_url = f'"https://www.youtube.com/watch?v={video_id}"'
                    command = f"/root/iscripts/summary_yt {video_url} /root/tempyt"
                    await run_command(command)
                    logger.info(f"[WORKER] 완료: {video_id}")
                    await send_message(application, f"✅ 요약 처리 완료: {video_id}")

                except Exception:
                    logger.exception(f"[WORKER] 오류 발생: {video_id}")
                    await send_message(application, f"❌ 처리 중 오류 발생: {video_id}")
            elif task.kind == TaskKind.SHORTS:
                try:
                    logger.info(f"[WORKER] 처리 시작: {task.value}")
                    await send_message(application, f"쇼츠 대본생성 시작: {task.value}")
                    target_url = f"{WebHook.shorts}?url={task.value}"
                    res = await fetch_data(target_url)
                    logger.info(f"[WORKER] 완료: {task.value}")
                    await send_message(application, f"✅ 쇼츠 처리 완료: {task.value}")
                except Exception as e:
                    logger.exception(f"[WORKER] 오류 발생: {task.value}")
                    await send_message(
                        application, f"❌ 처리 중 오류 발생: {task.value} - {e}"
                    )
            else:
                logger.error(f"[WORKER] 유효하지 않은 작업 유형: {task.kind}")
                await send_message(
                    application, f"❌ 유효하지 않은 작업 유형: {task.kind}"
                )
        except Exception as e:
            logger.exception(f"[WORKER] 작업 처리 중 오류: {e}")
            await send_message(application, f"❌ 워커 오류: {e}")
        finally:
            task_queue.task_done()


async def do_summary(video_url, update):
    video_id = extract_youtube_video_id(video_url)
    await task_queue.put(Task(kind=TaskKind.SUMMARY, value=video_id))

    logger.info(f"✅ 작업 큐에 추가됨: {video_id}")
    await update.message.reply_text(f"✅ 요청이 큐에 추가되었습니다: {video_id}")


async def do_make_shorts(text, update):
    try:
        page_url = text.split("|", 1)[1]
        await task_queue.put(Task(kind=TaskKind.SHORTS, value=page_url))
        logger.info(f"✅ 작업 큐에 추가됨: {page_url}")
        await update.message.reply_text(f"✅ 요청이 큐에 추가되었습니다: {page_url}")
    except Exception as e:
        logger.exception(f"Error handling message: {e}")
        await update.message.reply_text(f"❌ 오류 발생: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        logger.info(f"Received message: {text}")

        cmd_prefix = text.split("|")[0].strip()
        remain_text = text.split("|", 1)[1].strip()
        match cmd_prefix:
            case "요약":
                logger.info(f"요약 요청: {text}")
                await do_summary(remain_text, update)
            case "쇼츠":
                logger.info(f"쇼츠 요청: {text}")
            case _:
                logger.info(f"무시된 메시지: {text}")
    except Exception as e:
        logger.exception(f"메시지 처리 중 오류: {e}")
        if update.message:
            await update.message.reply_text(
                f"❌ 메시지 처리 중 오류가 발생했습니다: {e}"
            )


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


def run_with_restart():
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
