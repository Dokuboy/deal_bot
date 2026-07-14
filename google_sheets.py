import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_ID, SHEET_NAME
import json
import os
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_sheet():
    """Подключение к Google Sheets с полной диагностикой"""
    try:
        # Проверяем, существует ли файл
        if not os.path.exists("credentials.json"):
            logger.error("❌ Файл credentials.json НЕ НАЙДЕН в текущей директории!")
            logger.error(f"Текущая директория: {os.getcwd()}")
            logger.error(f"Содержимое: {os.listdir('.')}")
            raise FileNotFoundError("credentials.json не найден")
        
        # Проверяем, что файл читается
        with open("credentials.json", "r") as f:
            data = json.load(f)
            logger.info(f"✅ credentials.json загружен. client_email: {data.get('client_email', 'НЕ НАЙДЕН')}")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        logger.info("✅ Авторизация в Google прошла успешно!")
        
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        logger.info(f"✅ Подключение к листу '{SHEET_NAME}' успешно!")
        logger.info(f"📊 Количество строк: {len(sheet.get_all_values())}")
        return sheet
        
    except FileNotFoundError as e:
        logger.error(f"❌ Файл не найден: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка в JSON файле: {e}")
        raise
    except gspread.exceptions.SpreadsheetNotFound as e:
        logger.error(f"❌ Таблица с ID '{SHEET_ID}' не найдена")
        logger.error(f"   Проверьте, что ID правильный и доступ открыт")
        logger.error(f"   Ошибка: {e}")
        raise
    except gspread.exceptions.WorksheetNotFound as e:
        logger.error(f"❌ Лист с именем '{SHEET_NAME}' не найден")
        logger.error(f"   Проверьте название вкладки в таблице")
        logger.error(f"   Ошибка: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка подключения: {e}")
        logger.error(f"Тип ошибки: {type(e)}")
        raise

def add_deal_to_sheet(deal_data):
    """Запись данных с полной диагностикой"""
    try:
        logger.info(f"📝 Пытаюсь записать: {deal_data}")
        logger.info(f"📊 Количество полей: {len(deal_data)}")
        
        sheet = get_sheet()
        sheet.append_row(deal_data)
        logger.info(f"✅ Записано: {deal_data}")
        return True
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА при записи: {e}")
        logger.error(f"Тип ошибки: {type(e)}")
        logger.error(f"Данные: {deal_data}")
        
        import traceback
        logger.error(traceback.format_exc())
        raise

def get_last_rows(n=10):
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        if len(all_rows) <= 1:
            return []
        return all_rows[-n:] if len(all_rows) <= n+1 else all_rows[-(n):]
    except Exception as e:
        logger.error(f"❌ ОШИБКА при чтении: {e}")
        return []

def find_deal_by_id(deal_id):
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        for idx, row in enumerate(all_rows, start=1):
            if idx == 1:
                continue
            if row and row[0].strip() == str(deal_id):
                return row, idx
        return None, None
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        return None, None

def update_deal_by_id(deal_id, new_row_data):
    try:
        sheet = get_sheet()
        _, row_index = find_deal_by_id(deal_id)
        if row_index is None:
            logger.error(f"❌ Сделка {deal_id} не найдена")
            return False
        cell_range = f"A{row_index}:J{row_index}"
        sheet.update(cell_range, [new_row_data[:10]])
        logger.info(f"✅ Сделка {deal_id} обновлена (строка {row_index})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка обновления: {e}")
        return False
