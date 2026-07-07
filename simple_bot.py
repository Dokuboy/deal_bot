import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ Бот работает! Напиши /add или /list")

@dp.message(Command("add"))
async def add(message: types.Message):
    await message.answer("📝 Функция добавления сделки временно отключена для диагностики")

@dp.message(Command("list"))
async def list_deals(message: types.Message):
    await message.answer("📋 Функция списка сделок временно отключена для диагностики")

@dp.message()
async def echo(message: types.Message):
    await message.answer(f"👋 Я получил: {message.text}")

async def main():
    print("🟢 Простой бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())