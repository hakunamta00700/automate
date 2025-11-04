"""텔레그램 웹훅 서비스"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from telegram import Bot, Update

from ...core.config import get_settings


def create_app() -> FastAPI:
    """FastAPI 애플리케이션을 생성합니다."""
    settings = get_settings()

    # Bot 설정
    bot_token = settings.bot_token_str
    bot = Bot(token=bot_token)

    # FastAPI 앱 생성
    app = FastAPI()

    # lifespan 훅 정의
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # startup
        await bot.delete_webhook()
        await bot.set_webhook(settings.webhook_url)
        yield
        # shutdown
        await bot.delete_webhook()

    app.router.lifespan_context = lifespan

    # Webhook 엔드포인트
    @app.post(settings.WEBHOOK_PATH)
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

    return app
