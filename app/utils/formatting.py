from typing import List, Dict
from app.core.config import config


# ==========================================================
# Форматирование карточки товара
# ==========================================================
def product_card(name: str, description: str) -> str:
    return f"<b>{name}</b>\n{description}\n"


# ==========================================================
# Форматирование вариантов
# ==========================================================
def format_price(price: float) -> str:
    """Приводим к целому числу без .0"""
    price = float(price)
    if price.is_integer():
        return str(int(price))
    return str(price)


def variants_text(variants) -> str:
    """variants — список ProductVariant"""
    lines = []
    for v in variants:
        price = format_price(v.price)
        lines.append(f"• <b>{v.variant_label}</b> — {price}{config.CURRENCY}")

    return "\n".join(lines)


# ==========================================================
# Текст корзины
# ==========================================================
def cart_text(items: List[Dict]) -> str:
    if not items:
        return "<i>Корзина пуста.</i>"

    lines = ["🧺 <b>Ваша корзина:</b>\n"]

    for item in items:
        price = format_price(item["price"])
        lines.append(
            f"• {item['name']} ({item['variant']}) — {price}{config.CURRENCY} × {item['qty']}"
        )

    return "\n".join(lines)


# ==========================================================
# Итог
# ==========================================================
def total_text(total: float) -> str:
    return f"\n\n<b>Итого:</b> {format_price(total)}{config.CURRENCY}"


# ==========================================================
# Сообщение админа
# ==========================================================
def admin_order_message(order_id: str, user_id: int, name: str, phone: str, address: str, items: List[Dict], total: float) -> str:
    lines = [
        "🆕 <b>Новый заказ!</b>",
        f"<b>ID заказа:</b> {order_id}",
        f"<b>Пользователь:</b> {user_id}",
        f"<b>Имя:</b> {name}",
        f"<b>Телефон:</b> {phone}",
        f"<b>Адрес:</b> {address}",
        "\n<b>Товары:</b>",
    ]

    for i in items:
        price = format_price(i['price'])
        lines.append(f"• {i['name']} ({i['variant']}) × {i['qty']} = {price}{config.CURRENCY}")

    lines.append(f"\n<b>Итого:</b> {format_price(total)}{config.CURRENCY}")
    return "\n".join(lines)
