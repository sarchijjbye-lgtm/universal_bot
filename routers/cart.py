# cart.py — PRO EDITION

from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from caching import cache_get, cache_set
from google_sheets import load_products_safe

cart_router = Router()


async def get_cart(user_id):
    cart = await cache_get(f"cart:{user_id}")
    if cart:
        import json
        return json.loads(cart)
    return []


async def save_cart(user_id, cart):
    import json
    await cache_set(f"cart:{user_id}", json.dumps(cart), ttl=3600)


async def get_products():
    data = await cache_get("products")
    if data:
        import json
        return json.loads(data)
    return load_products_safe()


def calc_total(cart):
    return sum(item["price"] * item["qty"] for item in cart)


# ====== ADD ITEM ======

@cart_router.callback_query(lambda c: c.data.startswith("add_"))
async def add_item(cb: types.CallbackQuery):
    _, pid, vid = cb.data.split("_")
    products = await get_products()

    product = next((p for p in products if p["id"] == pid), None)
    if not product:
        await cb.answer("Ошибка товара", show_alert=True)
        return

    variant = next((v for v in product["variants"] if v["id"] == vid), None)
    if not variant:
        await cb.answer("Ошибка варианта", show_alert=True)
        return

    cart = await get_cart(cb.from_user.id)

    # check existing
    key = f"{pid}:{vid}"
    found = next((x for x in cart if x["key"] == key), None)
    if found:
        found["qty"] += 1
    else:
        cart.append({
            "key": key,
            "product": product["name"],
            "variant": variant["name"],
            "price": variant["price"],
            "qty": 1
        })

    await save_cart(cb.from_user.id, cart)
    await cb.answer("Добавлено в корзину!")


# ====== SHOW CART ======

@cart_router.message(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    cart = await get_cart(message.from_user.id)

    if not cart:
        await message.answer("Корзина пуста.")
        return

    text = "<b>🛒 Ваша корзина:</b>\n\n"
    kb = []

    for item in cart:
        text += f"{item['product']} ({item['variant']}) — {item['price']}₽ × {item['qty']}\n"
        kb.append([
            InlineKeyboardButton("➖", callback_data=f"qty_-_{item['key']}"),
            InlineKeyboardButton(f"{item['qty']}", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"qty_+_{item['key']}"),
            InlineKeyboardButton("🗑", callback_data=f"rm_{item['key']}")
        ])

    total = calc_total(cart)
    text += f"\n<b>Итого: {total} ₽</b>"

    kb.append([InlineKeyboardButton("Оформить заказ", callback_data="checkout_start")])

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


# ====== CHANGE QTY ======

@cart_router.callback_query(lambda c: c.data.startswith("qty_"))
async def change_qty(cb: types.CallbackQuery):
    _, op, key = cb.data.split("_")

    cart = await get_cart(cb.from_user.id)
    item = next((x for x in cart if x["key"] == key), None)

    if not item:
        await cb.answer()
        return

    if op == "+":
        item["qty"] += 1
    elif op == "-" and item["qty"] > 1:
        item["qty"] -= 1

    await save_cart(cb.from_user.id, cart)
    await cb.answer("Обновлено")
    await show_cart(cb.message)


# ====== REMOVE ITEM ======

@cart_router.callback_query(lambda c: c.data.startswith("rm_"))
async def remove_item(cb: types.CallbackQuery):
    key = cb.data[3:]

    cart = await get_cart(cb.from_user.id)
    cart = [x for x in cart if x["key"] != key]

    await save_cart(cb.from_user.id, cart)
    await cb.answer("Удалено")
    await show_cart(cb.message)
