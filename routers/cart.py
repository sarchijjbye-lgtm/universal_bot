from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_init import bot
from utils.sheets import load_products

cart_router = Router()
PRODUCTS = load_products()

CART = {}  # {user_id: [{id, name, variant, price}]}


def get_total(cart):
    return sum(x["price"] for x in cart)


@cart_router.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    _, prod_id, variant = callback.data.split("_")

    product = next(p for p in PRODUCTS if p["id"] == prod_id)

    if variant == "base":
        price = product["base_price"]
        variant_name = ""
    else:
        v = next(v for v in product["variants"] if v["name"] == variant)
        price = v["price"]
        variant_name = variant

    item = {
        "id": prod_id,
        "name": product["name"],
        "variant": variant_name,
        "price": price
    }

    CART.setdefault(callback.from_user.id, []).append(item)

    await callback.answer("Добавлено в корзину!")


@cart_router.message(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    cart = CART.get(message.from_user.id, [])

    if not cart:
        await message.answer("Корзина пуста.")
        return

    text = "🛒 *Ваш заказ*\n\n"
    for i, item in enumerate(cart, start=1):
        variant_text = f" ({item['variant']})" if item["variant"] else ""
        text += f"{i}. {item['name']}{variant_text} — {item['price']} ₽\n"

    text += f"\nИтого: *{get_total(cart)} ₽*"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="📦 Оформить заказ", callback_data="checkout")]
        ]
    )

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)


@cart_router.callback_query(lambda c: c.data == "clear_cart")
async def clear(callback: types.CallbackQuery):
    CART[callback.from_user.id] = []
    await callback.message.answer("Корзина очищена.")
    await callback.answer()
