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
    """
    Returns worksheet by name.
    """
    try:
        sh = client.open_by_key(GOOGLE_SHEET_ID)
        return sh.worksheet(sheet_name)
    except Exception as e:
        print(f"[GSHEETS ERROR] Could not open sheet {sheet_name}: {e}")
        raise


# === PRODUCTS LOADER ===
def load_products_safe():
    """
    Returns catalog in normalized structure:
    [
       {
          "id": "1",
          "name": "Тыквенное масло",
          "description": "...",
          "photo_file_id": "...",
          "variants": [
               {"id": "v1", "label": "250ml", "price": 600},
               {"id": "v2", "label": "500ml", "price": 1100}
          ]
       },
       ...
    ]
    """

    ws = connect_to_sheet("Products")
    rows = ws.get_all_records()

    products = []
    for row in rows:
        try:
            variants = json.loads(row["variants"]) if row.get("variants") else []
        except:
            variants = []

        products.append({
            "id": str(row["id"]),
            "name": row.get("name", "Без названия"),
            "description": row.get("description", ""),
            "photo_file_id": row.get("photo_file_id", ""),
            "variants": variants
        })

    return products
