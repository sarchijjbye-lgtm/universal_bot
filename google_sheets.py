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

# credentials
creds_dict = json.loads(GOOGLE_SHEET_CREDENTIALS)

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)


# ============================================================
#  SHEET CONNECTION
# ============================================================

def connect_to_sheet(sheet_name: str):
    sh = client.open_by_key(GOOGLE_SHEET_ID)
    return sh.worksheet(sheet_name)


# ============================================================
#  FIND ROW BY ID
# ============================================================

def find_row_by_id(ws, product_id: str):
    ids = ws.col_values(1)  # column A
    for i, v in enumerate(ids, start=1):
        if v.strip() == str(product_id).strip():
            return i
    return None


# ============================================================
#  LOAD PRODUCTS
# ============================================================

def load_products_safe():
    """
    Loads ALL rows. Parent = rows with parent_id == "".
    Children = parent_id != "" and price > 0.
    """

    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    products = []

    for r in rows:
        # active
        active_raw = str(r.get("active", "")).strip().lower()
        active = active_raw in ("true", "1", "yes")

        # stock
        stock_raw = r.get("stock")
        if stock_raw in ("", None, " "):
            stock = None
        else:
            try:
                stock = int(stock_raw)
            except:
                stock = None

        products.append({
            "id": str(r.get("id", "")).strip(),
            "parent_id": str(r.get("parent_id", "")).strip(),  # <- STRING
            "category": r.get("category", "").strip(),
            "name": r.get("name", "").strip(),
            "variant_label": r.get("variant_label", "").strip(),
            "price": int(r.get("price") or 0),
            "description": r.get("description", ""),
            "our_price": r.get("our_price") or None,
            "supplier": r.get("supplier", "").strip(),
            "stock": stock,
            "photo_url": r.get("photo_url", "").strip(),
            "file_id": r.get("file_id", "").strip(),
            "active": active
        })

    # return active only
    return [p for p in products if p["active"]]


# ============================================================
#  UPDATE STOCK
# ============================================================

def update_stock(product_id: str, new_stock: int):
    ws = connect_to_sheet("Products")
    row_i = find_row_by_id(ws, product_id)
    if not row_i:
        return False

    col_stock = 10   # J
    col_active = 13  # M

    ws.update_cell(row_i, col_stock, new_stock)

    ws.update_cell(row_i, col_active, "TRUE" if new_stock > 0 else "FALSE")
    return True


# ============================================================
#  UPDATE FILE ID
# ============================================================

def update_file_id(product_id: str, file_id: str):
    ws = connect_to_sheet("Products")
    row_i = find_row_by_id(ws, product_id)
    if not row_i:
        return False

    col_file = 12  # L
    ws.update_cell(row_i, col_file, file_id)
    return True
