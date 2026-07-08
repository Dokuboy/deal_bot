import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_ID, SHEET_NAME

def get_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        print("✅ Подключение к Google Sheets успешно!")
        return sheet
    except Exception as e:
        print(f"❌ Ошибка подключения к Google Sheets: {e}")
        raise e

def add_deal_to_sheet(deal_data):
    try:
        sheet = get_sheet()
        sheet.append_row(deal_data)
        print(f"✅ Записано: {deal_data}")
        return True
    except Exception as e:
        print(f"❌ ОШИБКА при записи: {e}")
        raise e

def get_last_rows(n=10):
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        if len(all_rows) <= 1:
            return []
        # Пропускаем заголовки (первая строка)
        return all_rows[-n:] if len(all_rows) <= n+1 else all_rows[-(n):]
    except Exception as e:
        print(f"❌ ОШИБКА при чтении: {e}")
        return []

def find_deal_by_id(deal_id):
    """Находит строку с указанным ID (первый столбец) и возвращает (row_data, row_index)"""
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        
        for idx, row in enumerate(all_rows, start=1):
            if idx == 1:  # Пропускаем заголовки
                continue
            if row and row[0].strip() == str(deal_id):
                return row, idx
        
        return None, None
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return None, None

def update_deal_by_id(deal_id, new_row_data):
    """Обновляет строку с указанным ID (первый столбец)"""
    try:
        sheet = get_sheet()
        _, row_index = find_deal_by_id(deal_id)
        
        if row_index is None:
            print(f"❌ Сделка {deal_id} не найдена")
            return False
        
        # Обновляем строку (10 столбцов)
        cell_range = f"A{row_index}:J{row_index}"
        sheet.update(cell_range, [new_row_data[:10]])  # Берём первые 10 полей
        print(f"✅ Сделка {deal_id} обновлена (строка {row_index})")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        return False