# app/utils/formatting.py

from typing import List, Dict
from app.core.config import config


# ==========================================================
# Форматирование карточки товара
# ==========================================================
def product_card(name: str, description: str) -> str:
    return (
        f"<b>{name}</b>\n"
        f"{description}\n"
    )


# ==========================================================
# Форматирование списка вариантов для карточки
# ==========================================================
def variants_text(variants) -> str:
    """
    variants — список ProductVariant
    """
    lines = []
    for v in variants:
        lines.append(f"• <b>{v.variant_label}</b> — {v.price}{config.CURRENCY}")

    return "\n".join(lines)


# ==========================================================
# Форматирование корзины
# ==========================================================
def cart_text(items: List[Dict]) -> str:
    """
    items — list of:
    {
        "product_id": ...,
        "variant_id": ...,
        "name": ...,
        "variant": ...,
        "price": ...,
        "qty": ...
    }
    """
    if not items:
        return "<i>Корзина пуста.</i>"

    lines = ["🧺 <b>Ваша корзина:</b>\n"]

    for item in items:
        name = item["name"]
        variant = item["variant"]
        qty = item["qty"]
        price = item["price"]

        lines.append(
            f"• {name} ({variant}) — {price}{config.CURRENCY} × {qty}"
        )

    return "\n".join(lines)


# ==========================================================
# Итоговая сумма
# ==========================================================
def total_text(total: float) -> str:
    return f"\n\n<b>Итого:</b> {total}{config.CURRENCY}"


# ==========================================================
# Полное сообщение перед оформлением
# ==========================================================
def checkout_preview(items: List[Dict], total: float) -> str:
    return (
        cart_text(items)
        + total_text(total)
        + "\n\nВведите, пожалуйста, ваше <b>имя</b>."
    )


# ==========================================================
# Сообщение для администратора о новом заказе
# ==========================================================
def admin_order_message(order_id: str, user_id: int, name: str, phone: str, address: str, items: List[Dict], total: float) -> str:
    lines = [
        f"🆕 <b>Новый заказ!</b>",
        f"<b>ID заказа:</b> {order_id}",
        f"<b>Пользователь:</b> {user_id}",
        f"<b>Имя:</b> {name}",
        f"<b>Телефон:</b> {phone}",
        f"<b>Адрес:</b> {address}",
        "\n<b>Товары:</b>"
    ]

    for i in items:
        lines.append(f"• {i['name']} ({i['variant']}) × {i['qty']} = {i['price']}{config.CURRENCY}")

    lines.append(f"\n<b>Итого:</b> {total}{config.CURRENCY}")

    return "\n".join(lines)
