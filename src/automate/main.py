from typing import Union
import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Bot 설정
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"http://{WEBHOOK_DOMAIN}{WEBHOOK_PATH}"

# FastAPI 앱 생성
app = FastAPI()

# Application 객체 생성 (v20+)
application = Application.builder().token(BOT_TOKEN).build()

# 메시지 핸들러 (async 함수)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = text[::-1]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Result: {response}")

# 핸들러 등록
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# lifespan 훅 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await application.bot.delete_webhook()
    await application.bot.set_webhook(WEBHOOK_URL)
    yield
    # shutdown
    await application.bot.delete_webhook()

app.router.lifespan_context = lifespan

# Webhook 엔드포인트
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    body = await req.json()
    try:
        update = Update.de_json(body, application.bot)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid update")
    await application.process_update(update)
    return {"ok": True}

