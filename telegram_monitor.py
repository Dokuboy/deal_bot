import os
import re
import json
import asyncio
import logging
import unicodedata
import hashlib

import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
SHEET_ID = os.environ["SHEET_ID"]


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
    -1001977656258,  # whiteaffiliate
    -1001039329051,  # @macpreparty
]


# ============================================================
# КУДА ОТПРАВЛЯЕМ
# ============================================================

DESTINATION_CHAT = -5462678076
DESTINATION_TITLE = "fresh offers"

destination_peer = None


# ============================================================
# ЧЁРНЫЙ СПИСОК (Google Sheets)
# ============================================================

BANNED_SHEET_NAME = "BannedUsers"


def get_banned_sheet():
    """Подключается к листу BannedUsers в Google Таблице"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client_gs = gspread.authorize(creds)
    sheet = client_gs.open_by_key(SHEET_ID).worksheet(BANNED_SHEET_NAME)
    return sheet


def load_banned_users():
    """
    Загружает чёрный список из Google Sheets.
    Возвращает словарь: {user_id: {"username": ..., "name": ...}}
    """
    try:
        sheet = get_banned_sheet()
        rows = sheet.get_all_values()
        banned = {}
        for row in rows[1:]:
            if row and row[0].strip():
                try:
                    user_id = int(row[0].strip())
                    banned[user_id] = {
                        "username": row[1] if len(row) > 1 else "",
                        "name": row[2] if len(row) > 2 else ""
                    }
                except ValueError:
                    continue
        print(f"✅ Загружено {len(banned)} забаненных из Google Sheets")
        return banned
    except Exception as e:
        print(f"⚠️ Ошибка загрузки чёрного списка: {e}")
        return {}


def save_banned_users(banned):
    """Сохраняет чёрный список в Google Sheets"""
    try:
        sheet = get_banned_sheet()
        sheet.clear()
        sheet.append_row(["ID", "Username", "Name"])
        for user_id, info in banned.items():
            sheet.append_row([
                user_id,
                info.get("username", ""),
                info.get("name", "")
            ])
        print(f"✅ Сохранено {len(banned)} забаненных в Google Sheets")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения чёрного списка: {e}")
        return False


# Загружаем чёрный список при старте
BANNED_USERS = load_banned_users()


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
# КОДЫ СТРАН (ищутся ОТДЕЛЬНО, как целые слова)
# ============================================================

GEO_CODES = [
    "AT", "BE", "CH", "CZ", "DE", "DK", "ES", "FI", "FR", "GB", "GR",
    "HU", "IE", "IT", "LT", "LU", "LV", "NL", "NO", "PL", "PT",
    "RO", "SE", "SI", "SK", "UK",
    "AR", "BO", "BR", "CL", "CO", "CR", "DO", "EC", "GT", "HN", "MX",
    "NI", "PA", "PE", "PY", "PR", "SV", "UY", "VE",
    "AE", "BH", "CN", "HK", "ID", "IL", "JP", "KR", "KW", "KZ",
    "MY", "PH", "PK", "QA", "SA", "SG", "TH", "TR", "TW", "VN",
]


# ============================================================
# МИНУС-СЛОВА (СТОП-СЛОВА)
# ============================================================

STOP_WORDS = [
    # === БАЗОВЫЕ ===
    "payment", "platform", "stripe", "paypal", "wise",
    "square", "sumup", "payoneer", "revolut", "geegpay",
    "visanet", "authorize.net", "flutterwave", "fresh",
    "bank", "documents", "retention", "signals", "tools",
    "recovery", "registration", "database", "api integration",
    "igaming", "платформа", "admin", "services", "ru",
    "чардж", "charge", "рекавери", "база", "варм",
    "холодка", "реги", "regs", "depositors", "osys",
    "reputation", "работа", "дроповод", "дроп", "domains",
    "подработка", "serm", "orm", "blackhat", "hosting",
    "ру", "реквизиты", "видео", "max",
    "provider", "sms", "data", "бан", "accounts",
    "телефония", "деньги", "вотсап", "Подработка",
    "Паспорт", "Обмен", "Обучение", "Content", "воркер",
    "vip", "игроки", "аккаунты", "фарм", "прокси",
    "доки", "агентские", "физ сим", "пополнение",

    "базы", "базу", "базе", "базой", "баз",
    "аккаунт", "аккаунта", "аккаунту", "аккаунтом", "аккаунтах",
    "фармы", "фармов", "фармам", "фармами", "фармах",
    "доки", "доков", "докам", "доками", "доках",
    "реферал", "рефералы", "реферала", "рефералов",
    "трастовые", "трастовых", "трастовым", "трастовыми",
    "выдача", "выдачи", "выдачу", "выдаче", "выдачей",

    "gambling", "gamble", "gambler", "gamblers",
    "гемблинг", "гембла", "гемблер",

    "nutra", "нутры", "нутра",

    "video", "videos", "видео",
    "motion", "motions",

    "design", "designs", "designer", "designers",
    "дизайн", "дизайна", "дизайну", "дизайном", "дизайны",
    "дизайнер", "дизайнера", "дизайнеров",

    "документы", "документов", "документам", "документами", "документах",
    "документ", "документом", "документе",
    "документик", "документика", "документику", "документиком",
    "документики", "документиков", "документикам", "документиками", "документиках",
    "док", "дока", "доку", "доком", "доки", "доков", "докам", "доками", "доках",
    "докер", "докера", "докеру", "докером", "докеры", "докеров", "докерам", "докерами", "докерах",
    "паспорт", "паспорта", "паспорту", "паспортом", "паспорты",
    "паспортов", "паспортам", "паспортами", "паспортах",
    "паспортик", "паспортикa", "паспортику", "паспортиком",
    "паспортики", "паспортиков", "паспортикам", "паспортиками", "паспортиках",
    "удостоверение", "удостоверения", "удостоверению", "удостоверением", "удостоверении",
    "удостоверенье", "удостоверенья", "удостоверенью", "удостовереньем",
    "удостоверенье", "удостовереньи", "удостоверений",
    "удостоверениям", "удостоверениями", "удостоверениях",
    "водительские", "водительского", "водительскому", "водительским",
    "водительскими", "водительских", "водительское", "водительская",
    "водительской", "водительскую", "водительские", "водительских",
    "водительским", "водительскими", "водительские",
    "selfie", "селфи", "id", "айди", "айдишник", "айдишника",
    "айдишнику", "айдишником", "айдишники", "айдишников",
    "айдишникам", "айдишниками", "айдишниках",

    "wire", "wires", "iban", "ibans", "ибан", "ибаны",
    "settlement", "settlements", "расчет", "расчеты",
    "расчета", "расчетов", "interac", "usdt", "c2b",
    "business", "бизнес", "бизнеса", "бизнесу", "бизнесом",
    "бизнесы", "бизнесов", "client name", "имя клиента",
    "client", "клиент", "клиента", "клиенту", "клиентом",
    "клиенты", "клиентов",

    "заработок", "заработка", "заработку", "заработком",
    "заработки", "заработков", "новичок", "новичка",
    "новичку", "новичком", "новички", "новичков",
    "бесплатный", "бесплатно", "бесплатная", "бесплатные",
    "бесплатного", "бесплатной", "бесплатных", "вход бесплатный",

    "otc", "fiat", "global otc", "zero risk",
    "safety period", "we pay first", "disbursal",
    "acepay_exc", "acepay_otc_bot", "обменник", "обмен",
    "крипта", "криптовалюта", "usd", "eur", "gbp",
    "sgd", "cny", "inr", "bdt", "pkr", "krw",
    "aed", "try", "myr", "thb", "vnd", "idr", "brl",
    "депозит", "деп", "вывод", "выплата", "payout",

    "высокий доход", "доход", "дохода", "доходу", "доходом",
    "доходы", "доходов", "500 тыс", "повышенный риск",
    "безопасность", "анонимность", "обучаем", "сопровождаем",
    "страхуем", "без залога", "карьерный рост",
    "доходность", "доходности", "финансовые проблемы", "финансовые цели",

    "dhm_2d3d371cbot", "dhm_754b721ebot", "dhm_868687fdbot",
    "dhm_da531fcabot",
    "dhm_", "dhm",

    "рассылка", "рассылки", "рассылку", "рассылке", "рассылкой", "рассылок",
    "телеграм рассылка",
    "реклама", "рекламы", "рекламу", "рекламе", "рекламой",
    "подписчиков", "подписчики", "подписчик",
    "прайс", "прайс рекламы",
    "сообщений", "сообщения",
    "канал", "каналы", "каналов",

    "chargebacks", "chargeback",
    "ready ftds", "ftds", "ftd",
    "flash coins", "flash cions", "flash",
    "secure your leads",
    "global coverage",
    "premium services",

    "ssn", "ssn+dob", "dob", "dl", "mmn", "mvr", "mvr+dl",
    "cs", "cs+cr", "bg", "ein", "tlo",
    "reverse ssn", "reverse phone", "reverse email",
    "prof license",
    "pricelist", "price list", "lookup service",
    "look up service", "lookup", "look up",
    "blessfinder", "blesslookup", "bless",
    "ssn lookup", "ssn dob", "data lookup",
    "background check", "background lookup",
    "fullz", "full info", "personal info",
    "dox", "doxx", "doxbin",
    "tlo lookup", "tlo service",
    "tracers", "skip trace", "skip tracing",
    "leads lookup", "find person", "find people",

    "xxin7", "xxin7_bot", "xxxin7_bot",
    "ylpay", "ylpay_868", "ylpay_868_bot",
    "want to make money",
    "stable daily income",
    "usdt purchasing",
    "hong kong-mainland",
    "f2f cash",
    "usdt to sell",
    "天赐代发",
    "此号不回",
    "代发广告联系天赐小新",
    "双向机器人",
    "24小时自助",
    "飞机号铺",
    "this group can't be displayed",
    "violated local laws",
]


# ============================================================
# ЗАМЕНА ГОМОГЛИФОВ (латиница → кириллица)
# ============================================================

HOMOGLYPHS = {
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х',
    'y': 'у', 'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н',
    'K': 'К', 'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х',
    'Y': 'У',
}


def replace_homoglyphs(text: str) -> str:
    if not text:
        return ""
    result = []
    for char in text:
        result.append(HOMOGLYPHS.get(char, char))
    return ''.join(result)


# ============================================================
# ЗАЩИТА ОТ ДУБЛИКАТОВ
# ============================================================

sent_texts = set()


def get_text_hash(text: str) -> str:
    if not text:
        return ""
    normalized = normalize_text_for_filter(text)
    normalized = ' '.join(normalized.split())
    return hashlib.md5(normalized.encode()).hexdigest()


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

def normalize_text_for_filter(text: str) -> str:
    if not text:
        return ""
    text = replace_homoglyphs(text)
    normalized = unicodedata.normalize('NFKC', text)
    cleaned = re.sub(r'[^\w\s]', ' ', normalized)
    cleaned = cleaned.lower()
    cleaned = ' '.join(cleaned.split())
    return cleaned


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = replace_homoglyphs(text)
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


def find_geo_codes(text: str):
    if not text:
        return []
    matched = []
    for code in GEO_CODES:
        pattern = rf"(?<![A-Za-z]){re.escape(code)}(?![A-Za-z])"
        if re.search(pattern, text, re.IGNORECASE):
            matched.append(code)
    return matched


# ============================================================
# ПОИСК DESTINATION ЧАТА
# ============================================================

async def resolve_destination():
    global destination_peer

    logger.info("🔎 Ищу чат fresh offers среди диалогов...")
    dialogs = await client.get_dialogs(limit=None)
    logger.info(f"📚 Загружено диалогов: {len(dialogs)}")

    destination_peer = None

    for dialog in dialogs:
        dialog_id = dialog.id
        entity_id = getattr(dialog.entity, "id", None)
        if dialog_id == DESTINATION_CHAT or entity_id == abs(DESTINATION_CHAT):
            destination_peer = dialog.input_entity
            logger.info(f"✅ Destination найден по ID: {dialog.name}")
            return destination_peer

    for dialog in dialogs:
        dialog_name = (dialog.name or "").strip()
        if dialog_name.casefold() == DESTINATION_TITLE.casefold():
            destination_peer = dialog.input_entity
            logger.info(f"✅ Destination найден по названию: {dialog.name}")
            return destination_peer

    logger.error("❌ fresh offers не найден среди диалогов.")
    raise RuntimeError("Чат fresh offers не найден среди диалогов Telethon-аккаунта.")


# ============================================================
# НОВЫЕ СООБЩЕНИЯ
# ============================================================

@client.on(events.NewMessage(incoming=True))
async def monitor_message(event):
    global destination_peer

    try:
        if event.chat_id not in TARGET_CHATS:
            return

        if event.sender_id in BANNED_USERS:
            print(f"⏭️ Пропущено (в чёрном списке): {event.sender_id}")
            return

        if destination_peer is None:
            return

        message = event.message
        message_text = message.raw_text or ""

        chat = await event.get_chat()
        sender = await event.get_sender()

        sender_username = getattr(sender, "username", None) if sender else None
        chat_title = getattr(chat, "title", "Unknown chat")
        chat_username = getattr(chat, "username", None)

        normalized_text = normalize_text_for_filter(message_text)
        simple_lower = message_text.lower()

        stop_word_found = False
        for stop_word in STOP_WORDS:
            word_lower = stop_word.lower()
            if word_lower in normalized_text or word_lower in simple_lower:
                print(f"⏭️ Пропущено (стоп-слово '{stop_word}') [{chat_title}]")
                stop_word_found = True
                break
        if stop_word_found:
            return

        matched_words = find_keywords(message_text)
        matched_geos = find_geo_codes(message_text)

        if not matched_words and not matched_geos:
            return

        all_matches = matched_words + matched_geos

        sender_id = getattr(sender, "id", None) if sender else None
        if sender_id:
            text_hash = get_text_hash(message_text)
            unique_key = (sender_id, text_hash)
            if unique_key in sent_texts:
                return
            sent_texts.add(unique_key)
            if len(sent_texts) > 10000:
                for _ in range(1000):
                    if sent_texts:
                        sent_texts.pop()

        sender_name = "Неизвестно"
        if sender:
            first_name = getattr(sender, "first_name", "") or ""
            last_name = getattr(sender, "last_name", "") or ""
            sender_name = f"{first_name} {last_name}".strip() or "Без имени"

        full_text = f"📩 НОВОЕ СООБЩЕНИЕ\n\n"
        full_text += f"📍 Источник: {chat_title}\n"
        full_text += f"👤 Отправитель: {sender_name}\n"
        if sender_username:
            full_text += f"🔹 Username: @{sender_username}\n"
            full_text += f"👤 Профиль: https://t.me/{sender_username}\n"
        if sender_id:
            full_text += f"🆔 Sender ID: {sender_id}\n"
        full_text += f"🆔 Message ID: {event.id}\n"
        full_text += f"🔑 Ключи: {', '.join(all_matches[:15])}\n\n"
        full_text += "=" * 50 + "\n\n"
        full_text += message_text
        if chat_username:
            full_text += f"\n\n🔗 Открыть оригинал:\nhttps://t.me/{chat_username}/{event.id}"

        try:
            await client.send_message(destination_peer, full_text)
            print(f"📨 Отправлено в fresh offers из {chat_title}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")

    except Exception as e:
        logger.exception(f"❌ Ошибка Telegram Monitor: {e}")


# ============================================================
# ОБРАБОТКА ОТВЕТОВ "бан" / "ban" В FRESH OFFERS
# ============================================================

# Кэш для хранения sender_id по message_id
last_sender_by_msg_id = {}


@client.on(events.NewMessage())
async def handle_ban_command(event):
    """
    Ловит ВСЕ сообщения и проверяет, что это fresh offers + команда бан.
    Фильтр по чату убран — проверяем вручную по ID.
    """
    try:
        # Проверяем, что сообщение из fresh offers
        if event.chat_id != DESTINATION_CHAT:
            return

        # Запоминаем sender_id каждого сообщения
        last_sender_by_msg_id[event.message.id] = {
            "sender_id": event.sender_id,
        }

        if len(last_sender_by_msg_id) > 2000:
            keys = list(last_sender_by_msg_id.keys())
            for k in keys[:1000]:
                last_sender_by_msg_id.pop(k, None)

        text = (event.message.raw_text or "").strip().lower()

        print(f"📥 [BAN] Сообщение в fresh offers: '{text[:40]}' | reply_to={event.message.reply_to_msg_id}")

        if text not in ["бан", "ban", "🚫", "❌"]:
            return

        reply_to = event.message.reply_to_msg_id
        if not reply_to:
            print("⏭️ [BAN] Не ответ на сообщение")
            return

        try:
            original_msg = await client.get_messages(DESTINATION_CHAT, ids=reply_to)
        except Exception as e:
            print(f"❌ [BAN] Ошибка получения оригинала: {e}")
            return

        if not original_msg:
            print("⏭️ [BAN] Оригинал пустой")
            return

        banned_id = None
        username = ""
        name = ""

        # Вариант 1: пересланное сообщение — берём Sender ID из текста
        if original_msg.text:
            match = re.search(r"🆔 Sender ID: (\d+)", original_msg.text)
            if match:
                banned_id = int(match.group(1))
                username_match = re.search(r"🔹 Username: @(\S+)", original_msg.text)
                username = username_match.group(1) if username_match else ""
                name_match = re.search(r"👤 Отправитель: (.+)", original_msg.text)
                name = name_match.group(1).strip() if name_match else ""

        # Вариант 2: бот писал напрямую в fresh offers
        if banned_id is None:
            cached = last_sender_by_msg_id.get(reply_to)
            if cached and cached["sender_id"]:
                banned_id = cached["sender_id"]
                print(f"🔍 [BAN] Беру sender_id из кэша: {banned_id}")

        if not banned_id:
            print("⏭️ [BAN] Не удалось определить ID")
            return

        me = await client.get_me()
        if banned_id == me.id:
            print("⏭️ [BAN] Самобан — пропускаем")
            return

        if banned_id in BANNED_USERS:
            print(f"⏳ [BAN] {banned_id} уже в бане")
            return

        BANNED_USERS[banned_id] = {"username": username, "name": name}
        save_banned_users(BANNED_USERS)

        print(f"🚫 [BAN] Пользователь {banned_id} (@{username}) добавлен")

        try:
            await client.send_message(
                DESTINATION_CHAT,
                f"🚫 Пользователь `{banned_id}` (@{username}) добавлен в чёрный список.",
                reply_to=event.message.id
            )
        except Exception as e:
            print(f"⚠️ Не удалось отправить подтверждение: {e}")

    except Exception as e:
        logger.exception(f"❌ Ошибка обработки команды 'бан': {e}")


# ============================================================
# START MONITOR
# ============================================================

async def start_monitor():
    global destination_peer

    logger.info("🔄 Подключение Telethon...")

    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError("TELEGRAM_STRING_SESSION не авторизована.")

    me = await client.get_me()
    username = f"@{me.username}" if me.username else "без username"
    logger.info(f"👤 Telethon аккаунт: {me.first_name} ({username})")

    await resolve_destination()

    logger.info("✅ SHARMINATOR MONITOR подключён")
    logger.info(f"👀 Отслеживаемых чатов: {len(TARGET_CHATS)}")
    logger.info(f"🔑 Ключевых слов: {len(KEYWORDS)}")
    logger.info(f"🌍 Гео-кодов: {len(GEO_CODES)}")
    logger.info(f"🚫 Стоп-слов: {len(STOP_WORDS)}")
    logger.info(f"🚫 Чёрный список: {len(BANNED_USERS)} пользователей")
    logger.info(f"📨 Destination ID: {DESTINATION_CHAT}")


# ============================================================
# STOP MONITOR
# ============================================================

async def stop_monitor():
    if client.is_connected():
        await client.disconnect()
        logger.info("🛑 Telegram Monitor отключён")


# ============================================================
# ЛОКАЛЬНЫЙ ЗАПУСК
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
        asyncio.run(run_standalone())
    except KeyboardInterrupt:
        print("\n🛑 Монитор остановлен пользователем")
