# routers/catalog.py

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google_sheets import load_products_safe

catalog_router = Router()


async def load_products_fresh():
    return load_products_safe()


def get_parents(products):
    return [p for p in products if p["parent_id"] is None]


def get_children(products, parent_id):
    return [p for p in products if p["parent_id"] == parent_id and p["price"] > 0]


@catalog_router.message(lambda m: m.text in ["🛍 Каталог", "🛍️ Каталог"])
async def show_catalog(message: types.Message):

    products = await load_products_fresh()
    categories = sorted({p["category"] for p in products if p["parent_id"] is None})

    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=c, callback_data=f"cat:{c}")

    kb.adjust(1)
    await message.answer("Выберите категорию:", reply_markup=kb.as_markup())


@catalog_router.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(callback: types.CallbackQuery):

    _, category = callback.data.split(":", 1)
    products = await load_products_fresh()

    parents = [p for p in products if p["category"] == category and p["parent_id"] is None]

    kb = InlineKeyboardBuilder()
    for p in parents:
        kb.button(text=p["name"], callback_data=f"prod:{p['id']}")

    kb.adjust(1)
    await callback.message.edit_text(f"<b>{category}</b>\nВыберите товар:", reply_markup=kb.as_markup())
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data.startswith("prod:"))
async def product_card(callback: types.CallbackQuery):

    _, parent_id = callback.data.split(":", 1)
    products = await load_products_fresh()

    parent = next((x for x in products if x["id"] == parent_id), None)
    children = get_children(products, parent_id)

    if not parent:
        return await callback.answer("Товар не найден", show_alert=True)

    caption = (
        f"<b>{parent['name']}</b>\n"
        f"{parent['description']}\n"
        f"\n👇 Выберите вариант:"
    )

    # PHOTO
    if parent["file_id"]:
        await callback.message.answer_photo(parent["file_id"], caption)
    elif parent["photo_url"]:
        msg = await callback.message.answer_photo(parent["photo_url"], caption)
        try:
            parent["file_id"] = msg.photo[-1].file_id
        except:
            pass
    else:
        await callback.message.answer(caption)

    kb = InlineKeyboardBuilder()
    for v in children:
        label = v["variant_label"] or "Вариант"
        kb.button(text=f"{label} — {v['price']}₽", callback_data=f"addcart:{parent_id}:{v['id']}")

    kb.adjust(1)

    await callback.message.answer("Выберите вариант:", reply_markup=kb.as_markup())
    await callback.answer()
