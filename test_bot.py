import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ Бот работает! Проверка прошла успешно! 🎉")

@dp.message(Command("ping"))
async def ping(message: types.Message):
    await message.answer("🏓 Pong!")

async def main():
    print("🟢 Тестовый бот запущен! Отправьте /start в Telegram")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())