import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from telegram import Bot, Update

load_dotenv()

# Bot 설정
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file.")
BOT_TOKEN = str(BOT_TOKEN)
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"http://{WEBHOOK_DOMAIN}{WEBHOOK_PATH}"

# FastAPI 앱 생성
app = FastAPI()
bot = Bot(token=BOT_TOKEN)


# lifespan 훅 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    yield
    # shutdown
    await bot.delete_webhook()


app.router.lifespan_context = lifespan


# Webhook 엔드포인트
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    body = await req.json()
    try:
        update = Update.de_json(body, bot)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid update")
    if update.message and update.message.text:
        text = update.message.text
        response = text[::-1]
        chat_id = update.message.chat.id
        await bot.send_message(chat_id=chat_id, text=f"Result: {response}")
    return {"ok": True}
