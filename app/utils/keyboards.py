from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


# ==========================================================
# Категории
# ==========================================================
def categories_kb(categories: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat, callback_data=f"cat:{cat}")
    kb.adjust(2)
    return kb.as_markup()


# ==========================================================
# Список товаров
# ==========================================================
def products_kb(products: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(
            text=product.name,
            callback_data=f"product:{product.id}"
        )
    kb.button(text="⬅ Назад", callback_data="back:catalog")
    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Карточка товара — варианты
# ==========================================================
def product_kb(product_id: int, variants: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for v in variants:
        kb.button(
            text=f"{v.variant_label} — {int(v.price)}₽",
            callback_data=f"add_to_cart:{product_id}:{v.variant_label}"
        )

    kb.button(text="🛒 Корзина", callback_data="open_cart")
    kb.button(text="⬅ Назад", callback_data="back:catalog")
    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Корзина
# ==========================================================
def cart_kb(items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for item in items:
        kb.button(
            text=f"❌ {item['name']} ({item['variant']})",
            callback_data=f"del:{item['variant_id']}"
        )

    kb.button(text="🧾 Оформить заказ", callback_data="checkout")
    kb.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    kb.button(text="⬅ Назад", callback_data="back:catalog")

    kb.adjust(1)
    return kb.as_markup()
