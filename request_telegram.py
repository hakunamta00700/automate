import argparse
import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file.")

# Type assertion for linter
BOT_TOKEN = str(BOT_TOKEN)
CHANNEL_CHAT_ID = "431464720"
parser = argparse.ArgumentParser(
    description="Send a message to a Telegram chat using the bot."
)
parser.add_argument("message", type=str, help="The message to send.")
args = parser.parse_args()


async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(chat_id=CHANNEL_CHAT_ID, text=args.message)
        print(f"Message sent to chat_id {CHANNEL_CHAT_ID}")
    except Exception as e:
        print(f"Failed to send message: {e}")


if __name__ == "__main__":
    asyncio.run(main())
