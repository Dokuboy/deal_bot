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
# TELEGRAM API / RENDER ENV
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
# КУДА ОТПРАВЛЯЕМ
# ============================================================

DESTINATION_CHAT = -5462678076
DESTINATION_TITLE = "fresh offers"

# После запуска сюда будет записан реальный InputPeer
destination_peer = None


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

    # CRG
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

    # REF
    "ref",
    "refs",
    "referral",
    "referrals",
    "referral traffic",
    "ref traffic",

    # РЕФ
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

    # CPL
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
# НОРМАЛИЗАЦИЯ
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

            matched_words.append(
                keyword
            )

    return matched_words


# ============================================================
# ПОИСК DESTINATION ЧАТА
# ============================================================

async def resolve_destination():

    global destination_peer

    logger.info(
        "🔎 Ищу чат fresh offers среди диалогов..."
    )

    # StringSession хранит авторизацию,
    # но entity cache нужно заполнить после запуска.
    dialogs = await client.get_dialogs(
        limit=None
    )

    logger.info(
        f"📚 Загружено диалогов: {len(dialogs)}"
    )

    destination_peer = None


    # --------------------------------------------------------
    # 1. Сначала ищем по ID
    # --------------------------------------------------------

    for dialog in dialogs:

        dialog_id = dialog.id

        entity_id = getattr(
            dialog.entity,
            "id",
            None
        )

        if (
            dialog_id == DESTINATION_CHAT
            or entity_id == abs(DESTINATION_CHAT)
        ):

            destination_peer = dialog.input_entity

            logger.info(
                f"✅ Destination найден по ID: "
                f"{dialog.name} | "
                f"dialog.id={dialog_id} | "
                f"entity.id={entity_id}"
            )

            return destination_peer


    # --------------------------------------------------------
    # 2. Если ID не совпал — ищем по названию
    # --------------------------------------------------------

    for dialog in dialogs:

        dialog_name = (
            dialog.name
            or ""
        ).strip()

        if (
            dialog_name.casefold()
            == DESTINATION_TITLE.casefold()
        ):

            destination_peer = dialog.input_entity

            logger.info(
                f"✅ Destination найден по названию: "
                f"{dialog.name} | "
                f"dialog.id={dialog.id}"
            )

            return destination_peer


    # --------------------------------------------------------
    # Не нашли
    # --------------------------------------------------------

    logger.error(
        "❌ fresh offers не найден среди диалогов."
    )

    logger.error(
        f"❌ Ожидался ID: {DESTINATION_CHAT}"
    )

    raise RuntimeError(
        "Чат fresh offers не найден среди "
        "диалогов Telethon-аккаунта."
    )


# ============================================================
# НОВЫЕ СООБЩЕНИЯ
# ============================================================

@client.on(
    events.NewMessage(
        incoming=True
    )
)
async def monitor_message(event):

    global destination_peer

    try:

        # ----------------------------------------------------
        # Проверяем, что это один из наших 6 чатов
        # ----------------------------------------------------

        if event.chat_id not in TARGET_CHATS:
            return


        # Если сообщение прилетело в момент запуска,
        # а destination ещё не готов
        if destination_peer is None:

            logger.warning(
                "⚠️ Destination ещё не готов. "
                "Сообщение пропущено."
            )

            return


        message = event.message

        message_text = (
            message.raw_text
            or ""
        )


        # ----------------------------------------------------
        # Получаем данные чата и автора
        # ----------------------------------------------------

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
        # ФИЛЬТР
        # ----------------------------------------------------

        matched_words = find_keywords(
            message_text
        )


        if not matched_words:

            print(
                f"⏭️ Пропущено "
                f"[{chat_title}]: "
                f"{message_text[:80]}..."
            )

            return


        # ----------------------------------------------------
        # ИНФОРМАЦИЯ ОБ ОТПРАВИТЕЛЕ
        # ----------------------------------------------------

        sender_name = "Неизвестно"
        sender_username = None
        sender_id = None


        if sender:

            first_name = (
                getattr(
                    sender,
                    "first_name",
                    ""
                )
                or ""
            )

            last_name = (
                getattr(
                    sender,
                    "last_name",
                    ""
                )
                or ""
            )


            sender_name = (
                f"{first_name} {last_name}"
                .strip()
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
        # ЛОГИ
        # ----------------------------------------------------

        print()
        print("=" * 70)

        print(
            "📩 НАЙДЕНО ПОДХОДЯЩЕЕ СООБЩЕНИЕ"
        )

        print(
            f"📍 Источник: {chat_title}"
        )

        print(
            f"🆔 Message ID: {event.id}"
        )

        print(
            f"👤 Отправитель: {sender_name}"
        )


        if sender_username:

            print(
                f"🔹 Username: "
                f"@{sender_username}"
            )


        if sender_id:

            print(
                f"🆔 Sender ID: "
                f"{sender_id}"
            )


        print(
            f"🔑 Совпадения: "
            f"{', '.join(matched_words[:10])}"
        )

        print("=" * 70)


        # ----------------------------------------------------
        # Получаем InputPeer ИСХОДНОГО ЧАТА
        #
        # Это надёжнее, чем передавать только числовой ID.
        # ----------------------------------------------------

        source_peer = await event.get_input_chat()


        # ----------------------------------------------------
        # ПЕРЕСЫЛКА
        # ----------------------------------------------------

        try:

            await client.forward_messages(
                destination_peer,
                event.id,
                from_peer=source_peer
            )


            print(
                f"✅ Переслано в fresh offers "
                f"из {chat_title}"
            )


        # ----------------------------------------------------
        # ЕСЛИ В ЧАТЕ ЗАПРЕЩЕНА ПЕРЕСЫЛКА
        # ----------------------------------------------------

        except ChatForwardsRestrictedError:

            print(
                f"🔒 В чате запрещена пересылка: "
                f"{chat_title}"
            )

            # ====================================================
            # ОТПРАВЛЯЕМ ТЕКСТ СООБЩЕНИЯ, А НЕ ТОЛЬКО УВЕДОМЛЕНИЕ
            # ====================================================

            # Формируем текст сообщения
            full_text = f"📩 НОВОЕ СООБЩЕНИЕ (защищённый чат)\n\n"
            full_text += f"📍 Источник: {chat_title}\n"
            full_text += f"👤 Отправитель: {sender_name}\n"

            if sender_username:
                full_text += f"🔹 Username: @{sender_username}\n"

            if sender_id:
                full_text += f"🆔 Sender ID: {sender_id}\n"

            full_text += f"🆔 Message ID: {event.id}\n"
            full_text += f"🔑 Ключи: {', '.join(matched_words[:10])}\n\n"

            # ДОБАВЛЯЕМ САМ ТЕКСТ СООБЩЕНИЯ
            full_text += "=" * 50 + "\n\n"
            full_text += message_text  # ← САМО СООБЩЕНИЕ

            # Если чат публичный — добавляем ссылку
            if chat_username:
                full_text += (
                    f"\n\n🔗 Открыть оригинал:\n"
                    f"https://t.me/{chat_username}/{event.id}"
                )

            # Отправляем текст в fresh offers
            try:
                await client.send_message(
                    destination_peer,
                    full_text
                )
                print("📨 Текст сообщения отправлен в fresh offers")
            except Exception as e:
                print(f"❌ Ошибка отправки текста: {e}")


        except Exception as e:

            logger.exception(
                f"❌ Ошибка пересылки "
                f"в fresh offers: {e}"
            )


    except Exception as e:

        logger.exception(
            f"❌ Ошибка Telegram Monitor: {e}"
        )


# ============================================================
# START MONITOR
# ============================================================

async def start_monitor():

    global destination_peer

    logger.info(
        "🔄 Подключение Telethon..."
    )


    # --------------------------------------------------------
    # Подключаемся
    # --------------------------------------------------------

    await client.connect()


    # --------------------------------------------------------
    # Проверяем StringSession
    # --------------------------------------------------------

    authorized = (
        await client.is_user_authorized()
    )


    if not authorized:

        await client.disconnect()

        raise RuntimeError(
            "TELEGRAM_STRING_SESSION "
            "не авторизована."
        )


    # --------------------------------------------------------
    # Наш аккаунт
    # --------------------------------------------------------

    me = await client.get_me()


    username = (
        f"@{me.username}"
        if me.username
        else "без username"
    )


    logger.info(
        f"👤 Telethon аккаунт: "
        f"{me.first_name} ({username})"
    )


    # --------------------------------------------------------
    # ВАЖНО:
    # Загружаем диалоги и находим fresh offers.
    # --------------------------------------------------------

    await resolve_destination()


    # --------------------------------------------------------
    # Готово
    # --------------------------------------------------------

    logger.info(
        "✅ SHARMINATOR MONITOR подключён"
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
        f"📨 Destination ID: "
        f"{DESTINATION_CHAT}"
    )


    logger.info(
        "✅ fresh offers готов "
        "к приёму сообщений"
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
# ЛОКАЛЬНЫЙ ЗАПУСК
# ============================================================

async def run_standalone():

    await start_monitor()

    print()
    print(
        "✅ SHARMINATOR MONITOR запущен"
    )
    print(
        "⏳ Ожидаю новые сообщения..."
    )
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
