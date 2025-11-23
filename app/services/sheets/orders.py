# app/services/sheets/orders.py

from __future__ import annotations
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.services.sheets.client import GoogleSheetsClient
from app.core.config import config


class OrdersService:
    """
    Работа с листом заказов.

    Структура листа Orders в Google Sheets:

    A: order_id
    B: created_at
    C: user_id
    D: name
    E: phone
    F: method (pickup/delivery)
    G: address (location / pickup address)
    H: items_json
    I: total
    """

    SHEET_NAME = None  # берется из settings sheet

    def __init__(self, client: GoogleSheetsClient):
        self.client = client
        self.SHEET_NAME = config.ORDERS_SHEET or "Orders"

    # ------------------------------------------------------
    # Генерация ID заказа (UUID короткий)
    # ------------------------------------------------------
    def _generate_order_id(self) -> str:
        return uuid.uuid4().hex[:10].upper()

    # ------------------------------------------------------
    # Добавление заказа
    # ------------------------------------------------------
    def create_order(
        self,
        user_id: int,
        name: str,
        phone: str,
        method: str,
        address: Optional[str],
        items: List[Dict],
        total: float,
    ) -> str:
        """
        Создает запись в Google Sheets.
        Возвращает order_id.
        """

        order_id = self._generate_order_id()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # items в JSON-строку
        items_json = self.client.dumps(items)

        row = [
            order_id,
            created_at,
            str(user_id),
            name,
            phone,
            method,
            address if address else "",
            items_json,
            str(int(total)),
        ]

        self.client.append_row(self.SHEET_NAME, row)
        return order_id

    # ------------------------------------------------------
    # Чтение всех заказов (при необходимости)
    # ------------------------------------------------------
    def list_orders(self) -> List[Dict]:
        raw = self.client.read(self.SHEET_NAME)
        return raw

    # ------------------------------------------------------
    # Получение одного заказа по ID
    # ------------------------------------------------------
    def get_order(self, order_id: str) -> Optional[Dict]:
        all_orders = self.client.read(self.SHEET_NAME)
        for row in all_orders:
            if str(row.get("order_id")) == str(order_id):
                return row
        return None
