# routers/catalog.py

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from google_sheets import load_products_safe

catalog_router = Router()


# ================================
# HELPERS
# ================================

async def load_products_fresh():
    return load_products_safe()


def is_parent(p: dict) -> bool:
    return p["parent_id"] == ""


def get_children(products, parent_id):
    return [
        p for p in products
        if p["parent_id"] == parent_id and p["price"] > 0
    ]


# ================================
# MAIN CATALOG
# ================================

@catalog_router.message(lambda m: m.text in ["🛍 Каталог", "🛍️ Каталог"])
async def show_catalog(msg: types.Message):
    products = await load_products_fresh()

    categories = sorted({p["category"] for p in products if is_parent(p)})

    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=f"📂 {c}", callback_data=f"cat:{c}")
    kb.adjust(1)

    await msg.answer(
        "<b>🛍 Каталог</b>\nВыберите категорию:",
        reply_markup=kb.as_markup()
    )


# ================================
# CATEGORY VIEW
# ================================

@catalog_router.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(cb: types.CallbackQuery):
    _, category = cb.data.split(":", 1)

    products = await load_products_fresh()
    parents = [
        p for p in products
        if is_parent(p) and p["category"] == category
    ]

    kb = InlineKeyboardBuilder()
    for p in parents:
        kb.button(text=p["name"], callback_data=f"prod:{p['id']}")

    # Навигация
    kb.button(text="⬅️ Назад в каталог", callback_data="catalog_back")
    kb.button(text="🛒 Корзина", callback_data="cart_open")
    kb.adjust(1)

    await cb.message.edit_text(
        f"<b>📂 {category}</b>\nВыберите товар:",
        reply_markup=kb.as_markup()
    )
    await cb.answer()


@catalog_router.callback_query(lambda c: c.data == "catalog_back")
async def back_to_catalog(cb: types.CallbackQuery):
    await show_catalog(cb.message)
    await cb.answer()


# ================================
# PRODUCT CARD
# ================================

@catalog_router.callback_query(lambda c: c.data.startswith("prod:"))
async def product_card(cb: types.CallbackQuery):
    _, parent_id = cb.data.split(":", 1)
    products = await load_products_fresh()

    parent = next((x for x in products if x["id"] == parent_id), None)
    if not parent:
        return await cb.answer("Товар не найден", show_alert=True)

    children = get_children(products, parent_id)

    # --- Клавиатура ---
    kb = InlineKeyboardBuilder()

    if not children:
        kb.button(
            text=f"🛒 Добавить — {parent['price']}₽",
            callback_data=f"addcart:{parent_id}:{parent_id}"
        )
    else:
        for v in children:
            label = v["variant_label"] or "Вариант"
            kb.button(
                text=f"{label} — {v['price']}₽",
                callback_data=f"addcart:{parent_id}:{v['id']}"
            )

    kb.button(text="⬅️ Назад", callback_data=f"cat:{parent['category']}")
    kb.button(text="🛒 Корзина", callback_data="cart_open")
    kb.adjust(1)

    # --- Текст карточки ---
    caption = (
        f"<b>{parent['name']}</b>\n"
        f"{parent['description']}\n"
    )

    # Удаляем старую кнопку (если была)
    try:
        await cb.message.delete()
    except:
        pass

    # Фото отображаем красиво
    if parent["file_id"]:
        await cb.message.answer_photo(
            parent["file_id"], caption, reply_markup=kb.as_markup()
        )
    elif parent["photo_url"]:
        msg = await cb.message.answer_photo(
            parent["photo_url"], caption, reply_markup=kb.as_markup()
        )
        # Сохраняем file_id чтобы ускорить бот
        try:
            parent["file_id"] = msg.photo[-1].file_id
        except:
            pass
    else:
        await cb.message.answer(caption, reply_markup=kb.as_markup())

    await cb.answer()
