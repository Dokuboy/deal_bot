import os
import asyncio
import logging
import threading

from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import router

# Готовый Telethon-монитор находится отдельно
from telegram_monitor import start_monitor, stop_monitor


# ============================================================
# ЛОГИ
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s %(asctime)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# FLASK — HEALTH SERVER ДЛЯ RENDER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "SHARMINATOR is alive!"


@app.route("/health")
def health():
    return {
        "status": "ok",
        "service": "SHARMINATOR"
    }


def run_web():
    """
    Небольшой HTTP-сервер для Render.
    Render передаёт порт через переменную PORT.
    Локально используем 10000.
    """

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    logger.info(
        f"🌐 Web server запускается на порту {port}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


# ============================================================
# ОСНОВНОЙ ПРОЦЕСС
# ============================================================

async def main():

    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК SHARMINATOR")
    logger.info("=" * 60)


    # ========================================================
    # AIROGRAM BOT
    # ========================================================

    bot = Bot(
        token=BOT_TOKEN
    )

    dp = Dispatcher(
        storage=MemoryStorage()
    )

    dp.include_router(
        router
    )

    logger.info(
        "✅ Aiogram подготовлен"
    )


    # ========================================================
    # TELETHON MONITOR
    # ========================================================

    try:

        logger.info(
            "🔄 Подключаю Telegram Monitor..."
        )

        await start_monitor()

        logger.info(
            "✅ Telegram Monitor подключён"
        )


        # ====================================================
        # ЗАПУСК AIROGRAM
        #
        # Пока aiogram находится в polling,
        # Telethon продолжает получать события
        # в том же asyncio event loop.
        # ====================================================

        logger.info(
            "🤖 Запускаю Telegram Bot polling..."
        )

        await dp.start_polling(
            bot
        )


    # ========================================================
    # ОСТАНОВКА
    # ========================================================

    finally:

        logger.info(
            "🛑 Останавливаю SHARMINATOR..."
        )


        # ----------------------------------------------------
        # Останавливаем Telethon
        # ----------------------------------------------------

        try:

            await stop_monitor()

            logger.info(
                "✅ Telegram Monitor отключён"
            )

        except Exception as e:

            logger.exception(
                f"❌ Ошибка остановки Telegram Monitor: {e}"
            )


        logger.info(
            "✅ SHARMINATOR остановлен"
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # FLASK В ОТДЕЛЬНОМ ПОТОКЕ
    # ========================================================

    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    logger.info(
        "🌐 Web server thread запущен"
    )


    # ========================================================
    # AIROGRAM + TELETHON
    # ========================================================

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "🛑 SHARMINATOR остановлен пользователем"
        )

    except Exception as e:

        logger.exception(
            f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}"
        )

        raise