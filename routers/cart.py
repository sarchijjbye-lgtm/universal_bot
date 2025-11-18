# routers/cart.py

from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

CART = {}  # user_id → list


def get_cart(uid: int):
    return CART.get(uid, [])


def calc_total(uid: int):
    return sum(item["price"] * item["qty"] for item in get_cart(uid))


def clear_cart(uid: int):
    CART.pop(uid, None)


cart_router = Router()


@cart_router.callback_query(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(callback: CallbackQuery):

    user_id = callback.from_user.id
    _, parent_id, child_id = callback.data.split(":")

    # load products fresh
    from google_sheets import load_products_safe
    products = load_products_safe()

    child = next((x for x in products if x["id"] == child_id), None)
    if not child:
        return await callback.answer("Вариация не найдена", show_alert=True)

    CART.setdefault(user_id, []).append({
        "child_id": child_id,
        "name": child["name"],
        "variant": child["variant_label"],
        "price": child["price"],
        "qty": 1
    })

    await callback.answer("✔ Добавлено в корзину")
