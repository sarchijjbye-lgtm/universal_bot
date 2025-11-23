# app/services/sheets/catalog.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict

from app.services.sheets.client import GoogleSheetsClient


# ==========================================================
# Data Models
# ==========================================================

@dataclass
class ProductVariant:
    id: int
    parent_id: int
    name: str
    variant_label: str
    price: float
    file_id: Optional[str]
    active: bool


@dataclass
class Product:
    id: int
    name: str
    description: str
    category: str
    file_id: Optional[str]
    variants: List[ProductVariant]
    active: bool


# ==========================================================
# Catalog Service
# ==========================================================

class CatalogService:
    """
    Читает каталог из Google Sheets → Products.

    Требуемая структура таблицы:

    id | parent_id | name | category | description | variant_label | price | file_id | active
    """

    SHEET_NAME = "Products"

    def __init__(self, client: GoogleSheetsClient):
        self.client = client
        self._cache: Dict[int, Product] = {}
        self._categories: List[str] = []

    # ------------------------------------------------------
    # Загрузка каталога
    # ------------------------------------------------------
    def load(self):
        rows = self.client.read(self.SHEET_NAME)

        parents: Dict[int, Dict] = {}
        children = []

        # разделяем parent и variants
        for row in rows:
            pid = int(row["id"])
            parent_id = row.get("parent_id")

            active = row.get("active")
            active = bool(int(active)) if str(active).isdigit() else True
            if not active:
                continue

            if not parent_id:  # parent
                parents[pid] = {
                    "id": pid,
                    "name": row["name"],
                    "category": row["category"],
                    "description": row.get("description", ""),
                    "file_id": row.get("file_id"),
                    "variants": [],
                    "active": True,
                }
            else:
                children.append(row)

        # привязываем варианты
        for row in children:
            vid = int(row["id"])
            parent_id = int(row["parent_id"])

            inherited_file = row.get("file_id") or parents.get(parent_id, {}).get("file_id")

            variant = ProductVariant(
                id=vid,
                parent_id=parent_id,
                name=row["name"],
                variant_label=row.get("variant_label", ""),
                price=float(row.get("price", 0)),
                file_id=inherited_file,
                active=True
            )

            if parent_id in parents:
                parents[parent_id]["variants"].append(variant)

        # формируем dataclasses
        self._cache = {}
        categories = set()

        for p_id, data in parents.items():
            product = Product(
                id=p_id,
                name=data["name"],
                description=data["description"],
                category=data["category"],
                file_id=data["file_id"],
                variants=data["variants"],
                active=data["active"],
            )

            self._cache[p_id] = product
            categories.add(product.category)

        self._categories = sorted(categories)

    # ------------------------------------------------------
    # Public API
    # ------------------------------------------------------
    def get_categories(self) -> List[str]:
        return self._categories

    def get_products_by_category(self, category: str) -> List[Product]:
        return [p for p in self._cache.values() if p.category == category]

    def get_product(self, product_id: int) -> Optional[Product]:
        return self._cache.get(product_id)

    def get_variant(self, variant_id: int) -> Optional[ProductVariant]:
        for product in self._cache.values():
            for variant in product.variants:
                if variant.id == variant_id:
                    return variant
        return None

    def all_products(self) -> List[Product]:
        return list(self._cache.values())
