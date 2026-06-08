"""
Local run script — Bot va FastAPI serverini parallel ishga tushiradi.
"""
import asyncio
import logging
import uvicorn
from main import bot, dp, start_polling
from api.routes import app
from config import PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_fastapi():
    """FastAPI serverini 8000 portda ishga tushirish."""
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    except SystemExit as exc:
        logger.warning(
            "FastAPI %s portda ishga tushmadi. Bot polling davom etadi.",
            PORT,
        )
        if exc.code not in (0, None):
            logger.warning(
                "Agar API kerak bo'lsa, PORT band emasligini tekshiring yoki boshqa port bering."
            )
    except OSError as exc:
        logger.warning(
            "FastAPI %s portda ishga tushmadi: %s. Bot polling davom etadi.",
            PORT,
            exc,
        )

async def main():
    # Parallel ravishda server va bot pollingni ishga tushiramiz
    logger.info("Starting API on http://127.0.0.1:%s ...", PORT)
    logger.info("Starting Telegram Bot (Polling)...")
    await asyncio.gather(
        run_fastapi(),
        start_polling()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped.")
