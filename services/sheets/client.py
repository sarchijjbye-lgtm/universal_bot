# app/services/sheets/client.py

import json
from typing import Any, Dict, List

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from app.core.config import config


class GoogleSheetsClient:
    """Единая точка доступа к Google Sheets.
    Загружает:
    - settings
    - catalog
    - orders sheet
    """

    def __init__(self):
        self.gc = self._authorize()
        self.spreadsheet = self.gc.open(config.SPREADSHEET_NAME)

    # ---------------------------------------------------------
    # Авторизация сервисного аккаунта
    # ---------------------------------------------------------
    def _authorize(self):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        service_account_info = json.loads(config.GOOGLE_SA_JSON)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            service_account_info,
            scopes=scopes
        )

        return gspread.authorize(credentials)

    # ---------------------------------------------------------
    # Получение таблицы
    # ---------------------------------------------------------
    def worksheet(self, name: str):
        """Возвращает рабочий лист по имени."""
        return self.spreadsheet.worksheet(name)

    # ---------------------------------------------------------
    # Чтение данных
    # ---------------------------------------------------------
    def read(self, sheet_name: str) -> List[Dict[str, Any]]:
        """Возвращает таблицу в формате массивов dict."""
        ws = self.worksheet(sheet_name)
        return ws.get_all_records()

    # ---------------------------------------------------------
    # Запись строки (append)
    # ---------------------------------------------------------
    def append_row(self, sheet_name: str, row: List[Any]):
        """Добавляет новую строку в указанную таблицу."""
        ws = self.worksheet(sheet_name)
        ws.append_row(row, value_input_option="USER_ENTERED")

    # ---------------------------------------------------------
    # Обновление отдельной ячейки
    # ---------------------------------------------------------
    def update_cell(self, sheet_name: str, row: int, column: int, value: Any):
        """Обновляет указанную ячейку."""
        ws = self.worksheet(sheet_name)
        ws.update_cell(row, column, value)

    # ---------------------------------------------------------
    # Поиск строки по условию
    # ---------------------------------------------------------
    def find_row(self, sheet_name: str, column: str, value: Any) -> int:
        """
        Возвращает номер строки, где column=value.
        Используется для обновления file_id, stock, цены и т.д.
        """
        ws = self.worksheet(sheet_name)
        data = ws.get_all_records()

        for i, row in enumerate(data, start=2):  # строка 1 — заголовки
            if str(row.get(column)) == str(value):
                return i

        raise ValueError(f"Row with {column}={value} not found")

