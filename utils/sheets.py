# utils/sheets.py

import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SA_JSON, PRODUCTS_SHEET_NAME, SPREADSHEET_NAME


def connect():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]

    service_account_info = json.loads(GOOGLE_SA_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    return gspread.authorize(creds)


def load_products():
    client = connect()
    sheet = client.open(PRODUCTS_SHEET_NAME).sheet1
    rows = sheet.get_all_records()

    products = []

    for r in rows:

        # variants
        try:
            variants = json.loads(r.get("variants", "")) if r.get("variants") else []
        except:
            variants = []

        # stock
        stock_raw = r.get("stock")
        if stock_raw in ("", None):
            stock = None
        else:
            try:
                stock = int(stock_raw)
            except:
                stock = None

        products.append({
            "id": str(r.get("id", "")),
            "category": r.get("category", ""),
            "name": r.get("name", ""),
            "description": r.get("description") or "",
            "base_price": int(r.get("base_price") or 0),
            "our_price": r.get("our_price") or None,
            "supplier": r.get("supplier") or "",
            "variants": variants,
            "photo_url": r.get("photo_url") or "",
            "file_id": r.get("file_id") or "",
            "stock": stock,
            "active": str(r.get("active", "")).lower() in ("true", "1", "yes")
        })

    return [p for p in products if p["active"]]


def add_order(order):
    client = connect()
    sheet = client.open(SPREADSHEET_NAME).sheet1
    sheet.append_row([
        order["tg_id"],
        order["name"],
        order["phone"],
        order["address"],
        order["items"],
        order["total"]
    ])
