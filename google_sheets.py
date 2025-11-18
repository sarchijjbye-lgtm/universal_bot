# google_sheets.py

import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials

GOOGLE_SHEET_CREDENTIALS = os.getenv("GOOGLE_SHEET_CREDENTIALS")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

if not GOOGLE_SHEET_CREDENTIALS:
    raise Exception("ENV GOOGLE_SHEET_CREDENTIALS missing!")

if not GOOGLE_SHEET_ID:
    raise Exception("ENV GOOGLE_SHEET_ID missing!")

# Обработка JSON ключей
creds_dict = json.loads(GOOGLE_SHEET_CREDENTIALS)

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)


# ============================================================
#  UNIVERSAL CONNECTION
# ============================================================

def connect_to_sheet(sheet_name: str):
    sh = client.open_by_key(GOOGLE_SHEET_ID)
    return sh.worksheet(sheet_name)


# ============================================================
#  FIND ROW BY ID
# ============================================================

def find_row_by_id(ws, product_id: str):
    """
    Возвращает индекс строки (1-based) по колонке id.
    Возвращает None, если не найдено.
    """
    ids = ws.col_values(1)  # колонка A - id
    for i, value in enumerate(ids, start=1):
        if value.strip() == str(product_id).strip():
            return i
    return None


# ============================================================
#  LOAD PRODUCTS (parent + child items)
# ============================================================

def load_products_safe():
    """
    Загружает ВСЕ товары (parent + child).
    Ряды должны содержать колонки:

    id | parent_id | category | name | variant_label | price | description | our_price | supplier | stock | photo_url | file_id | active
    """

    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    products = []

    for row in rows:
        active_raw = str(row.get("active", "")).strip().lower()
        active = active_raw in ("true", "1", "yes")

        # stock
        stock_raw = row.get("stock")
        if stock_raw in ("", None, " "):
            stock = None
        else:
            try:
                stock = int(stock_raw)
            except:
                stock = None

        products.append({
            "id": str(row.get("id", "")).strip(),
            "parent_id": str(row.get("parent_id", "")).strip(),
            "category": row.get("category", "").strip(),
            "name": row.get("name", "").strip(),
            "variant_label": row.get("variant_label", "").strip(),
            "price": int(row.get("price") or 0),
            "description": row.get("description", ""),
            "our_price": row.get("our_price") or None,
            "supplier": row.get("supplier", ""),
            "stock": stock,
            "photo_url": row.get("photo_url", "").strip(),
            "file_id": row.get("file_id", "").strip(),
            "active": active
        })

    # Возвращаем только активные child + parent без вариантов
    return [p for p in products if p["active"]]


# ============================================================
#  UPDATE STOCK
# ============================================================

def update_stock(product_id: str, new_stock: int):
    """
    Обновляет stock в таблице.
    Если stock = 0 → active = FALSE.
    Если stock > 0 → active = TRUE.
    """

    ws = connect_to_sheet("Products")
    row_i = find_row_by_id(ws, product_id)

    if not row_i:
        print(f"[GSHEETS] update_stock: id {product_id} not found")
        return False

    stock_col = 10   # J
    active_col = 13  # M

    ws.update_cell(row_i, stock_col, new_stock)

    # auto active
    if new_stock == 0:
        ws.update_cell(row_i, active_col, "FALSE")
    else:
        ws.update_cell(row_i, active_col, "TRUE")

    return True


# ============================================================
#  UPDATE FILE ID
# ============================================================

def update_file_id(product_id: str, file_id: str):
    """
    Записывает file_id в продукт (child или parent).
    """

    ws = connect_to_sheet("Products")
    row_i = find_row_by_id(ws, product_id)

    if not row_i:
        return False

    file_col = 12  # L
    ws.update_cell(row_i, file_col, file_id)
    return True
