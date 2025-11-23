# app/services/sheets/orders.py

from datetime import datetime
from typing import List, Dict, Any

from app.services.sheets.client import GoogleSheetsClient
from app.core.config import config


class OrdersService:
    """
    Сервис для записи заказов в Google Sheets.
    Таблица обычно имеет вид:

    timestamp | order_id | user_id | name | phone | address | items_json | total | status
    """

    def __init__(self, client: GoogleSheetsClient):
        self.client = client
        self.sheet_name = config.ORDERS_SHEET or "Orders"

    # ---------------------------------------------------------
    # Генерация ID заказа
    # ---------------------------------------------------------
    def generate_order_id(self) -> str:
        now = datetime.utcnow()
        return now.strftime("ORD-%Y%m%d-%H%M%S")

    # ---------------------------------------------------------
    # Формирование строки заказа
    # ---------------------------------------------------------
    def _build_row(
        self,
        order_id: str,
        user_id: int,
        name: str,
        phone: str,
        address: str,
        items: List[Dict[str, Any]],
        total: float,
    ) -> List[Any]:
        """
        items — список вида:
        [
            {
                "product_id": 1,
                "variant_id": 3,
                "name": "Масло льняное",
                "variant": "500 мл",
                "price": 600,
                "qty": 1
            }
        ]
        """

        # Превращаем товары в компактную JSON-строку
        items_repr = "; ".join(
            f"{item['name']} ({item['variant']}) x{item['qty']} = {item['price']}₽"
            for item in items
        )

        row = [
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            order_id,
            str(user_id),
            name,
            phone,
            address,
            items_repr,
            total,
            "NEW",  # статус заказа по умолчанию
        ]

        return row

    # ---------------------------------------------------------
    # Публичный метод: записать заказ
    # ---------------------------------------------------------
    def create_order(
        self,
        user_id: int,
        name: str,
        phone: str,
        address: str,
        items: List[Dict[str, Any]],
        total: float,
    ) -> str:
        """
        Создаёт заказ в таблице и возвращает order_id.
        """

        order_id = self.generate_order_id()
        row = self._build_row(order_id, user_id, name, phone, address, items, total)

        self.client.append_row(self.sheet_name, row)
        return order_id
