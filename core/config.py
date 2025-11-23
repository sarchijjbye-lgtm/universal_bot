# app/core/config.py

import json
import os
from dotenv import load_dotenv

from pathlib import Path

load_dotenv()  # Загрузка переменных окружения

BASE_DIR = Path(__file__).resolve().parents[2]


class Config:
    """Главная конфигурация приложения.
    Объединяет:
    - .env
    - settings.json
    - настройки из Google Sheets (загружаются отдельно)
    """

    def __init__(self):
        # ----- .ENV -----
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        self.ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0"))
        self.SPREADSHEET_NAME: str = os.getenv("SPREADSHEET_NAME", "")
        self.GOOGLE_SA_JSON: str = os.getenv("GOOGLE_SA_JSON", "")

        # ----- settings.json -----
        self._load_local_settings()

        # ----- Настройки из Sheets -----
        # Загружаются позже (lazy load)
        self.sheet_settings = {}

    # ==========================================================
    # Загружаем local JSON (brand, currency)
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
    # Обновление настроек из Google Sheets
    # ==========================================================
    def update_sheet_settings(self, data: dict):
        """Принимает dict вида:
        {
            'welcome_message': '...',
            'pickup_address': '...',
            'store_name': '...',
            'brand_name': '...',
            'after_order_message': '...',
            'orders_sheet': 'Orders',
            'admin_chat_id': '12345'
        }
        """
        self.sheet_settings = data

        # Обновляем ключевые значения
        self.WELCOME_MESSAGE = data.get("welcome_message", "")
        self.PICKUP_ADDRESS = data.get("pickup_address", "")
        self.STORE_NAME = data.get("store_name", self.BRAND)
        self.BRAND_NAME = data.get("brand_name", self.BRAND)
        self.AFTER_ORDER_MESSAGE = data.get("after_order_message", "")
        self.ORDERS_SHEET = data.get("orders_sheet", "Orders")

        # Обновить admin_chat_id если он задан в таблице
        admin_from_sheet = data.get("admin_chat_id")
        if admin_from_sheet:
            try:
                self.ADMIN_CHAT_ID = int(admin_from_sheet)
            except ValueError:
                pass

    # ==========================================================
    # Getter
    # ==========================================================
    def get(self, key, default=None):
        return getattr(self, key, default)


# Singleton instance
config = Config()
