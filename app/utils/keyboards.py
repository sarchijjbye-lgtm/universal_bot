# app/utils/keyboards.py

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


# ==========================================================
# Глобальное меню — отображается на всех экранах
# ==========================================================
def global_menu_kb(categories: list[str]) -> InlineKeyboardMarkup:
    """
    Основное меню: категории + корзина.
    Используется в /start и в каталоге.
    """
    kb = InlineKeyboardBuilder()

    for cat in categories:
        kb.button(text=cat, callback_data=f"cat:{cat}")

    kb.button(text="🧺 Корзина", callback_data="cart")

    kb.adjust(2)
    return kb.as_markup()


# ==========================================================
# Список товаров категории
# ==========================================================
def products_kb(products: list) -> InlineKeyboardMarkup:
    """
    products — список Product
    """
    kb = InlineKeyboardBuilder()

    for p in products:
        kb.button(text=p.name, callback_data=f"product:{p.id}")

    kb.button(text="⬅ Назад в категории", callback_data="back:catalog")
    kb.button(text="🧺 Корзина", callback_data="cart")

    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Варианты товара
# ==========================================================
def variants_kb(product_id: int, variants: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for v in variants:
        kb.button(
            text=f"{v.variant_label} — {int(v.price)}₽",
            callback_data=f"variant:{v.id}"
        )

    kb.button(text="🧺 Корзина", callback_data="cart")
    kb.button(text="⬅ Назад", callback_data=f"back:product:{product_id}")

    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Корзина
# ==========================================================
def cart_kb(items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # Кнопки удаления товаров
    for i in items:
        kb.button(
            text=f"❌ {i['name']} ({i['variant']})",
            callback_data=f"del:{i['variant_id']}"
        )

    # Основные кнопки
    kb.button(text="🧾 Оформить заказ", callback_data="checkout")
    kb.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    kb.button(text="⬅ Назад в категории", callback_data="back:catalog")

    kb.adjust(1)
    return kb.as_markup()


# ==========================================================
# Клавиатура подтверждения заказа
# ==========================================================
def confirm_order_kb():
    kb = InlineKeyboardBuilder()

    kb.button(text="✔ Подтвердить заказ", callback_data="order_confirm")
    kb.button(text="❌ Отменить", callback_data="order_cancel")

    kb.adjust(1)
    return kb.as_markup()
