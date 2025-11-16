# routers/cart.py

from aiogram import Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# Простое in-memory хранилище корзин
# CART[user_id] = [ {name, variant, price, qty}, ... ]
CART: dict[int, list[dict]] = {}

def get_cart(uid: int):
    return CART.get(uid, [])

def calc_total(uid: int) -> int:
    return sum(item["price"] * item["qty"] for item in get_cart(uid))

def clear_cart(uid: int):
    """Очищает корзину пользователя (используем после успешного заказа)."""
    CART.pop(uid, None)


cart_router = Router()


@cart_router.callback_query(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(callback: CallbackQuery):
    """
    callback_data формата: addcart:<product_id>:<variant_id>
    """
    user_id = callback.from_user.id
    _, pid, vid = callback.data.split(":")

    # Берём товар из кеша каталога
    from routers.catalog import PRODUCTS_CACHE

    products = PRODUCTS_CACHE or []
    product = next((p for p in products if str(p["id"]) == pid), None)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    variant = next((v for v in product["variants"] if str(v["id"]) == vid), None)
    if not variant:
        await callback.answer("Вариант не найден", show_alert=True)
        return

    CART.setdefault(user_id, []).append({
        "name": product["name"],
        "variant": variant["label"],
        "price": int(variant["price"]),
        "qty": 1
    })

    await callback.answer("✔ Товар добавлен в корзину", show_alert=False)


@cart_router.message(lambda m: m.text in ["🛒 Корзина", "Корзина"])
async def show_cart(msg: Message):

    items = get_cart(msg.from_user.id)
    if not items:
        await msg.answer("🛒 Корзина пуста")
        return

    lines = ["<b>Ваш заказ:</b>", ""]
    for item in items:
        lines.append(
            f"— {item['name']} ({item['variant']}) — {item['price']}₽ x {item['qty']}"
        )

    total = calc_total(msg.from_user.id)
    lines.append("")
    lines.append(f"<b>Итого: {total}₽</b>")

    text = "\n".join(lines)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout:start")]
        ]
    )

    await msg.answer(text, reply_markup=kb)
