import os
import re
import asyncio
import logging

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import ChatForwardsRestrictedError


# ============================================================
# ЛОГИ
# ============================================================

logging.basicConfig(
    format="[%(levelname)s %(asctime)s] %(name)s: %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# TELEGRAM API / RENDER ENVIRONMENT
# ============================================================

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"].strip()
STRING_SESSION = os.environ["TELEGRAM_STRING_SESSION"].strip()


# ============================================================
# ЧАТЫ, КОТОРЫЕ ОТСЛЕЖИВАЕМ
# ============================================================

TARGET_CHATS = [
    -1001961863956,  # FX💬Affiliation | UTIP Technologies
    -1001787758104,  # FX💬Аффилиация | TrafficIcons
    -1002295936547,  # Buy CRG / CPL Requests Only
    -1001339038710,  # Mobster
    -1001293599219,  # BLACK CHAT
    -1001337397906,  # Forex world  
]


# ============================================================
# КУДА ПЕРЕСЫЛАЕМ
# ============================================================

DESTINATION_CHAT = -5462678076  # fresh offers


# ============================================================
# КЛЮЧЕВЫЕ СЛОВА
# ============================================================

KEYWORDS = [

    # LOOKING FOR
    "looking for",
    "looking 4",
    "searching for",
    "searching",
    "seeking",
    "wanted",
    "lf",
    "wtb",
    "anyone have",
    "anyone has",
    "who has",
    "who have",
    "who can provide",
    "who can offer",

    # РУССКИЕ — ИЩУ
    "ищу",
    "ищем",
    "в поиске",
    "нужен",
    "нужна",
    "нужны",
    "нужно",
    "требуется",
    "требуются",
    "есть у кого",
    "у кого есть",
    "кто дает",
    "кто даёт",
    "кто может дать",
    "кто может предложить",

    # DIRECT BRAND
    "db",
    "d.b.",
    "direct brand",
    "direct-brand",
    "directbrand",
    "brand direct",
    "brand-direct",
    "direct brands",
    "direct advertiser",
    "direct adv",
    "brand owner",
    "brandowner",
    "in-house brand",
    "inhouse brand",
    "brand",
    "brands",

    # БРЕНД
    "бренд",
    "бренды",
    "бренда",
    "брендом",
    "бренду",
    "директ бренд",
    "директ-бренд",
    "директбренд",
    "прямой бренд",
    "прямые бренды",
    "бренд напрямую",
    "напрямую от бренда",
    "от бренда",
    "прямой рекламодатель",
    "рекламодатель напрямую",

    # BROKER
    "broker",
    "brokers",
    "direct broker",
    "direct-broker",
    "directbroker",
    "broker direct",
    "broker-direct",

    # БРОКЕР
    "брокер",
    "брокеры",
    "брокера",
    "брокеру",
    "директ брокер",
    "директ-брокер",
    "директброкер",
    "прямой брокер",
    "прямые брокеры",
    "брокер напрямую",

    # CRG / СРГ
    "crg",
    "c.r.g",
    "c-r-g",
    "c r g",
    "срг",
    "с.р.г",
    "с-р-г",
    "с р г",
    "сrg",
    "cрg",
    "crг",
    "срg",
    "cрг",

    # REFS
    "ref",
    "refs",
    "referral",
    "referrals",
    "referral traffic",
    "ref traffic",

    # РЕФЫ
    "реф",
    "рефы",
    "реферал",
    "рефералы",
    "реферальный",
    "реферальный трафик",

    # LATAM
    "latam",
    "lat am",
    "lat-am",
    "latin america",
    "latin american",

    # ЛАТАМ
    "латам",
    "лат ам",
    "лат-ам",
    "латинская америка",

    # EUROPE
    "europe",
    "european",
    "eu geo",
    "eu traffic",
    "eu market",
    "europe geo",

    # ЕВРОПА
    "европа",
    "европы",
    "европе",
    "европейский",
    "европейские гео",
    "евро гео",

    # CPL / СПЛ
    "cpl",
    "c.p.l",
    "c-p-l",
    "c p l",
    "сpl",
    "cпl",
    "cpл",
    "спл",
    "с.п.л",
    "с-п-л",
    "с п л",
    "cost per lead",
    "pay per lead",
    "payment per lead",
    "per lead",
    "lead payout",

    # РУССКИЕ CPL
    "оплата за лид",
    "оплата за лида",
    "цена за лид",
    "выплата за лид",
]


# ============================================================
# TELETHON CLIENT
# ============================================================

client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)


# ============================================================
# НОРМАЛИЗАЦИЯ ТЕКСТА
# ============================================================

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# ПОИСК КЛЮЧЕВЫХ СЛОВ
# ============================================================

def find_keywords(text: str):
    normalized = normalize_text(text)

    matched_words = []

    for keyword in KEYWORDS:
        if keyword.lower() in normalized:
            matched_words.append(keyword)

    return matched_words


# ============================================================
# НОВЫЕ СООБЩЕНИЯ
# ============================================================

@client.on(events.NewMessage(incoming=True))
async def monitor_message(event):

    try:
        # ----------------------------------------------------
        # Проверяем источник
        # ----------------------------------------------------

        if event.chat_id not in TARGET_CHATS:
            return


        message = event.message
        message_text = message.raw_text or ""

        chat = await event.get_chat()
        sender = await event.get_sender()


        chat_title = getattr(
            chat,
            "title",
            "Unknown chat"
        )

        chat_username = getattr(
            chat,
            "username",
            None
        )


        # ----------------------------------------------------
        # Фильтр
        # ----------------------------------------------------

        matched_words = find_keywords(
            message_text
        )

        if not matched_words:

            print(
                f"⏭️ Пропущено [{chat_title}]: "
                f"{message_text[:80]}..."
            )

            return


        # ----------------------------------------------------
        # Отправитель
        # ----------------------------------------------------

        sender_name = "Неизвестно"
        sender_username = None
        sender_id = None


        if sender:

            first_name = (
                getattr(sender, "first_name", "")
                or ""
            )

            last_name = (
                getattr(sender, "last_name", "")
                or ""
            )

            sender_name = (
                f"{first_name} {last_name}".strip()
                or "Без имени"
            )

            sender_username = getattr(
                sender,
                "username",
                None
            )

            sender_id = getattr(
                sender,
                "id",
                None
            )


        # ----------------------------------------------------
        # Логи
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("📩 НАЙДЕНО ПОДХОДЯЩЕЕ СООБЩЕНИЕ")
        print(f"📍 Источник: {chat_title}")
        print(f"🆔 Message ID: {event.id}")
        print(f"👤 Отправитель: {sender_name}")

        if sender_username:
            print(f"🔹 Username: @{sender_username}")

        if sender_id:
            print(f"🆔 Sender ID: {sender_id}")

        print(
            f"🔑 Совпадения: "
            f"{', '.join(matched_words[:10])}"
        )

        print("=" * 70)


        # ----------------------------------------------------
        # Пробуем обычный Telegram Forward
        # ----------------------------------------------------

        try:

            await client.forward_messages(
                DESTINATION_CHAT,
                event.message
            )

            print(
                f"✅ Переслано в fresh offers "
                f"из {chat_title}"
            )


        # ----------------------------------------------------
        # Если владелец исходного чата запретил forward
        # ----------------------------------------------------

        except ChatForwardsRestrictedError:

            print(
                f"🔒 Чат защищён от пересылки: "
                f"{chat_title}"
            )


            notice = (
                "🔒 Найдено подходящее сообщение "
                "в защищённом чате\n\n"

                f"📍 Источник: {chat_title}\n"
                f"👤 Отправитель: {sender_name}\n"
            )


            if sender_username:

                notice += (
                    f"🔹 Username: "
                    f"@{sender_username}\n"
                )


            if sender_id:

                notice += (
                    f"🆔 Sender ID: "
                    f"{sender_id}\n"
                )


            notice += (
                f"🆔 Message ID: {event.id}\n"
                f"🔑 Ключи: "
                f"{', '.join(matched_words[:10])}"
            )


            # Если исходный чат публичный,
            # добавляем прямую ссылку
            if chat_username:

                notice += (
                    "\n\n🔗 Открыть оригинал:\n"
                    f"https://t.me/"
                    f"{chat_username}/"
                    f"{event.id}"
                )


            await client.send_message(
                DESTINATION_CHAT,
                notice
            )


            print(
                "📨 Уведомление отправлено "
                "в fresh offers"
            )


    except Exception as e:

        logger.exception(
            f"❌ Ошибка Telegram Monitor: {e}"
        )


# ============================================================
# START MONITOR
#
# Вызывается из bot.py
# ============================================================

async def start_monitor():

    logger.info(
        "🔄 Подключение Telethon..."
    )


    # connect() не пытается спрашивать телефон
    await client.connect()


    # Проверяем, что StringSession действительно авторизована
    authorized = await client.is_user_authorized()


    if not authorized:

        await client.disconnect()

        raise RuntimeError(
            "TELEGRAM_STRING_SESSION не авторизована. "
            "Создайте новую StringSession локально "
            "и обновите TELEGRAM_STRING_SESSION в Render."
        )


    me = await client.get_me()


    username = (
        f"@{me.username}"
        if me.username
        else "без username"
    )


    logger.info(
        "✅ SHARMINATOR MONITOR подключён"
    )

    logger.info(
        f"👤 Telethon аккаунт: "
        f"{me.first_name} ({username})"
    )

    logger.info(
        f"👀 Отслеживаемых чатов: "
        f"{len(TARGET_CHATS)}"
    )

    logger.info(
        f"🔑 Ключевых слов: "
        f"{len(KEYWORDS)}"
    )

    logger.info(
        f"📨 Destination: "
        f"{DESTINATION_CHAT}"
    )


# ============================================================
# STOP MONITOR
# ============================================================

async def stop_monitor():

    if client.is_connected():

        await client.disconnect()

        logger.info(
            "🛑 Telegram Monitor отключён"
        )


# ============================================================
# ОТДЕЛЬНЫЙ ЛОКАЛЬНЫЙ ЗАПУСК
#
# Этот блок НЕ выполняется, когда bot.py делает:
#
# from telegram_monitor import start_monitor, stop_monitor
# ============================================================

async def run_standalone():

    await start_monitor()

    print()
    print("✅ SHARMINATOR MONITOR запущен")
    print("⏳ Ожидаю новые сообщения...")
    print()

    await client.run_until_disconnected()


if __name__ == "__main__":

    try:

        asyncio.run(
            run_standalone()
        )

    except KeyboardInterrupt:

        print(
            "\n🛑 Монитор остановлен пользователем"
        )
