# routers/catalog.py

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google_sheets import load_products_safe

catalog_router = Router()


async def load_products_fresh():
    return load_products_safe()


# ===== Helpers =====

def is_parent(p: dict) -> bool:
    return p["parent_id"] == ""  # parent_id пустая строка = parent row


def get_children(products, parent_id):
    return [
        p for p in products
        if p["parent_id"] == parent_id and p["price"] > 0
    ]


# ===== Show catalog =====

@catalog_router.message(lambda m: m.text in ["🛍 Каталог", "🛍️ Каталог"])
async def show_catalog(msg: types.Message):
    products = await load_products_fresh()

    categories = sorted({
        p["category"] for p in products
        if is_parent(p)
    })

    if not categories:
        return await msg.answer("Категории не найдены.")

    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=c, callback_data=f"cat:{c}")
    kb.adjust(1)

    await msg.answer("Выберите категорию:", reply_markup=kb.as_markup())


# ===== Show items in category =====

@catalog_router.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(cb: types.CallbackQuery):
    _, category = cb.data.split(":", 1)

    products = await load_products_fresh()
    parents = [
        p for p in products
        if is_parent(p) and p["category"] == category
    ]

    if not parents:
        return await cb.answer("Пока нет товаров", show_alert=True)

    kb = InlineKeyboardBuilder()
    for p in parents:
        kb.button(text=p["name"], callback_data=f"prod:{p['id']}")
    kb.adjust(1)

    await cb.message.edit_text(
        f"<b>{category}</b>\nВыберите товар:",
        reply_markup=kb.as_markup()
    )
    await cb.answer()


# ===== Product card =====

@catalog_router.callback_query(lambda c: c.data.startswith("prod:"))
async def product_card(cb: types.CallbackQuery):
    _, parent_id = cb.data.split(":", 1)

    products = await load_products_fresh()

    parent = next((x for x in products if x["id"] == parent_id), None)
    if not parent:
        return await cb.answer("Товар не найден", show_alert=True)

    children = get_children(products, parent_id)

    caption = (
        f"<b>{parent['name']}</b>\n"
        f"{parent['description']}\n"
    )

    # ---- show photo ----
    if parent["file_id"]:
        await cb.message.answer_photo(parent["file_id"], caption)
    elif parent["photo_url"]:
        msg = await cb.message.answer_photo(parent["photo_url"], caption)
        try:
            parent["file_id"] = msg.photo[-1].file_id
        except:
            pass
    else:
        await cb.message.answer(caption)

    # ===== Variants =====
    kb = InlineKeyboardBuilder()

    # case A: товар БЕЗ вариаций
    if not children:
        kb.button(
            text=f"Добавить — {parent['price']}₽",
            callback_data=f"addcart:{parent_id}:{parent_id}"
        )
        kb.adjust(1)
        await cb.message.answer("Добавить в корзину:", reply_markup=kb.as_markup())
        return await cb.answer()

    # case B: обычные вариации
    for v in children:
        name = v["variant_label"] or "Вариант"
        kb.button(
            text=f"{name} — {v['price']}₽",
            callback_data=f"addcart:{parent_id}:{v['id']}"
        )

    kb.adjust(1)
    await cb.message.answer("Выберите вариант:", reply_markup=kb.as_markup())
    await cb.answer()
