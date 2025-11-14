# routers/cart.py

from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

CART = {}

def get_cart(uid):
    return CART.get(uid, [])

def calc_total(uid):
    return sum(item["price"] * item["qty"] for item in get_cart(uid))

cart_router = Router()


@cart_router.callback_query(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    _, pid, vid = callback.data.split(":")

    if user_id not in CART:
        CART[user_id] = []

    # достаём товар из глобального кеша
    from routers.catalog import PRODUCT_CACHE
    prod = next(p for p in PRODUCT_CACHE if str(p["id"]) == pid)
    var = next(v for v in prod["variants"] if str(v["id"]) == vid)

    CART[user_id].append({
        "name": prod["name"],
        "variant": var["label"],
        "price": var["price"],
        "qty": 1
    })

    await callback.answer("✔ Добавлено в корзину!", show_alert=False)


@cart_router.message(lambda m: m.text == "🛒 Корзина")
async def show_cart(msg: Message):

    cart = get_cart(msg.from_user.id)
    if not cart:
        return await msg.answer("🛒 Корзина пуста")

    text = "<b>Ваш заказ:</b>\n\n"
    for item in cart:
        text += f"— {item['name']} ({item['variant']}) — {item['price']}₽ x {item['qty']}\n"

    total = calc_total(msg.from_user.id)
    text += f"\n<b>Итого: {total}₽</b>"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout:start")]
        ]
    )

    await msg.answer(text, reply_markup=kb)
