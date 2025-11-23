# app/services/cart.py

from typing import Dict, Any, List

from aiogram.fsm.context import FSMContext

from app.services.sheets.catalog import CatalogService


class CartService:
    """
    Хранение корзины полностью изолировано в FSMContext.
    Структура корзины в state:

    cart = {
        variant_id (int): {
            "product_id": 1,
            "variant_id": 3,
            "name": "Масло льняное",
            "variant": "500 мл",
            "price": 600,
            "qty": 2
        },
        ...
    }
    """

    STATE_KEY = "cart"

    def __init__(self, catalog: CatalogService):
        self.catalog = catalog

    # ---------------------------------------------------------
    # Получить корзину пользователя
    # ---------------------------------------------------------
    async def _get_cart(self, state: FSMContext) -> Dict[int, Dict[str, Any]]:
        return await state.get_data() or {}

    async def _save_cart(self, state: FSMContext, cart: Dict[int, Dict[str, Any]]):
        await state.update_data(**cart)

    # ---------------------------------------------------------
    # Добавление товара
    # ---------------------------------------------------------
    async def add(self, state: FSMContext, variant_id: int, qty: int = 1):
        data = await state.get_data()
        cart = data.get(self.STATE_KEY, {})

        variant = self.catalog.get_variant(variant_id)
        if not variant:
            return False

        # Если уже в корзине — увеличиваем количество
        if variant_id in cart:
            cart[variant_id]["qty"] += qty
        else:
            cart[variant_id] = {
                "product_id": variant.parent_id,
                "variant_id": variant.id,
                "name": variant.name,
                "variant": variant.variant_label,
                "price": variant.price,
                "qty": qty,
            }

        await state.update_data({self.STATE_KEY: cart})
        return True

    # ---------------------------------------------------------
    # Уменьшить количество товара
    # ---------------------------------------------------------
    async def decrease(self, state: FSMContext, variant_id: int):
        data = await state.get_data()
        cart = data.get(self.STATE_KEY, {})

        if variant_id not in cart:
            return False

        cart[variant_id]["qty"] -= 1

        if cart[variant_id]["qty"] <= 0:
            del cart[variant_id]

        await state.update_data({self.STATE_KEY: cart})
        return True

    # ---------------------------------------------------------
    # Удаление товара из корзины
    # ---------------------------------------------------------
    async def remove(self, state: FSMContext, variant_id: int):
        data = await state.get_data()
        cart = data.get(self.STATE_KEY, {})

        if variant_id in cart:
            del cart[variant_id]
            await state.update_data({self.STATE_KEY: cart})
            return True

        return False

    # ---------------------------------------------------------
    # Очистить корзину
    # ---------------------------------------------------------
    async def clear(self, state: FSMContext):
        await state.update_data({self.STATE_KEY: {}})

    # ---------------------------------------------------------
    # Получить все товары корзины
    # ---------------------------------------------------------
    async def list(self, state: FSMContext) -> List[Dict[str, Any]]:
        data = await state.get_data()
        cart = data.get(self.STATE_KEY, {})
        return list(cart.values())

    # ---------------------------------------------------------
    # Посчитать итоговую сумму
    # ---------------------------------------------------------
    async def total(self, state: FSMContext) -> float:
        items = await self.list(state)
        return sum(item["price"] * item["qty"] for item in items)

    # ---------------------------------------------------------
    # Преобразовать корзину к формату OrdersService
    # ---------------------------------------------------------
    async def to_order_items(self, state: FSMContext) -> List[Dict[str, Any]]:
        """
        Преобразует корзину в формат, который принимает OrdersService:
        [
            {
                "product_id": ...,
                "variant_id": ...,
                "name": ...,
                "variant": ...,
                "price": ...,
                "qty": ...
            }
        ]
        """
        return await self.list(state)
