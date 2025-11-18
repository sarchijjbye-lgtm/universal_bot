# routers/cart.py

from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# user_id → list[{child_id, name, variant, price, qty}]
CART = {}

cart_router = Router()


# ============================================================
# HELPERS
# ============================================================

def get_cart(uid: int):
    return CART.get(uid, [])


def calc_total(uid: int):
    return sum(item["price"] * item["qty"] for item in get_cart(uid))


def clear_cart(uid: int):
    if uid in CART:
        del CART[uid]


def render_cart_text(uid: int):
    items = get_cart(uid)
    if not items:
        return "🛒 <b>Корзина пуста</b>\n\nДобавьте товары из каталога."

    lines = ["<b>🛒 Ваша корзина:</b>", ""]
    for item in items:
        lines.append(
            f"• {item['name']} ({item['variant']}) — {item['price']}₽ × {item['qty']}"
        )
    lines.append("")
    lines.append(f"<b>Итого: {calc_total(uid)}₽</b>")

    return "\n".join(lines)


def build_cart_keyboard(uid: int):
    items = get_cart(uid)
    kb = []

    if not items:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛍 В каталог", callback_data="catalog_back")]
            ]
        )

    for idx, item in enumerate(items):
        kb.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart_minus:{idx}"),
            InlineKeyboardButton(text=str(item["qty"]), callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_plus:{idx}")
        ])
        kb.append([
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"cart_del:{idx}")
        ])

    kb.append([InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout:start")])
    kb.append([InlineKeyboardButton(text="🛍 В каталог", callback_data="catalog_back")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


# ============================================================
# ОБРАБОТЧИК REPLY-КНОПКИ "Корзина"
# ============================================================

@cart_router.message(lambda m: m.text in ["🛒 Корзина", "Корзина"])
async def cart_from_message(msg: Message):
    uid = msg.from_user.id

    text = render_cart_text(uid)
    kb = build_cart_keyboard(uid)

    await msg.answer(text, reply_markup=kb)


# ============================================================
# ДОБАВЛЕНИЕ ТОВАРА В КОРЗИНУ
# ============================================================

@cart_router.callback_query(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    _, parent_id, child_id = callback.data.split(":")

    from google_sheets import load_products_safe
    products = load_products_safe()

    child = next((x for x in products if x["id"] == child_id), None)
    if not child:
        return await callback.answer("Ошибка: вариация не найдена", show_alert=True)

    cart = CART.setdefault(user_id, [])
    existing = next((x for x in cart if x["child_id"] == child_id), None)

    if existing:
        existing["qty"] += 1
    else:
        cart.append({
            "child_id": child_id,
            "name": child["name"],
            "variant": child["variant_label"],
            "price": child["price"],
            "qty": 1
        })

    # Клавиатура после добавления
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_open")],
            [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog_back")],
        ]
    )

    await callback.message.answer("✔ Добавлено в корзину", reply_markup=kb)
    await callback.answer()


# ============================================================
# ОТКРЫТЬ КОРЗИНУ
# ============================================================

@cart_router.callback_query(lambda c: c.data == "cart_open")
async def cart_open(callback: CallbackQuery):
    uid = callback.from_user.id

    text = render_cart_text(uid)
    kb = build_cart_keyboard(uid)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except:
        await callback.message.answer(text, reply_markup=kb)

    await callback.answer()


# ============================================================
# ➕ УВЕЛИЧИТЬ
# ============================================================

@cart_router.callback_query(lambda c: c.data.startswith("cart_plus:"))
async def cart_plus(callback: CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split(":")[1])

    try:
        CART[uid][idx]["qty"] += 1
    except:
        return await callback.answer("Ошибка")

    text = render_cart_text(uid)
    kb = build_cart_keyboard(uid)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Количество увеличено")


# ============================================================
# ➖ УМЕНЬШИТЬ
# ============================================================

@cart_router.callback_query(lambda c: c.data.startswith("cart_minus:"))
async def cart_minus(callback: CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split(":")[1])

    try:
        item = CART[uid][idx]
    except:
        return await callback.answer("Ошибка")

    if item["qty"] > 1:
        item["qty"] -= 1
    else:
        CART[uid].pop(idx)

    text = render_cart_text(uid)
    kb = build_cart_keyboard(uid)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Количество уменьшено")


# ============================================================
# ❌ УДАЛИТЬ
# ============================================================

@cart_router.callback_query(lambda c: c.data.startswith("cart_del:"))
async def cart_del(callback: CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split(":")[1])

    try:
        CART[uid].pop(idx)
    except:
        pass

    text = render_cart_text(uid)
    kb = build_cart_keyboard(uid)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Удалено")
