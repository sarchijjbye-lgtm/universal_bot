# app/utils/keyboards.py

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ==========================================================
# Кнопки категорий
# ==========================================================
def categories_kb(categories: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for cat in categories:
        kb.button(text=cat, callback_data=f"cat:{cat}")

    kb.adjust(2)
    return kb.as_markup()


# ==========================================================
# Кнопки списка товаров
# ==========================================================
def products_kb(products: list) -> InlineKeyboardMarkup:
    """
    products — список Product объектов.
    """
    kb = InlineKeyboardBuilder()

    for product in products:
        kb.button(
            text=product.name,
            callback_data=f"product:{product.id}"
        )

    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Кнопки вариантов товара
# ==========================================================
def variants_kb(product_id: int, variants: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for variant in variants:
        kb.button(
            text=f"{variant.variant_label} — {variant.price}₽",
            callback_data=f"variant:{variant.id}"
        )

    kb.button(text="⬅ Назад", callback_data=f"back:product:{product_id}")

    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Кнопки корзины
# ==========================================================
def cart_kb(items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # удаление каждого варианта
    for item in items:
        kb.button(
            text=f"❌ {item['name']} ({item['variant']})",
            callback_data=f"del:{item['variant_id']}"
        )

    # кнопки действий
    kb.button(text="🧾 Оформить заказ", callback_data="checkout")
    kb.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    kb.button(text="⬅ Назад", callback_data="back:catalog")

    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Кнопки во время оформления заказа
# ==========================================================
def confirm_order_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="✔ Подтвердить заказ", callback_data="order_confirm")
    kb.button(text="❌ Отменить", callback_data="order_cancel")

    kb.adjust(1)
    return kb.as_markup()
