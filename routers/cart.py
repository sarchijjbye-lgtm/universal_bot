from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.sheets import load_products

cart_router = Router()

# Простая in-memory корзина: {user_id: [items]}
CART = {}
PRODUCTS = load_products()


def get_total(items: list) -> int:
    return sum(x["price"] for x in items)


@cart_router.message(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    uid = message.from_user.id
    items = CART.get(uid, [])

    if not items:
        await message.answer("Ваша корзина пуста.")
        return

    text = "🛒 *Ваша корзина*\n\n" + "\n".join(
        f"{i+1}. {x['name']} ({x['variant']}) — {x['price']} ₽"
        for i, x in enumerate(items)
    )
    text += f"\n\nИтого: {get_total(items)} ₽"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")]
        ]
    )

    await message.answer(text, reply_markup=kb)


@cart_router.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    uid = callback.from_user.id
    # формат: add_{product_id}_{variant}
    _, pid, variant = callback.data.split("_")

    product = next(x for x in PRODUCTS if x["id"] == pid)

    if variant == "base":
        price = product["base_price"]
    else:
        price = next(v["price"] for v in product["variants"] if v["name"] == variant)

    CART.setdefault(uid, []).append({
        "name": product["name"],
        "variant": variant,
        "price": price
    })

    await callback.answer("Добавлено в корзину!")
