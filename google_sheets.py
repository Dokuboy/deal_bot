import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_ID, SHEET_NAME
import json
import os

def get_sheet():
    """Подключение к Google Sheets с полной диагностикой"""
    try:
        # Проверяем, существует ли файл
        if not os.path.exists("credentials.json"):
            print("❌ Файл credentials.json НЕ НАЙДЕН в текущей директории!")
            print(f"Текущая директория: {os.getcwd()}")
            print(f"Содержимое: {os.listdir('.')}")
            raise FileNotFoundError("credentials.json не найден")
        
        # Проверяем, что файл читается
        with open("credentials.json", "r") as f:
            data = json.load(f)
            print(f"✅ credentials.json загружен. client_email: {data.get('client_email', 'НЕ НАЙДЕН')}")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        print("✅ Авторизация в Google прошла успешно!")
        
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        print(f"✅ Подключение к листу '{SHEET_NAME}' успешно!")
        print(f"📊 Количество строк: {len(sheet.get_all_values())}")
        return sheet
        
    except FileNotFoundError as e:
        print(f"❌ Файл не найден: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в JSON файле: {e}")
        raise
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ Таблица с ID '{SHEET_ID}' не найдена")
        print(f"   Проверьте, что ID правильный и доступ открыт")
        raise
    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ Лист с именем '{SHEET_NAME}' не найден")
        print(f"   Проверьте название вкладки в таблице")
        raise
    except Exception as e:
        print(f"❌ Неизвестная ошибка подключения: {e}")
        print(f"Тип ошибки: {type(e)}")
        raise

def add_deal_to_sheet(deal_data):
    """Запись данных с полной диагностикой"""
    try:
        print(f"📝 Пытаюсь записать: {deal_data}")
        print(f"📊 Количество полей: {len(deal_data)}")
        
        sheet = get_sheet()
        sheet.append_row(deal_data)
        print(f"✅ Записано: {deal_data}")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА при записи: {e}")
        print(f"Тип ошибки: {type(e)}")
        print(f"Данные: {deal_data}")
        
        # Выводим полный traceback
        import traceback
        traceback.print_exc()
        raise

def get_last_rows(n=10):
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        if len(all_rows) <= 1:
            return []
        return all_rows[-n:] if len(all_rows) <= n+1 else all_rows[-(n):]
    except Exception as e:
        print(f"❌ ОШИБКА при чтении: {e}")
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
        print(f"❌ Ошибка поиска: {e}")
        return None, None

def update_deal_by_id(deal_id, new_row_data):
    try:
        sheet = get_sheet()
        _, row_index = find_deal_by_id(deal_id)
        if row_index is None:
            print(f"❌ Сделка {deal_id} не найдена")
            return False
        cell_range = f"A{row_index}:J{row_index}"
        sheet.update(cell_range, [new_row_data[:10]])
        print(f"✅ Сделка {deal_id} обновлена (строка {row_index})")
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        return False
