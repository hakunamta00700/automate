import os

import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.info("Starting telegram_pulling_bot.py")

YOUTUBE_SUMMARY_WEBHOOK = os.getenv("YOUTUBE_SUMMARY_WEBHOOK")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables.")

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        logger.warning("Received update with no message or text.")
        return
    text = update.message.text
    logger.info(f"Received message: {text}")
    if text.startswith("요약|"):
        try:
            video_url = text.split("|")[1]
            logger.info(f"Extracted video_url: {video_url}")
            # POST 방식으로 video_url 전달
            params = {
                "video_url": video_url
            }
            response = requests.post(YOUTUBE_SUMMARY_WEBHOOK, params=params)
            logger.info(
                f"POST to webhook, status_code={response.status_code}, response={response.text}"
            )
            await update.message.reply_text(
                f"✅ 요청 전송됨\n응답: {response.status_code}"
            )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(f"❌ 오류 발생: {e}")
    else:
        logger.debug("Message does not start with '영상요약'")


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
logger.info("Bot polling started.")
app.run_polling()
