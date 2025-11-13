import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SA_JSON, SPREADSHEET_NAME


def connect():
    # Обязательные права для таблиц
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Преобразуем JSON ключа в dict
    service_account_info = json.loads(GOOGLE_SA_JSON)

    # Авторизация сервис-аккаунта
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    client = gspread.authorize(creds)
    return client


def load_products():
    client = connect()

    # Открываем таблицу Products -> первая вкладка
    sheet = client.open("Products").sheet1
    rows = sheet.get_all_records()

    products = []

    for r in rows:
        variants = []

        # variants = JSON строка => превращаем в массив
        if r.get("variants"):
            try:
                variants = json.loads(r["variants"])
            except:
                variants = []

        products.append({
            "id": str(r["id"]),
            "category": r["category"],
            "name": r["name"],
            "description": r.get("description") or "",
            "base_price": int(r.get("base_price") or 0),
            "variants": variants,  # список с вариациями и ценами
            "photo": r.get("photo_url") or "",
            "active": str(r.get("active", "")).lower() in ("true", "1", "yes")
        })

    # Фильтруем только активные товары
    return [p for p in products if p["active"]]


def add_order(order):
    client = connect()

    sheet = client.open(SPREADSHEET_NAME).sheet1

    sheet.append_row([
        order["tg_id"],
        order["name"],
        order["phone"],
        order["address"],
        order["items"],  # строка с товарами
        order["total"]   # итоговая сумма
    ])
