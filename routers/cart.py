# routers/cart.py

from aiogram import Router
from aiogram.types import (
    CallbackQuery,
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
        return "🛒 <b>Корзина пуста</b>"

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

    for idx, item in enumerate(items):
        kb.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart_minus:{idx}"),
            InlineKeyboardButton(text=str(item["qty"]), callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_plus:{idx}")
        ])
        kb.append([
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"cart_del:{idx}")
        ])

    if items:
        kb.append([
            InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout:start")
        ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


# ============================================================
# ДОБАВЛЕНИЕ ТОВАРА
# ============================================================

@cart_router.callback_query(lambda c: c.data.startswith("addcart:"))
async def add_to_cart(callback: CallbackQuery):
    uid = callback.from_user.id
    _, parent_id, child_id = callback.data.split(":")

    # Подгружаем товары
    from google_sheets import load_products_safe
    products = load_products_safe()

    child = next((x for x in products if x["id"] == child_id), None)
    if not child:
        return await callback.answer("Ошибка: товар не найден", show_alert=True)

    user_cart = CART.setdefault(uid, [])
    existing = next((x for x in user_cart if x["child_id"] == child_id), None)

    if existing:
        existing["qty"] += 1
    else:
        user_cart.append({
            "child_id": child_id,
            "name": child["name"],
            "variant": child["variant_label"],
            "price": child["price"],
            "qty": 1
        })

    # Показать кнопку "Корзина"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_open")]
        ]
    )

    # ⚠️ редактируем текущее сообщение, чтобы не создавать новое
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer("✔ Добавлено в корзину")


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
        # Если fails — отправляем новое сообщение
        await callback.message.answer(text, reply_markup=kb)

    await callback.answer()


# ============================================================
# ➕ УВЕЛИЧЕНИЕ КОЛИЧЕСТВА
# ============================================================

@cart_router.callback_query(lambda c: c.data.startswith("cart_plus:"))
async def cart_plus(callback: CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split(":")[1])

    try:
        CART[uid][idx]["qty"] += 1
    except:
        return await callback.answer("Ошибка", show_alert=True)

    text = render_cart_text(uid)
    kb = build_cart_keyboard(uid)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Корзина обновлена")


# ============================================================
# ➖ УМЕНЬШЕНИЕ КОЛИЧЕСТВА
# ============================================================

@cart_router.callback_query(lambda c: c.data.startswith("cart_minus:"))
async def cart_minus(callback: CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split(":")[1])

    try:
        item = CART[uid][idx]
    except:
        return await callback.answer("Ошибка", show_alert=True)

    if item["qty"] > 1:
        item["qty"] -= 1
    else:
        CART[uid].pop(idx)

    text = render_cart_text(uid)
    kb = build_cart_keyboard(uid)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Корзина обновлена")


# ============================================================
# ❌ УДАЛЕНИЕ ТОВАРА
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
    await callback.answer("Товар удалён")
