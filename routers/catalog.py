from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from routers.catalog import PRODUCTS

cart_router = Router()
user_carts = {}  # user_id: [items]

def find_product(pid):
    return next((p for p in PRODUCTS if p["id"] == pid), None)

@cart_router.callback_query(lambda c: c.data.startswith("addvar_") or c.data.startswith("addbase_"))
async def add_to_cart(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    mode = parts[0]
    pid = parts[1]
    p = find_product(pid)
    uid = callback.from_user.id

    if mode == "addvar":
        var_id = parts[2]
        v = next((x for x in p["variants"] if str(x["id"]) == var_id), None)
        price = v["price"]
        label = v["label"]
    else:
        price = p["base_price"]
        label = None

    user_carts.setdefault(uid, []).append({
        "product_id": pid,
        "name": p["name"],
        "variant_label": label,
        "price": price,
        "qty": 1
    })

    await callback.answer("Добавлено!")

@cart_router.message(commands=['cart'])
async def show_cart(message: types.Message):
    uid = message.from_user.id
    cart = user_carts.get(uid, [])

    if not cart:
        return await message.answer("Корзина пуста")

    total = 0
    txt = "🛒 <b>Корзина</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for i, item in enumerate(cart):
        line_total = item["price"] * item["qty"]
        total += line_total
        title = item["name"]
        if item["variant_label"]:
            title += f" ({item['variant_label']})"

        txt += f"{i+1}. {title} — {item['price']} ₽ x {item['qty']} = {line_total} ₽\n"
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=f"Удалить {i+1}", callback_data=f"del_{i}")
        ])

    txt += f"\n<b>Итого:</b> {total} ₽"

    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Очистить корзину", callback_data="clear_cart")
    ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Оформить заказ", callback_data="make_order")
    ])

    await message.answer(txt, parse_mode="HTML", reply_markup=kb)

@cart_router.callback_query(lambda c: c.data.startswith("del_"))
async def delete_item(callback: types.CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split("_")[1])
    if uid in user_carts and 0 <= idx < len(user_carts[uid]):
        user_carts[uid].pop(idx)
    await callback.answer("Удалено!")
    await show_cart(callback.message)

@cart_router.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_carts[callback.from_user.id] = []
    await callback.answer("Корзина очищена!")
    await callback.message.answer("Корзина пуста.")
