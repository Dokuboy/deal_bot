from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from google_sheets import add_deal_to_sheet, find_deal_by_id, update_deal_by_id, get_last_rows
from openai import OpenAI
from config import DEEPSEEK_API_KEY, ADMIN_ID, BOT_TOKEN
import json
import re

router = Router()
bot = Bot(token=BOT_TOKEN)

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# --- Состояния для обновления ---
class UpdateStates(StatesGroup):
    waiting_for_new_data = State()

# --- Вспомогательные функции ---
def format_priority(priority_str):
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

# --- Команды ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "👋 Бот для автоматического добавления оферов в Google Таблицу.\n\n"
            "📌 Команды:\n"
            "/add - добавить новый офер (или просто отправьте текст с офером)\n"
            "/list - показать последние 10 записей\n"
            "/view {ID} - показать сделку по ID\n"
            "/update {ID} - обновить сделку по ID\n"
            "/cancel - отменить обновление",
            reply_markup=ReplyKeyboardRemove()
        )

@router.message(Command("list"))
async def cmd_list(message: Message):
    rows = get_last_rows(10)
    if not rows:
        await message.answer("📭 В таблице пока нет записей.")
        return
    text = "📋 **Последние 10 записей:**\n\n"
    for i, row in enumerate(rows, 1):
        if len(row) >= 10:
            text += f"{i}. ID: {row[0]}, GEO: {row[1]}, Цена: {row[2]}, Priority: {row[6] or '—'}\n"
        else:
            text += f"{i}. {row[:3]}\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("view"))
async def cmd_view(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажите ID: /view 112323")
        return
    
    deal_id = args[1]
    row, _ = find_deal_by_id(deal_id)
    
    if row is None:
        await message.answer(f"❌ Сделка с ID {deal_id} не найдена.")
        return
    
    text = f"""
📋 **Сделка #{deal_id}**

ID партнера: {row[0]}
GEO: {row[1]}
Цена (без маржи): {row[2]}
Воронка: {row[3]}
Source: {row[4]}
CR: {row[5] or '—'}
Priority: {row[6] or '—'}
Deduction: {row[7] or '—'}
Комментарий: {row[8] or '—'}
Менеджер: {row[9] or '—'}
    """
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("update"))
async def cmd_update(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажите ID: /update 112323")
        return
    
    deal_id = args[1]
    await state.update_data(deal_id=deal_id)
    
    row, _ = find_deal_by_id(deal_id)
    if row is None:
        await message.answer(f"❌ Сделка с ID {deal_id} не найдена.")
        await state.clear()
        return
    
    # Показываем текущие данные
    current = f"""
📋 **Текущие данные сделки #{deal_id}**

GEO: {row[1]}
Цена: {row[2]}
Воронка: {row[3]}
Source: {row[4]}
CR: {row[5] or '—'}
Priority: {row[6] or '—'}
Deduction: {row[7] or '—'}
Комментарий: {row[8] or '—'}
Менеджер: {row[9] or '—'}

📝 Отправьте **НОВЫЕ** данные в формате:
`GEO | Цена | Воронка | Source | CR | Priority | Deduction | Комментарий | Менеджер`

Например:
`UK | CRG 1350$+12% | AIProfitApp, AI CapitalSystem | GG+SEO | CR 13%+ | High | 10% | Новый комментарий | David`

Для отмены отправьте /cancel
    """
    await message.answer(current, parse_mode="Markdown")
    await state.set_state(UpdateStates.waiting_for_new_data)

@router.message(UpdateStates.waiting_for_new_data)
async def process_update(message: Message, state: FSMContext):
    data = await state.get_data()
    deal_id = data.get('deal_id')
    
    # Проверка на отмену
    if message.text.startswith("/cancel"):
        await message.answer("❌ Обновление отменено.")
        await state.clear()
        return
    
    # Парсим строку с данными
    parts = [p.strip() for p in message.text.split('|')]
    if len(parts) < 9:
        await message.answer(
            "❌ Неверный формат. Нужно 9 полей через |\n"
            "Пример: `GEO | Цена | Воронка | Source | CR | Priority | Deduction | Комментарий | Менеджер`",
            parse_mode="Markdown"
        )
        return
    
    # Собираем новую строку с ID
    new_row = [deal_id] + parts  # ID + 9 полей = 10 столбцов
    
    success = update_deal_by_id(deal_id, new_row)
    
    if success:
        await message.answer(f"✅ Сделка #{deal_id} успешно обновлена!")
    else:
        await message.answer(f"❌ Ошибка при обновлении сделки #{deal_id}.")
    
    await state.clear()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Операция отменена.")

# --- Основной обработчик сообщений (добавление новых сделок) ---
@router.message(F.text)
async def parse_deals_with_ai(message: Message):
    user_text = message.text
    chat_id = message.chat.id
    sender_name = message.from_user.full_name

    # Игнорируем команды
    if user_text.startswith('/'):
        return

    # Фильтр ключевых слов
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
                
                # Столбцы: ID партнера | GEO | Цена | Воронка | Source | CR | Priority | Deduction | Комментарий | Менеджер
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