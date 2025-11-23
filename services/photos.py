# app/services/photos.py

from typing import Optional

from app.services.sheets.client import GoogleSheetsClient
from app.services.sheets.catalog import CatalogService
from app.core.config import config


class PhotoManager:
    """
    Управляет file_id товаров.
    Используется в admin flow:
      1) Админ отправляет фото
      2) Админ отправляет product_id
      3) Менеджер сохраняет file_id в Google Sheets
    """

    SHEET_NAME = "Products"

    def __init__(self, client: GoogleSheetsClient, catalog: CatalogService):
        self.client = client
        self.catalog = catalog

    # ---------------------------------------------------------
    # Записать file_id в таблицу по product_id
    # ---------------------------------------------------------
    def save_file_id(self, product_id: int, file_id: str) -> bool:
        """
        Обновляет file_id товара по ID.
        Работает для parent товара.
        """
        try:
            row = self.client.find_row(self.SHEET_NAME, "id", product_id)
        except ValueError:
            return False

        # Найти индекс колонки file_id
        worksheet = self.client.worksheet(self.SHEET_NAME)
        headers = worksheet.row_values(1)

        try:
            col_index = headers.index("file_id") + 1  # +1 → потому что индексация с 1
        except ValueError:
            return False

        # Обновляем Google Sheets
        self.client.update_cell(self.SHEET_NAME, row, col_index, file_id)

        # Перезагружаем каталог (для актуального фото)
        self.catalog.load()

        return True

    # ---------------------------------------------------------
    # Получить file_id товара (или None)
    # ---------------------------------------------------------
    def get_file_id(self, product_id: int) -> Optional[str]:
        product = self.catalog.get_product(product_id)
        if not product:
            return None
        return product.file_id
