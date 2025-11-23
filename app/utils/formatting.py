# app/utils/formatting.py

from typing import List, Dict, Optional
from app.core.config import config


# ==========================================================
# Универсальное форматирование цены
# ==========================================================
def format_price(price: float) -> str:
    """Форматирование цены без копеек + валюта."""
    try:
        price_int = int(round(float(price)))
    except (TypeError, ValueError):
        price_int = price
    return f"{price_int}{config.CURRENCY}"


# ==========================================================
# Форматирование карточки товара
# ==========================================================
def product_card(name: str, description: str) -> str:
    """Формирует заголовок и описание товара."""
    description = description or ""
    return f"<b>{name}</b>\n{description}\n"


# ==========================================================
# Список вариантов товара
# ==========================================================
def variants_text(variants) -> str:
    """Список вариантов внутри карточки товара."""
    lines = [
        f"• <b>{v.variant_label}</b> — {format_price(v.price)}"
        for v in variants
    ]
    return "\n".join(lines)


# ==========================================================
# Корзина пользователя
# ==========================================================
def cart_text(items: List[Dict]) -> str:
    """
    items — список словарей:
    {
        "product_id": int,
        "variant_id": int,
        "name": str,
        "variant": str,
        "price": float,
        "qty": int
    }
    """
    if not items:
        return "<i>Корзина пуста.</i>"

    lines = ["🧺 <b>Ваша корзина:</b>\n"]

    for item in items:
        lines.append(
            f"• {item['name']} ({item['variant']}) — "
            f"{format_price(item['price'])} × {item['qty']}"
        )

    return "\n".join(lines)


# ==========================================================
# Итоговая сумма
# ==========================================================
def total_text(total: float) -> str:
    return f"\n\n<b>Итого:</b> {format_price(total)}"


# ==========================================================
# Предпросмотр перед оформлением
# ==========================================================
def checkout_preview(items: List[Dict], total: float, method: str) -> str:
    """
    method: 'pickup' | 'delivery'
    """
    base = cart_text(items) + total_text(total)

    if method == "pickup":
        return (
            base
            + f"\n\n<b>Способ получения:</b> Самовывоз\n"
            f"<i>Адрес:</i> {config.PICKUP_ADDRESS}"
            + "\n\nПодтвердите заказ."
        )

    return (
        base
        + "\n\n<b>Способ получения:</b> Доставка\n"
        + "Подтвердите заказ."
    )


# ==========================================================
# Форматирование сообщения администратору
# ==========================================================
def admin_order_message(
    order_id: str,
    user_id: int,
    name: str,
    phone: str,
    method: str,
    address: Optional[str],
    items: List[Dict],
    total: float,
) -> str:
    """
    Формирует сообщение администратору о новом заказе.
    """

    lines = [
        "🆕 <b>Новый заказ</b>",
        f"<b>ID:</b> {order_id}",
        f"<b>User ID:</b> {user_id}",
        f"<b>Имя:</b> {name}",
        f"<b>Телефон:</b> {phone}",
        "",
        "<b>Товары:</b>",
    ]

    for i in items:
        lines.append(
            f"• {i['name']} ({i['variant']}) × {i['qty']} = {format_price(i['price'])}"
        )

    lines.append(f"\n<b>Итого:</b> {format_price(total)}")

    # способ получения
    if method == "pickup":
        lines.append("\n<b>Получение:</b> Самовывоз")
        lines.append(f"<b>Адрес:</b> {config.PICKUP_ADDRESS}")
    else:
        lines.append("\n<b>Получение:</b> Доставка")
        lines.append(f"<b>Адрес:</b> {address}")

    return "\n".join(lines)
