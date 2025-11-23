# app/services/sheets/settings.py

from typing import Dict, Any

from app.services.sheets.client import GoogleSheetsClient
from app.core.config import config


class SettingsService:

    SHEET_NAME = "Settings"

    def __init__(self, client: GoogleSheetsClient):
        self.client = client

    # ---------------------------------------------------------
    # Основной метод: загрузить все настройки
    # ---------------------------------------------------------
    def load(self) -> Dict[str, Any]:
        """
        Загружает таблицу Settings формата:

        key | value
        -------------------------
        welcome_message | Добро пожаловать!
        pickup_address  | ул. Льва Толстого 19
        store_name      | HION shop
        ...

        Возвращает dict и обновляет глобальный config.
        """

        raw = self.client.read(self.SHEET_NAME)

        settings = {}
        for row in raw:
            key = str(row.get("key")).strip()
            value = row.get("value")

            if key:
                settings[key] = value

        # обновляем глобальный config
        config.update_sheet_settings(settings)
        return settings

    # ---------------------------------------------------------
    # Получение одного параметра
    # ---------------------------------------------------------
    def get(self, key: str, default=None):
        return config.sheet_settings.get(key, default)
