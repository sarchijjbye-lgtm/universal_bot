# routers/catalog.py

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from google_sheets import load_products_safe

catalog_router = Router()


# ======================================
# HELPERS
# ======================================

def is_parent(item):
    return item["parent_id"] == ""


def get_children(items, parent_id):
    return [
        p for p in items
        if p["parent_id"] == parent_id and p["price"] > 0 and p["active"]
    ]


async def load_all():
    return load_products_safe()


# ======================================
# MAIN CATALOG
# ======================================

@catalog_router.message(lambda m: m.text in ["🛍 Каталог", "🛍️ Каталог"])
async def show_catalog(msg: types.Message):
    products = await load_all()

    categories = sorted({p["category"] for p in products if is_parent(p)})

    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=f"📂 {c}", callback_data=f"cat:{c}")
    kb.adjust(1)

    await msg.answer(
        "<b>🛍 Каталог</b>\nВыберите категорию:",
        reply_markup=kb.as_markup()
    )


# ======================================
# CATEGORY
# ======================================

@catalog_router.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(cb: types.CallbackQuery):
    _, category = cb.data.split(":", 1)

    products = await load_all()
    parents = [
        p for p in products
        if is_parent(p) and p["category"] == category and p["active"]
    ]

    kb = InlineKeyboardBuilder()
    for p in parents:
        kb.button(text=p["name"], callback_data=f"prod:{p['id']}")

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


# ======================================
# PRODUCT CARD
# ======================================

@catalog_router.callback_query(lambda c: c.data.startswith("prod:"))
async def product_card(cb: types.CallbackQuery):
    _, parent_id = cb.data.split(":", 1)

    products = await load_all()

    parent = next((p for p in products if p["id"] == parent_id), None)
    if not parent:
        return await cb.answer("Товар не найден", show_alert=True)

    children = get_children(products, parent_id)

    # ----- Клавиатура -----
    kb = InlineKeyboardBuilder()

    if not children:
        kb.button(
            text=f"🛒 Добавить — {parent['price']}₽",
            callback_data=f"addcart:{parent_id}:{parent_id}"
        )
    else:
        for child in children:
            label = child["variant_label"] or "Вариант"
            kb.button(
                text=f"{label} — {child['price']}₽",
                callback_data=f"addcart:{parent_id}:{child['id']}"
            )

    kb.button(text="⬅️ Назад", callback_data=f"cat:{parent['category']}")
    kb.button(text="🛒 Корзина", callback_data="cart_open")
    kb.adjust(1)

    # ----- Красивое форматирование -----

    desc = parent["description"].strip()

    variations_text = ""
    if children:
        variations_text = "\n<b>Доступные варианты:</b>\n" + "\n".join(
            [f"• {c['variant_label']} — {c['price']}₽" for c in children]
        )

    caption = (
        f"🔥 <b>{parent['name']}</b>\n\n"
        f"{desc}\n"
        f"{variations_text}"
    )

    # удалить предыдущее сообщение, если возможно
    try:
        await cb.message.delete()
    except:
        pass

    # ----- Фото -----
    if parent["file_id"]:
        await cb.message.answer_photo(
            parent["file_id"],
            caption,
            reply_markup=kb.as_markup()
        )
    elif parent["photo_url"]:
        msg = await cb.message.answer_photo(
            parent["photo_url"],
            caption,
            reply_markup=kb.as_markup()
        )

        # кэшируем file_id
        try:
            parent["file_id"] = msg.photo[-1].file_id
        except:
            pass
    else:
        await cb.message.answer(
            caption,
            reply_markup=kb.as_markup()
        )

    await cb.answer()
