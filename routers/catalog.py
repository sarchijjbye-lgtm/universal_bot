# catalog.py — PRODUCTION EDITION

from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from caching import cache_get, cache_set
from google_sheets import load_products_safe
import math

catalog_router = Router()

ITEMS_PER_PAGE = 6


# ====== LOAD PRODUCTS (cached) ======
async def get_products():
    data = await cache_get("products")
    if data:
        import json
        return json.loads(data)

    products = load_products_safe()  # безопасная версия (возвращает [] при ошибке)

    # нормализуем variants
    for p in products:
        if isinstance(p.get("variants"), list):
            for v in p["variants"]:
                if "name" not in v and "label" in v:
                    v["name"] = v["label"]
                    del v["label"]

    import json
    await cache_set("products", json.dumps(products), ttl=600)
    return products


# ====== CATEGORY SCREEN WITH PAGINATION ======

@catalog_router.message(lambda m: m.text == "🛍 Каталог")
async def open_catalog(message: types.Message):
    products = await get_products()
    categories = sorted(list({p["category"] for p in products}))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c, callback_data=f"cat_{c}_page_1")]
            for c in categories
        ]
    )

    await message.answer("Выберите категорию:", reply_markup=kb)


@catalog_router.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(cb: types.CallbackQuery):
    _, cat, _, page = cb.data.split("_")
    page = int(page)

    products = await get_products()
    items = [p for p in products if p["category"] == cat]

    total_pages = max(1, math.ceil(len(items) / ITEMS_PER_PAGE))
    start = (page - 1) * ITEMS_PER_PAGE
    chunk = items[start: start + ITEMS_PER_PAGE]

    kb = []
    for p in chunk:
        kb.append([InlineKeyboardButton(text=p["name"], callback_data=f"item_{p['id']}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"cat_{cat}_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"cat_{cat}_page_{page+1}"))

    if nav:
        kb.append(nav)

    await cb.message.edit_text(f"Категория: {cat}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await cb.answer()


# ====== ITEM CARD ======

@catalog_router.callback_query(lambda c: c.data.startswith("item_"))
async def show_item(cb: types.CallbackQuery):
    item_id = cb.data[5:]
    products = await get_products()
    product = next((x for x in products if x["id"] == item_id), None)

    if not product:
        await cb.message.answer("Ошибка: товар не найден")
        return

    # ==== file_id CDN ====
    file_id = await cache_get(f"fileid:{item_id}")
    if not file_id:
        photo = product.get("photo_url") or "https://via.placeholder.com/600x400?text=No+Image"
    else:
        photo = file_id

    # Красивая HTML карточка
    text = (
        f"<b>{product['name']}</b>\n"
        f"<i>{product['description']}</i>\n\n"
        f"<b>Выберите объём:</b>"
    )

    kb = []
    for v in product["variants"]:
        kb.append([
            InlineKeyboardButton(
                text=f"{v['name']} — {v['price']} ₽",
                callback_data=f"add_{item_id}_{v['id']}"
            )
        ])

    try:
        await cb.message.answer_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
    except Exception as e:
        await cb.message.answer("Фото недоступно, но товар можно заказать:")
        await cb.message.answer(
            text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )

    await cb.answer()
