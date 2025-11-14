from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.sheets import load_products


cart_router = Router()

# ❗ Корзины пользователей
USER_CARTS = {}  # {user_id: [{id, name, variant, price, qty}]}


def get_products():
    """Грузим товары (без кеша — кеш в catalog.py)"""
    return load_products()


# ======================
# 📌 Добавить в корзину
# ======================
@cart_router.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    """
    callback_data = add_{product_id}_{variant}
    """
    user_id = callback.from_user.id
    _, product_id, variant = callback.data.split("_", 2)

    products = get_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    # Найти цену варианта
    if product.get("variants"):
        v = next((v for v in product["variants"] if v["name"] == variant), None)
        if not v:
            await callback.answer("Вариант не найден", show_alert=True)
            return
        price = v["price"]
    else:
        price = product["base_price"]

    # Корзина пользователя
    cart = USER_CARTS.setdefault(user_id, [])

    # Если товар с этим вариантом уже есть — увеличиваем количество
    existing = next((x for x in cart if x["id"] == product_id and x["variant"] == variant), None)

    if existing:
        existing["qty"] += 1
    else:
        cart.append({
            "id": product_id,
            "name": product["name"],
            "variant": variant,
            "price": price,
            "qty": 1
        })

    await callback.answer("Добавлено в корзину 🎉")


# ======================
# 📌 Показать корзину
# ======================
@cart_router.message(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    cart = USER_CARTS.get(user_id, [])

    if not cart:
        await message.answer("🛒 Корзина пуста")
        return

    # Общая сумма
    total = sum(item["price"] * item["qty"] for item in cart)

    # Формируем сообщение
    text = "<b>🛒 Ваша корзина:</b>\n\n"
    for item in cart:
        text += (
            f"<b>{item['name']}</b> — {item['variant']}\n"
            f"Цена: {item['price']} ₽ × {item['qty']} = <b>{item['price'] * item['qty']} ₽</b>\n"
            f"<i>ID: {item['id']}</i>\n\n"
        )

    text += f"<b>Итого: {total} ₽</b>"

    # Кнопки управления
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Увеличить", callback_data="cart_inc")],
        [InlineKeyboardButton(text="➖ Уменьшить", callback_data="cart_dec")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="cart_remove")],
        [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="cart_clear")]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


# ======================
# ➕ Увеличить количество последнего товара
# ======================
@cart_router.callback_query(lambda c: c.data == "cart_inc")
async def cart_inc(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = USER_CARTS.get(user_id, [])

    if cart:
        cart[-1]["qty"] += 1

    await callback.answer("Количество увеличено 👍")
    await show_cart(callback.message)


# ======================
# ➖ Уменьшить количество последнего товара
# ======================
@cart_router.callback_query(lambda c: c.data == "cart_dec")
async def cart_dec(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = USER_CARTS.get(user_id, [])

    if cart:
        if cart[-1]["qty"] > 1:
            cart[-1]["qty"] -= 1
        else:
            cart.pop()

    await callback.answer("Количество уменьшено")
    await show_cart(callback.message)


# ======================
# ❌ Удалить последний товар
# ======================
@cart_router.callback_query(lambda c: c.data == "cart_remove")
async def cart_remove(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = USER_CARTS.get(user_id, [])

    if cart:
        cart.pop()

    await callback.answer("Товар удалён")
    await show_cart(callback.message)


# ======================
# 🧹 Полная очистка корзины
# ======================
@cart_router.callback_query(lambda c: c.data == "cart_clear")
async def cart_clear(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    USER_CARTS[user_id] = []

    await callback.answer("Корзина очищена")
    await callback.message.answer("🧹 Корзина пустая")
