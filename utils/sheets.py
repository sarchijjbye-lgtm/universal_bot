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

    sa = json.loads(GOOGLE_SA_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(sa, scope)
    return gspread.authorize(creds)


def load_products():
    client = connect()
    sheet = client.open(PRODUCTS_SHEET_NAME).sheet1
    rows = sheet.get_all_records()

    products = []

    for r in rows:
        raw_stock = r.get("stock")
        try:
            stock = int(raw_stock) if raw_stock not in ("", None) else None
        except:
            stock = None

        products.append({
            "id": str(r.get("id", "")),
            "parent_id": str(r.get("parent_id", "")).strip() or None,
            "category": r.get("category", ""),
            "name": r.get("name", ""),
            "variant_label": r.get("variant_label", ""),
            "price": int(r.get("price") or 0),
            "description": r.get("description") or "",
            "our_price": r.get("our_price") or None,
            "supplier": r.get("supplier") or "",
            "stock": stock,
            "photo_url": r.get("photo_url") or "",
            "file_id": r.get("file_id") or "",
            "active": str(r.get("active")).lower() in ("true", "1", "yes")
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
