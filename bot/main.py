"""
Kino Bot — main entry point.
Bot (aiogram 3) + FastAPI (API server) birgalikda ishlaydi.
Render uchun webhook rejimida.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, PORT
import database as db
from api.routes import app, set_bot
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.search import router as search_router
from handlers.channel_post import router as channel_post_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# Routerlarni qo'shish (tartib muhim — admin avval, search oxirda)
dp.include_router(start_router)
dp.include_router(admin_router)
dp.include_router(channel_post_router)
dp.include_router(search_router)


@asynccontextmanager
async def lifespan(application):
    """FastAPI lifecycle — bot webhook o'rnatish."""
    # Startup
    await db.init_db()
    set_bot(bot)
    logger.info("Database initialized")

    if WEBHOOK_URL:
        webhook_full = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
        await bot.set_webhook(webhook_full, drop_pending_updates=True)
        logger.info(f"Webhook set: {webhook_full}")
    else:
        logger.info("No WEBHOOK_URL — starting polling mode")

    yield

    # Shutdown
    if WEBHOOK_URL:
        await bot.delete_webhook()
    await bot.session.close()

app.router.lifespan_context = lifespan


@app.post(WEBHOOK_PATH)
async def webhook_handler(update: dict):
    """Telegram webhook handler."""
    telegram_update = Update.model_validate(update, context={"bot": bot})
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}


async def start_polling():
    """Polling rejimida ishga tushirish (local test uchun)."""
    await db.init_db()
    set_bot(bot)
    logger.info("Starting bot in polling mode...")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    if WEBHOOK_URL:
        # Render uchun — webhook + uvicorn
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    else:
        # Local test uchun — polling
        asyncio.run(start_polling())
