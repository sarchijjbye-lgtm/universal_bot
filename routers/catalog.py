# routers/catalog.py

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google_sheets import load_products_safe

catalog_router = Router()


# === Load fresh products every time ===
async def load_products_fresh():
    return load_products_safe()


# === Show categories ===
@catalog_router.message(lambda m: m.text in ["🛍 Каталог", "🛍️ Каталог"])
async def show_catalog(message: types.Message):
    products = await load_products_fresh()

    categories = sorted({p["category"] for p in products})

    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=c, callback_data=f"cat:{c}")
    kb.adjust(1)

    await message.answer("Выберите категорию:", reply_markup=kb.as_markup())


# === Show items in category ===
@catalog_router.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(callback: types.CallbackQuery):
    _, category = callback.data.split(":", 1)

    products = await load_products_fresh()
    items = [p for p in products if p["category"] == category]

    kb = InlineKeyboardBuilder()
    for p in items:
        kb.button(text=p["name"], callback_data=f"prod:{p['id']}")
    kb.adjust(1)

    await callback.message.edit_text(
        f"Категория: <b>{category}</b>\nВыберите товар:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# === Product card ===
@catalog_router.callback_query(lambda c: c.data.startswith("prod:"))
async def product_card(callback: types.CallbackQuery):
    _, product_id = callback.data.split(":", 1)

    products = await load_products_fresh()
    p = next((x for x in products if str(x["id"]) == product_id), None)

    if not p:
        return await callback.answer("Ошибка: товар не найден", show_alert=True)

    # STOCK / SUPPLIER TEXT
    stock_text = f"\nВ наличии: {p['stock']} шт." if p.get("stock") not in (None, "") else ""
    supplier_text = f"\nПоставщик: {p['supplier']}" if p.get("supplier") else ""

    caption = (
        f"<b>{p['name']}</b>\n"
        f"{p['description']}\n"
        f"{stock_text}"
        f"{supplier_text}\n\n"
        f"👇 Выберите вариант:"
    )

    # ==== Show photo ====
    if p.get("file_id"):
        await callback.message.answer_photo(
            p["file_id"],
            caption=caption,
            reply_markup=_variants_keyboard(p)
        )
    elif p.get("photo_url") and p["photo_url"].startswith("http"):
        msg = await callback.message.answer_photo(
            p["photo_url"],
            caption=caption,
            reply_markup=_variants_keyboard(p)
        )
        # Cache Telegram file_id
        try:
            p["file_id"] = msg.photo[-1].file_id
        except:
            pass
    else:
        await callback.message.answer(
            caption,
            reply_markup=_variants_keyboard(p)
        )

    await callback.answer()


# === Variants buttons ===
def _variants_keyboard(product):
    kb = InlineKeyboardBuilder()

    for v in product["variants"]:
        kb.button(
            text=f"{v['label']} — {v['price']}₽",
            callback_data=f"addcart:{product['id']}:{v['id']}"
        )

    kb.adjust(1)
    return kb.as_markup()
