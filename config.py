import os
from dotenv import load_dotenv

load_dotenv()

# === TELEGRAM ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# === WEBHOOK ===
BOT_URL = os.getenv("BOT_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = BOT_URL + WEBHOOK_PATH

# === GOOGLE SHEETS ===
GOOGLE_SA_JSON = os.getenv("GOOGLE_SA_JSON")

# Таблица с продуктами
PRODUCTS_SHEET_NAME = os.getenv("PRODUCTS_SHEET_NAME", "Products")

# Таблица заказов
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Orders")
