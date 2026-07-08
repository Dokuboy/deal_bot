import asyncio
import logging
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import router

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Создание фиктивного веб-сервера для Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# --- Основной код бота ---
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем Flask-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web)
    web_thread.start()
    logging.info("Фиктивный веб-сервер запущен на порту 10000")
    
    # Запускаем основную функцию бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем.")