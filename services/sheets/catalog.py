# app/services/sheets/catalog.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from app.services.sheets.client import GoogleSheetsClient
from app.core.config import config


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

    SHEET_NAME = "Products"

    def __init__(self, client: GoogleSheetsClient):
        self.client = client
        self._cache: Dict[int, Product] = {}   # product_id -> Product
        self._categories = []                  # список категорий

    # ------------------------------------------------------
    # Публичный метод: загрузить весь каталог
    # ------------------------------------------------------
    def load(self):
        raw = self.client.read(self.SHEET_NAME)
        parents = {}
        children = []

        # 1. Разделяем parent и child товары
        for row in raw:
            pid = row.get("id")
            parent_id = row.get("parent_id")
            active = bool(row.get("active", True))

            if not active:
                continue

            if not parent_id:  # parent product
                parents[pid] = {
                    "id": pid,
                    "name": row["name"],
                    "category": row["category"],
                    "description": row.get("description", ""),
                    "file_id": row.get("file_id"),
                    "variants": [],
                    "active": active,
                }
            else:  # variant (child)
                children.append(row)

        # 2. Сопоставляем детей с родителями
        for row in children:
            vid = row["id"]
            parent_id = row["parent_id"]

            # если у варианта нет file_id → наследуем от родителя
            file_id = row.get("file_id") or parents.get(parent_id, {}).get("file_id")

            variant = ProductVariant(
                id=vid,
                parent_id=parent_id,
                name=row["name"],
                variant_label=row.get("variant_label", ""),
                price=float(row.get("price", 0)),
                file_id=file_id,
                active=True
            )

            if parent_id in parents:
                parents[parent_id]["variants"].append(variant)

        # 3. Превращаем в dataclass Product
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
                active=data["active"]
            )

            self._cache[p_id] = product
            categories.add(data["category"])

        self._categories = sorted(categories)

    # ------------------------------------------------------
    # Публичный API для handlers
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

