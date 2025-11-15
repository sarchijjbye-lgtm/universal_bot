# google_sheets.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# === Load credentials ===
GOOGLE_SHEET_CREDENTIALS = os.getenv("GOOGLE_SHEET_CREDENTIALS")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

if not GOOGLE_SHEET_CREDENTIALS:
    raise Exception("ENV GOOGLE_SHEET_CREDENTIALS missing!")

if not GOOGLE_SHEET_ID:
    raise Exception("ENV GOOGLE_SHEET_ID missing!")

# Convert JSON env string into dict
creds_dict = json.loads(GOOGLE_SHEET_CREDENTIALS)

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)


# === UNIVERSAL: Open sheet by name ===
def connect_to_sheet(sheet_name: str):
    try:
        sh = client.open_by_key(GOOGLE_SHEET_ID)
        return sh.worksheet(sheet_name)
    except Exception as e:
        print(f"[GSHEETS ERROR] Could not open sheet {sheet_name}: {e}")
        raise


# === MAIN LOADER ===
def load_products_safe():
    """
    Структура товара после загрузки:

    {
        "id": "1",
        "category": "Масла",
        "name": "Масло льняное",
        "description": "...",
        "photo_url": "http://...",
        "file_id": "",
        "variants": [
            {"id": "250", "label": "250 мл", "price": 350},
            {"id": "500", "label": "500 мл", "price": 600}
        ],
        "active": True
    }
    """

    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    products = []

    for row in rows:
        # Пропуск неактивных товаров
        if str(row.get("active")).strip().upper() not in ["TRUE", "1", "YES"]:
            continue

        # Разбор вариантов JSON
        try:
            variants = json.loads(row.get("variants", "")) if row.get("variants") else []
        except:
            variants = []

        product = {
            "id": str(row.get("id", "")),
            "category": row.get("category", "Без категории").strip(),
            "name": row.get("name", "Без названия"),
            "description": row.get("description", ""),
            "photo_url": row.get("photo_url", "").strip(),
            "file_id": row.get("file_id", "").strip(),   # локальный кеш Telegram file_id
            "variants": variants,
            "active": True
        }

        products.append(product)

    return products
