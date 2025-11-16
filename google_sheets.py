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
    Полная загрузка каталога из Google Sheets.
    Поддерживает поля:
    - id
    - category
    - name
    - description
    - base_price
    - our_price
    - supplier
    - variants (JSON)
    - photo_url
    - file_id
    - stock
    - active
    """

    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    products = []

    for row in rows:

        # Пропуск выключенных товаров
        if str(row.get("active")).strip().lower() not in ("true", "1", "yes"):
            continue

        # Разбор variants
        try:
            variants = json.loads(row.get("variants", "")) if row.get("variants") else []
        except:
            variants = []

        # stock (оставляем None если пусто)
        stock_raw = row.get("stock")
        if stock_raw in (None, "", " "):
            stock = None
        else:
            try:
                stock = int(stock_raw)
            except:
                stock = None

        product = {
            "id": str(row.get("id", "")).strip(),
            "category": row.get("category", "Без категории").strip(),
            "name": row.get("name", "Без названия"),
            "description": row.get("description", ""),
            "base_price": row.get("base_price") or 0,
            "our_price": row.get("our_price") or None,
            "supplier": row.get("supplier") or "",
            "variants": variants,
            "photo_url": row.get("photo_url", "").strip(),
            "file_id": row.get("file_id", "").strip(),
            "stock": stock,
            "active": True
        }

        products.append(product)

    return products
