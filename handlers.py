from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from google_sheets import add_deal_to_sheet
from openai import OpenAI
from config import DEEPSEEK_API_KEY, ADMIN_ID, BOT_TOKEN
import json
import re

router = Router()
bot = Bot(token=BOT_TOKEN)

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def format_priority(priority_str):
    """Форматирует Priority из сообщения в читаемый вид"""
    if not priority_str:
        return ""
    p = priority_str.lower().strip()
    if p in ["high", "h"]:
        return "High 🟢"
    elif p in ["middle", "medium", "m"]:
        return "Middle 🟡"
    elif p in ["low", "l"]:
        return "Low 🔴"
    return priority_str

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "👋 Бот для автоматического добавления оферов в Google Таблицу.\n"
            "Просто отправьте офер текстом, и я добавлю его в таблицу.\n"
            "Для Priority укажите: High, Middle или Low.\n"
            "Если Priority не указан — поле останется пустым.",
            reply_markup=ReplyKeyboardRemove()
        )

@router.message(Command("list"))
async def cmd_list(message: Message):
    from google_sheets import get_last_rows
    rows = get_last_rows(10)
    if not rows:
        await message.answer("📭 В таблице пока нет записей.")
        return
    text = "📋 **Последние 10 записей:**\n\n"
    for i, row in enumerate(rows, 1):
        if len(row) >= 10:
            text += f"{i}. GEO: {row[1]}, Цена: {row[2]}, Priority: {row[6] or '—'}\n"
        else:
            text += f"{i}. {row[:3]}\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text)
async def parse_deals_with_ai(message: Message):
    user_text = message.text
    chat_id = message.chat.id
    sender_name = message.from_user.full_name

    keywords = ["CRG", "Daily cap", "AIProfitApp", "QuantSystemAI", "AICapitalPlatform", "CR", "СR",
                "price:", "source:", "Geo:", "Campaign:", "Manager", "id", "deduction", "priority"]
    if not any(kw in user_text for kw in keywords):
        return

    await bot.send_message(ADMIN_ID, f"🔍 Начинаю парсить офер от {sender_name} в чате {chat_id}")

    system_prompt = """
Ты — ассистент, который извлекает данные о сделках из неструктурированного текста.

В тексте могут быть описаны одна или несколько сделок. Каждая сделка обычно содержит:
- Manager (имя менеджера)
- id (цифровой идентификатор)
- Geo (страна или несколько стран, разделённых / или ,)
- price (цена с процентами и вычетами)
- source (источник)
- Campaign (название кампании)
- deduction (вычеты, например: 10%, -10% deductions)
- priority (приоритет: High, Middle, Low — ТОЛЬКО если явно указан в тексте)

Твоя задача — найти все сделки и вернуть их в виде JSON-списка.

Для каждой сделки извлеки поля:
- manager (имя менеджера)
- id (числовой идентификатор)
- geo (строка с географией)
- price (строка с ценой и процентами)
- source (источник)
- campaign (название кампании)
- deduction (строка с вычетами, только цифры и знак %, например: "10%")
- priority (приоритет: High, Middle, Low — ТОЛЬКО если он есть в тексте)

Важно: если priority не указан в тексте — верни пустую строку "".
НЕ придумывай priority, если его нет в сообщении.

Если какое-то поле отсутствует, верни пустую строку "".
Ответ должен содержать ТОЛЬКО JSON-массив без лишнего текста.
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content
        print(f"Ответ от DeepSeek: {ai_response}")
        
        json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
        if json_match:
            ai_response = json_match.group(0)
        
        deals_data = json.loads(ai_response)
        
        if not deals_data or not isinstance(deals_data, list):
            await bot.send_message(ADMIN_ID, f"⚠️ Не удалось распарсить офер от {sender_name}.")
            return
        
        # Разбиваем Geo на отдельные страны
        expanded = []
        for deal in deals_data:
            geo_raw = deal.get('geo', '')
            if '/' in geo_raw or ',' in geo_raw:
                countries = [g.strip() for g in re.split(r'[/,]\s*', geo_raw) if g.strip()]
                for country in countries:
                    new_deal = deal.copy()
                    new_deal['geo'] = country
                    expanded.append(new_deal)
            else:
                expanded.append(deal)
        deals_data = expanded

        success = 0
        for deal in deals_data:
            try:
                price = deal.get('price', '')
                priority_raw = deal.get('priority', '')
                deduction = deal.get('deduction', '')
                
                priority = format_priority(priority_raw) if priority_raw else ""
                
                row = [
                    deal.get('id', ''),
                    deal.get('geo', ''),
                    price,
                    deal.get('campaign', ''),
                    deal.get('source', ''),
                    '',
                    priority,
                    deduction,
                    '',
                    deal.get('manager', sender_name)
                ]
                add_deal_to_sheet(row)
                success += 1
                print(f"✅ Записано: {row}")
            except Exception as e:
                print(f"Ошибка записи: {e}")
                await bot.send_message(ADMIN_ID, f"❌ Ошибка записи: {e}")
        
        if success > 0:
            await bot.send_message(ADMIN_ID, f"✅ Добавлено {success} сделок от {sender_name}")
            await message.answer(f"✅ Добавлено {success} сделок в Google Таблицу!")
        else:
            await bot.send_message(ADMIN_ID, f"⚠️ Офер от {sender_name} не содержал данных для записи.")
            await message.answer("⚠️ Не удалось добавить сделки. Проверьте формат.")

    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        await bot.send_message(ADMIN_ID, f"❌ Ошибка JSON: {e}")
    except Exception as e:
        print(f"Ошибка: {e}")
        await bot.send_message(ADMIN_ID, f"❌ Ошибка обработки: {e}")