import asyncio
import logging
import threading
import os
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import router

# --- Импорты для Telethon ---
from telethon import TelegramClient, events
from telethon.errors import ChatForwardsRestrictedError

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Создание фиктивного веб-сервера для Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ============================================================
# TELEGRAM MONITOR (Telethon)
# ============================================================

async def run_telethon_monitor():
    """Запускает мониторинг чатов через личный аккаунт"""
    
    API_ID = int(os.environ.get("TELEGRAM_API_ID", 0))
    API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
    
    if not API_ID or not API_HASH:
        logging.warning("⚠️ TELEGRAM_API_ID или TELEGRAM_API_HASH не заданы. Монитор не запущен.")
        return
    
    # ЧАТЫ ДЛЯ ОТСЛЕЖИВАНИЯ
    TARGET_CHATS = [
        -1001961863956,  # FX💬Affiliation | UTIP Technologies
        -1001787758104,  # FX💬Аффилиация | TrafficIcons
        -1002295936547,  # Buy CRG / CPL Requests Only
    ]
    
    DESTINATION_CHAT = -5394290236  # fresh offers
    
    # КЛЮЧЕВЫЕ СЛОВА
    KEYWORDS = [
        "looking for", "looking 4", "searching for", "searching",
        "seeking", "wanted", "lf", "wtb",
        "anyone have", "anyone has", "who has", "who have",
        "who can provide", "who can offer",
        "ищу", "ищем", "в поиске",
        "нужен", "нужна", "нужны", "нужно",
        "требуется", "требуются",
        "есть у кого", "у кого есть",
        "кто дает", "кто даёт", "кто может дать", "кто может предложить",
        "db", "d.b.",
        "direct brand", "direct-brand", "directbrand",
        "brand direct", "brand-direct",
        "direct brands", "direct advertiser", "direct adv",
        "brand owner", "brandowner",
        "in-house brand", "inhouse brand",
        "brand", "brands",
        "бренд", "бренды", "бренда", "брендом", "бренду",
        "директ бренд", "директ-бренд", "директбренд",
        "прямой бренд", "прямые бренды",
        "бренд напрямую", "напрямую от бренда", "от бренда",
        "прямой рекламодатель", "рекламодатель напрямую",
        "broker", "brokers",
        "direct broker", "direct-broker", "directbroker",
        "broker direct", "broker-direct",
        "брокер", "брокеры", "брокера", "брокеру",
        "директ брокер", "директ-брокер", "директброкер",
        "прямой брокер", "прямые брокеры",
        "брокер напрямую",
        "crg", "c.r.g", "c-r-g", "c r g",
        "срг", "с.р.г", "с-р-г", "с р г",
        "сrg", "cрg", "crг", "срg", "cрг",
        "ref", "refs", "referral", "referrals",
        "referral traffic", "ref traffic",
        "реф", "рефы", "реферал", "рефералы",
        "реферальный", "реферальный трафик",
        "latam", "lat am", "lat-am",
        "latin america", "latin american",
        "латам", "лат ам", "лат-ам",
        "латинская америка",
        "europe", "european",
        "eu geo", "eu traffic", "eu market",
        "europe geo",
        "европа", "европы", "европе",
        "европейский", "европейские гео",
        "евро гео",
        "cpl", "c.p.l", "c-p-l", "c p l",
        "сpl", "cпl", "cpл", "спл",
        "с.п.л", "с-п-л", "с п л",
        "cost per lead", "pay per lead",
        "payment per lead", "per lead", "lead payout",
        "оплата за лид", "оплата за лида",
        "цена за лид", "выплата за лид",
    ]
    
    # ============================================================
    # ИСПОЛЬЗУЕМ ФАЙЛ СЕССИИ (а не строку)
    # ============================================================
    
    # Проверяем, есть ли файл сессии в Secret Files
    session_file = 'telethon.session'  # Имя файла, который загрузили на Render
    
    # Если файла нет, пробуем использовать другой вариант
    if not os.path.exists(session_file):
        logging.warning(f"⚠️ Файл {session_file} не найден, пробую создать новую сессию")
        client = TelegramClient("sharminator_user", API_ID, API_HASH)
    else:
        logging.info(f"✅ Используем файл сессии: {session_file}")
        client = TelegramClient(session_file, API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=TARGET_CHATS, incoming=True))
    async def monitor_message(event):
        try:
            chat = await event.get_chat()
            sender = await event.get_sender()
            message_text = event.message.text or ""
            
            # Проверка ключевых слов
            text_lower = message_text.lower()
            matched = any(kw.lower() in text_lower for kw in KEYWORDS)
            if not matched:
                return
            
            chat_title = getattr(chat, "title", "Unknown chat")
            chat_username = getattr(chat, "username", None)
            
            # Собираем информацию об отправителе
            sender_name = "Неизвестно"
            sender_username = "Нет username"
            sender_id = "Неизвестно"
            
            if sender:
                first_name = getattr(sender, "first_name", "")
                last_name = getattr(sender, "last_name", "")
                sender_name = f"{first_name} {last_name}".strip() or "Без имени"
                sender_username = f"@{sender.username}" if getattr(sender, "username", None) else "Нет username"
                sender_id = getattr(sender, "id", "Неизвестно")
            
            # Формируем сообщение
            header = f"📩 НОВОЕ СООБЩЕНИЕ\n"
            header += f"📍 Источник: {chat_title}\n"
            header += f"👤 Отправитель: {sender_name}\n"
            header += f"🔹 Username: {sender_username}\n"
            header += f"🆔 ID: {sender_id}\n"
            
            if chat_username:
                header += f"🔗 https://t.me/{chat_username}/{event.id}\n"
            
            full_text = header + "\n" + "=" * 40 + "\n\n" + message_text
            
            # Отправляем через Telethon (в fresh offers)
            try:
                await client.send_message(DESTINATION_CHAT, full_text)
                print(f"📨 Отправлено сообщение из {chat_title}")
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
            
        except Exception as e:
            logging.exception(f"❌ Ошибка мониторинга: {e}")
    
    await client.start()
    logging.info("✅ Telethon Monitor запущен")
    logging.info(f"👀 Отслеживаемые чаты: {TARGET_CHATS}")
    await client.run_until_disconnected()

# ============================================================
# ОСНОВНОЙ КОД БОТА (Aiogram)
# ============================================================

async def main():
    # Запускаем Telethon-монитор в фоновом режиме
    asyncio.create_task(run_telethon_monitor())
    
    # Запускаем Aiogram-бота
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