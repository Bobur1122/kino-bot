"""
Kino Bot — main entry point (OPTIMIZED).
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

import uvicorn
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, CallbackQuery, ErrorEvent, TelegramObject
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, PORT
import database as db
from api.routes import app, set_bot
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.search import router as search_router
from handlers.channel_post import router as channel_post_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())


# ===== CALLBACK ANSWER MIDDLEWARE — tugmalar qotmasligi uchun =====
class CallbackAnswerMiddleware(BaseMiddleware):
    """Har bir callback tugma bosilganda darhol answer() chaqiradi.
    Bu Telegram'dagi loading spinnerni yo'qotadi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery):
            try:
                await event.answer()
            except Exception:
                pass
        return await handler(event, data)


# Middleware'ni callback_query'ga qo'shish
dp.callback_query.middleware(CallbackAnswerMiddleware())

# Routerlar
dp.include_router(start_router)
dp.include_router(admin_router)
dp.include_router(channel_post_router)
dp.include_router(search_router)


# ===== GLOBAL ERROR HANDLER =====
@dp.error()
async def global_error_handler(event: ErrorEvent):
    logger.error(f"Bot error: {event.exception}", exc_info=True)
    update = event.update
    try:
        if update and update.callback_query:
            cb = update.callback_query
            try:
                await cb.answer("❌ Xatolik yuz berdi", show_alert=True)
            except Exception:
                pass
            try:
                await cb.message.answer(f"⚠️ Xatolik: {event.exception}")
            except Exception:
                pass
        elif update and update.message:
            await update.message.answer(f"⚠️ Xatolik: {event.exception}")
    except Exception:
        pass


@asynccontextmanager
async def lifespan(application):
    await db.init_db()
    set_bot(bot)
    logger.info("Database initialized")

    if WEBHOOK_URL:
        webhook_full = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
        await bot.set_webhook(
            webhook_full,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "channel_post"]
        )
        logger.info(f"Webhook set: {webhook_full}")
    else:
        logger.info("No WEBHOOK_URL — polling mode")

    yield

    if WEBHOOK_URL:
        await bot.delete_webhook()
    await bot.session.close()

app.router.lifespan_context = lifespan


@app.post(WEBHOOK_PATH)
async def webhook_handler(update: dict):
    telegram_update = Update.model_validate(update, context={"bot": bot})
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}


async def start_polling():
    await db.init_db()
    set_bot(bot)
    logger.info("Starting bot in polling mode...")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    if WEBHOOK_URL:
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    else:
        asyncio.run(start_polling())
