import os
import logging
import re

from telethon import TelegramClient, events
from telethon.errors import ChatForwardsRestrictedError


# ============================================================
# ЛОГИ
# ============================================================

logging.basicConfig(
    format="[%(levelname)s %(asctime)s] %(name)s: %(message)s",
    level=logging.INFO
)


# ============================================================
# TELEGRAM API
# ============================================================

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]


# ============================================================
# ЧАТЫ, КОТОРЫЕ ОТСЛЕЖИВАЕМ
# ============================================================

TARGET_CHATS = [
    -1001961863956,  # FX💬Affiliation | UTIP Technologies
    -1001787758104,  # FX💬Аффилиация | TrafficIcons
    -1002295936547,  # Buy CRG / CPL Requests Only
]


# ============================================================
# КУДА ПЕРЕСЫЛАЕМ
# ============================================================

DESTINATION_CHAT = -5394290236  # fresh offers


# ============================================================
# КЛЮЧЕВЫЕ СЛОВА ДЛЯ ФИЛЬТРАЦИИ
# ============================================================

KEYWORDS = [
    # === АНГЛИЙСКИЕ ===
    "looking for", "looking 4", "searching for", "searching",
    "seeking", "wanted", "lf", "wtb",
    "anyone have", "anyone has", "who has", "who have",
    "who can provide", "who can offer",

    # === РУССКИЕ ===
    "ищу", "ищем", "в поиске",
    "нужен", "нужна", "нужны", "нужно",
    "требуется", "требуются",
    "есть у кого", "у кого есть",
    "кто дает", "кто даёт", "кто может дать", "кто может предложить",

    # === DIRECT BRAND ===
    "db", "d.b.",
    "direct brand", "direct-brand", "directbrand",
    "brand direct", "brand-direct",
    "direct brands", "direct advertiser", "direct adv",
    "brand owner", "brandowner",
    "in-house brand", "inhouse brand",
    "brand", "brands",

    # === РУССКИЕ БРЕНД ===
    "бренд", "бренды", "бренда", "брендом", "бренду",
    "директ бренд", "директ-бренд", "директбренд",
    "прямой бренд", "прямые бренды",
    "бренд напрямую", "напрямую от бренда", "от бренда",
    "прямой рекламодатель", "рекламодатель напрямую",

    # === BROKER ===
    "broker", "brokers",
    "direct broker", "direct-broker", "directbroker",
    "broker direct", "broker-direct",

    # === РУССКИЕ БРОКЕР ===
    "брокер", "брокеры", "брокера", "брокеру",
    "директ брокер", "директ-брокер", "директброкер",
    "прямой брокер", "прямые брокеры",
    "брокер напрямую",

    # === CRG ===
    "crg", "c.r.g", "c-r-g", "c r g",
    "срг", "с.р.г", "с-р-г", "с р г",
    "сrg", "cрg", "crг", "срg", "cрг",

    # === REF ===
    "ref", "refs", "referral", "referrals",
    "referral traffic", "ref traffic",

    # === РУССКИЕ РЕФ ===
    "реф", "рефы", "реферал", "рефералы",
    "реферальный", "реферальный трафик",

    # === LATAM ===
    "latam", "lat am", "lat-am",
    "latin america", "latin american",

    # === РУССКИЕ ЛАТАМ ===
    "латам", "лат ам", "лат-ам",
    "латинская америка",

    # === EUROPE ===
    "europe", "european",
    "eu geo", "eu traffic", "eu market",
    "europe geo",

    # === РУССКИЕ ЕВРОПА ===
    "европа", "европы", "европе",
    "европейский", "европейские гео",
    "евро гео",

    # === CPL ===
    "cpl", "c.p.l", "c-p-l", "c p l",
    "сpl", "cпl", "cpл", "спл",
    "с.п.л", "с-п-л", "с п л",
    "cost per lead", "pay per lead",
    "payment per lead", "per lead", "lead payout",

    # === РУССКИЕ CPL ===
    "оплата за лид", "оплата за лида",
    "цена за лид", "выплата за лид",
]


# ============================================================
# TELETHON CLIENT
# ============================================================

client = TelegramClient(
    "sharminator_user_new",
    API_ID,
    API_HASH
)


# ============================================================
# НОВЫЕ СООБЩЕНИЯ
# ============================================================

@client.on(
    events.NewMessage(
        chats=TARGET_CHATS,
        incoming=True
    )
)
async def monitor_message(event):

    try:
        chat = await event.get_chat()
        message = event.message
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

        # Получаем текст сообщения
        message_text = message.text or ""

        # ====================================================
        # ФИЛЬТРАЦИЯ ПО КЛЮЧЕВЫМ СЛОВАМ
        # ====================================================

        text_lower = message_text.lower()

        # Проверяем, есть ли хотя бы одно ключевое слово
        matched = False
        matched_words = []

        for keyword in KEYWORDS:
            if keyword.lower() in text_lower:
                matched = True
                matched_words.append(keyword)

        if not matched:
            print(f"⏭️ Пропущено (нет ключевых слов): {message_text[:50]}...")
            return

        print(f"🔑 Совпадения: {', '.join(matched_words[:5])}...")

        # ====================================================
        # ИНФОРМАЦИЯ ОБ ОТПРАВИТЕЛЕ
        # ====================================================

        sender_info = ""

        if sender:
            first_name = getattr(sender, "first_name", "")
            last_name = getattr(sender, "last_name", "")
            full_name = f"{first_name} {last_name}".strip() or "Без имени"
            sender_username = getattr(sender, "username", None)
            username_str = f"@{sender_username}" if sender_username else "Нет username"
            sender_id = getattr(sender, "id", "Неизвестно")

            sender_info = (
                f"👤 Отправитель: {full_name}\n"
                f"🔹 Username: {username_str}\n"
                f"🆔 ID: {sender_id}\n"
            )

        print("\n" + "=" * 60)
        print("📩 НОВОЕ СООБЩЕНИЕ (отфильтровано)")
        print(f"📍 Источник: {chat_title}")
        print(f"🆔 Message ID: {event.id}")
        print(sender_info)

        if chat_username:
            print(f"🔗 @{chat_username}")

        print("=" * 60)

        # ====================================================
        # ФОРМИРУЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ
        # ====================================================

        header = f"📩 НОВОЕ СООБЩЕНИЕ\n"
        header += f"📍 Источник: {chat_title}\n"
        header += f"🆔 Message ID: {event.id}\n"

        if sender_info:
            header += sender_info

        if chat_username:
            header += f"🔗 https://t.me/{chat_username}/{event.id}\n"

        if message_text:
            max_len = 3500
            if len(message_text) > max_len:
                message_text = message_text[:max_len] + "\n\n... (текст обрезан)"
            full_text = header + "\n" + "=" * 40 + "\n\n" + message_text
        else:
            full_text = header + "\n" + "⚠️ Сообщение без текста (возможно, медиа)"

        # ====================================================
        # ОТПРАВЛЯЕМ ТЕКСТ
        # ====================================================

        try:
            await client.send_message(
                DESTINATION_CHAT,
                full_text
            )
            print("✅ Текст сообщения отправлен в fresh offers")

        except Exception as e:
            print(f"❌ Ошибка отправки текста: {e}")

        # ====================================================
        # ЕСЛИ ЕСТЬ ФОТО — СКАЧИВАЕМ И ОТПРАВЛЯЕМ
        # ====================================================

        if message.photo:
            try:
                path = await message.download_media()
                if path:
                    await client.send_file(
                        DESTINATION_CHAT,
                        path,
                        caption=f"📸 Вложение из {chat_title}"
                    )
                    print("✅ Фото отправлено")
                    try:
                        os.remove(path)
                    except:
                        pass
            except Exception as e:
                print(f"❌ Ошибка при отправке фото: {e}")

        # ====================================================
        # ЕСЛИ ЕСТЬ ДОКУМЕНТ — СКАЧИВАЕМ И ОТПРАВЛЯЕМ
        # ====================================================

        if message.document:
            try:
                path = await message.download_media()
                if path:
                    await client.send_file(
                        DESTINATION_CHAT,
                        path,
                        caption=f"📄 Документ из {chat_title}"
                    )
                    print("✅ Документ отправлен")
                    try:
                        os.remove(path)
                    except:
                        pass
            except Exception as e:
                print(f"❌ Ошибка при отправке документа: {e}")

    except Exception as e:
        logging.exception(
            f"❌ Ошибка мониторинга: {e}"
        )


# ============================================================
# ЗАПУСК
# ============================================================

async def main():

    me = await client.get_me()

    username = (
        f"@{me.username}"
        if me.username
        else "без username"
    )

    print()
    print("✅ SHARMINATOR MONITOR запущен")
    print(f"👤 Аккаунт: {me.first_name} ({username})")

    print()
    print("👀 Отслеживаемые чаты:")

    for chat_id in TARGET_CHATS:
        print(f"   • {chat_id}")

    print()
    print(f"📨 Куда: fresh offers")
    print(f"🆔 Destination: {DESTINATION_CHAT}")
    print(f"🔑 Ключевых слов: {len(KEYWORDS)}")
    print()
    print("⏳ Ожидаю новые сообщения...")
    print()


# ============================================================
# СТАРТ
# ============================================================

with client:

    client.loop.run_until_complete(
        main()
    )

    client.run_until_disconnected()