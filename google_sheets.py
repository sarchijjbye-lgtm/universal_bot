# google_sheets.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

GOOGLE_SHEET_CREDENTIALS = os.getenv("GOOGLE_SHEET_CREDENTIALS")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

if not GOOGLE_SHEET_CREDENTIALS:
    raise Exception("ENV GOOGLE_SHEET_CREDENTIALS missing!")

if not GOOGLE_SHEET_ID:
    raise Exception("ENV GOOGLE_SHEET_ID missing!")

creds_dict = json.loads(GOOGLE_SHEET_CREDENTIALS)

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)


def connect_to_sheet(sheet_name: str):
    sh = client.open_by_key(GOOGLE_SHEET_ID)
    return sh.worksheet(sheet_name)


def load_products_safe():
    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    products = []

    for row in rows:

        # only active = true
        if str(row.get("active")).strip().lower() not in ("true", "1", "yes"):
            continue

        # stock
        raw_stock = row.get("stock")
        try:
            stock = int(raw_stock) if raw_stock not in (None, "", " ") else None
        except:
            stock = None

        products.append({
            "id": str(row.get("id", "")).strip(),
            "parent_id": str(row.get("parent_id", "")).strip() or None,
            "category": row.get("category", "").strip(),
            "name": row.get("name", "").strip(),
            "variant_label": row.get("variant_label", "").strip(),
            "price": int(row.get("price") or 0),
            "description": row.get("description", ""),
            "our_price": row.get("our_price") or None,
            "supplier": row.get("supplier") or "",
            "stock": stock,
            "photo_url": row.get("photo_url", "").strip(),
            "file_id": row.get("file_id", "").strip()
        })

    return products


def update_stock(product_id: str, new_stock: int):
    """
    Записывает новый stock в Google Sheets.
    Если stock = 0 → active = FALSE.
    """
    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    for idx, r in enumerate(rows, start=2):  # data starts at row 2
        if str(r.get("id")) == str(product_id):

            ws.update_cell(idx, 10, new_stock)  # stock column
            if new_stock <= 0:
                ws.update_cell(idx, 13, "FALSE")  # active column

            return True

    return False


def update_file_id(product_id: str, file_id: str):
    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    for idx, r in enumerate(rows, start=2):
        if str(r.get("id")) == str(product_id):
            ws.update_cell(idx, 12, file_id)
            return True
    return False
