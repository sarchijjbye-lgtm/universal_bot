from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.sheets import load_products

cart_router = Router()

# Хранилище корзин
USER_CARTS = {}  # user_id: [ {id, name, variant, price, qty} ]


# === utils ===

def get_cart(user_id):
    return USER_CARTS.get(user_id, [])


def save_cart(user_id, items):
    USER_CARTS[user_id] = items


def add_to_cart(user_id, product_id, variant_name, price, product_name):
    cart = get_cart(user_id)

    # ищем существующую позицию
    for item in cart:
        if item["id"] == product_id and item["variant"] == variant_name:
            item["qty"] += 1
            save_cart(user_id, cart)
            return

    # добавляем новый товар
    cart.append({
        "id": product_id,
        "name": product_name,
        "variant": variant_name,
        "price": price,
        "qty": 1
    })

    save_cart(user_id, cart)


def change_qty(user_id, idx, delta):
    cart = get_cart(user_id)

    if 0 <= idx < len(cart):
        cart[idx]["qty"] += delta

        if cart[idx]["qty"] <= 0:
            cart.pop(idx)

    save_cart(user_id, cart)


def clear_cart(user_id):
    USER_CARTS[user_id] = []


def get_total(user_id):
    cart = get_cart(user_id)
    return sum(item["price"] * item["qty"] for item in cart)


# === HANDLERS ===

@cart_router.callback_query(F.data.startswith("add_"))
async def add_item(callback: types.CallbackQuery):
    """
    Формат callback: add_{productId}_{variantName}
    Например: add_3_250 мл
    """
    parts = callback.data.split("_", 2)
    product_id = parts[1]
    variant_name = parts[2]

    products = load_products()
    product = next((x for x in products if x["id"] == product_id), None)

    if not product:
        await callback.answer("Ошибка: товар не найден")
        return

    if product["variants"]:
        variant = next((v for v in product["variants"] if v["name"] == variant_name), None)
        price = variant["price"]
    else:
        price = product["base_price"]

    add_to_cart(
        user_id=callback.from_user.id,
        product_id=product_id,
        variant_name=variant_name,
        price=price,
        product_name=product["name"],
    )

    await callback.answer("Добавлено!")
    await show_cart(callback.message, callback.from_user.id)


@cart_router.message(F.text == "🛒 Корзина")
async def open_cart(message: types.Message):
    await show_cart(message, message.from_user.id)


async def show_cart(message: types.Message, user_id: int):
    cart = get_cart(user_id)

    if not cart:
        await message.answer("🛒 Ваша корзина пуста.")
        return

    total = get_total(user_id)

    text = "🛒 <b>Ваша корзина:</b>\n\n"
    kb_rows = []

    for idx, item in enumerate(cart):
        text += (
            f"• <b>{item['name']}</b> ({item['variant']})\n"
            f"   {item['price']} ₽ × {item['qty']} = <b>{item['price'] * item['qty']} ₽</b>\n\n"
        )

        kb_rows.append([
            InlineKeyboardButton(text="➖", callback_data=f"dec_{idx}"),
            InlineKeyboardButton(text="➕", callback_data=f"inc_{idx}")
        ])

    text += f"💰 <b>Итого: {total} ₽</b>"

    kb = InlineKeyboardMarkup(
        inline_keyboard=kb_rows + [
            [InlineKeyboardButton(text="🧹 Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="📦 Оформить заказ", callback_data="checkout")]
        ]
    )

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@cart_router.callback_query(F.data.startswith("inc_"))
async def inc_item(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    change_qty(callback.from_user.id, idx, +1)
    await callback.answer("Количество увеличено")
    await show_cart(callback.message, callback.from_user.id)


@cart_router.callback_query(F.data.startswith("dec_"))
async def dec_item(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    change_qty(callback.from_user.id, idx, -1)
    await callback.answer("Количество уменьшено")
    await show_cart(callback.message, callback.from_user.id)


@cart_router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: types.CallbackQuery):
    clear_cart(callback.from_user.id)
    await callback.answer("Корзина очищена")
    await callback.message.answer("🧹 Корзина очищена.")
