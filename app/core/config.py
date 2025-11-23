# app/core/config.py

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения

BASE_DIR = Path(__file__).resolve().parents[2]


class Config:
    """
    Глобальная конфигурация приложения.
    Источники:
    - .env
    - data/settings.json (локальные настройки)
    - Google Sheets (динамические настройки)
    """

    def __init__(self):
        # -------------------------------
        # .ENV НАСТРОЙКИ
        # -------------------------------
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        self.ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0"))

        # Google API
        self.SPREADSHEET_NAME: str = os.getenv("SPREADSHEET_NAME", "")
        self.GOOGLE_SA_JSON: str = os.getenv("GOOGLE_SA_JSON", "")

        # URL проекта — важно для вебхука
        self.BOT_URL: str = os.getenv("BOT_URL", "").rstrip("/")

        # -------------------------------
        # LOCAL SETTINGS (settings.json)
        # -------------------------------
        self._load_local_settings()

        # -------------------------------
        # Google Sheets settings
        # -------------------------------
        self.sheet_settings = {}

    # ==========================================================
    # Загружаем параметры из settings.json
    # ==========================================================
    def _load_local_settings(self):
        settings_path = BASE_DIR / "data" / "settings.json"

        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        self.BRAND = data.get("brand", "Shop")
        self.CURRENCY = data.get("currency", "₽")

    # ==========================================================
    # Google Sheets dynamic settings
    # ==========================================================
    def update_sheet_settings(self, data: dict):
        """
        Применяет настройки из таблицы.
        """
        self.sheet_settings = data

        self.WELCOME_MESSAGE = data.get("welcome_message", "")
        self.PICKUP_ADDRESS = data.get("pickup_address", "")
        self.STORE_NAME = data.get("store_name", self.BRAND)
        self.BRAND_NAME = data.get("brand_name", self.BRAND)
        self.AFTER_ORDER_MESSAGE = data.get("after_order_message", "")
        self.ORDERS_SHEET = data.get("orders_sheet", "Orders")

        admin_from_sheet = data.get("admin_chat_id")
        if admin_from_sheet:
            try:
                self.ADMIN_CHAT_ID = int(admin_from_sheet)
            except ValueError:
                pass

    # ==========================================================
    # Универсальный getter
    # ==========================================================
    def get(self, key, default=None):
        return getattr(self, key, default)


# Singleton
config = Config()
