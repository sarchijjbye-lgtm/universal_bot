import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", 0))

BOT_URL = os.getenv("BOT_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BOT_URL}{WEBHOOK_PATH}"
