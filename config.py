import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")  # таблица заказов
GOOGLE_SA_JSON = os.getenv("GOOGLE_SA_JSON")       # ключ сервис-аккаунта
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
