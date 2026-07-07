import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_ID, SHEET_NAME

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    return sheet

def add_deal_to_sheet(deal_data):
    try:
        sheet = get_sheet()
        sheet.append_row(deal_data)
        print("✅ Успешно записано в таблицу!")
        return True
    except Exception as e:
        print(f"❌ ОШИБКА при записи: {e}")
        print(f"Тип ошибки: {type(e)}")
        raise e

def get_last_rows(n=5):
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        if len(all_rows) <= 1:
            return []
        return all_rows[-n:] if len(all_rows) <= n+1 else all_rows[-(n):]
    except Exception as e:
        print(f"❌ ОШИБКА при чтении: {e}")
        return []