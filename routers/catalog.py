from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.sheets import load_products

catalog_router = Router()

# КЕШ ПРОДУКТОВ
PRODUCTS_CACHE = None


def get_products():
    global PRODUCTS_CACHE
    if PRODUCTS_CACHE is None:
        print("[CATALOG] Loading products from Google Sheets...")
        PRODUCTS_CACHE = load_products()

        # --- FIX: гарантируем правильный формат variants ---
        for p in PRODUCTS_CACHE:
            if isinstance(p.get("variants"), list):
                for v in p["variants"]:
                    if "name" not in v and "label" in v:
                        v["name"] = v["label"]  # исправляем
                        del v["label"]
        print(f"[CATALOG] Loaded {len(PRODUCTS_CACHE)} items")

    return PRODUCTS_CACHE


@catalog_router.message(lambda m: m.text == "🛍 Каталог")
async def open_catalog(message: types.Message):
    products = get_products()
    categories = sorted(list({p["category"] for p in products}))

    if not categories:
        await message.answer("Каталог пока пуст 😔")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c, callback_data=f"cat_{c}")]
            for c in categories
        ]
    )

    await message.answer("Выберите категорию:", reply_markup=kb)


@catalog_router.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(callback: types.CallbackQuery):
    products = get_products()
    cat = callback.data[4:]

    items = [p for p in products if p["category"] == cat]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=p["name"], callback_data=f"item_{p['id']}")]
            for p in items
        ]
    )

    await callback.message.answer(f"Категория: {cat}", reply_markup=kb)
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data.startswith("item_"))
async def show_item(callback: types.CallbackQuery):
    products = get_products()
    item_id = callback.data[5:]

    product = next((x for x in products if x["id"] == item_id), None)

    if not product:
        await callback.message.answer("Ошибка: товар не найден 😔")
        return

    # --- текст карточки ---
    text = f"📦 <b>{product['name']}</b>\n\n{product['description']}"

    # --- фото (если нет — ставим плейсхолдер) ---
    photo_url = product.get("photo_url") or "https://via.placeholder.com/600x400?text=No+Image"

    # --- кнопки вариантов ---
    ikb = []

    if product.get("variants"):
        for v in product["variants"]:
            ikb.append([
                InlineKeyboardButton(
                    text=f"{v['name']} — {v['price']} ₽",
                    callback_data=f"add_{product['id']}_{v['name']}"
                )
            ])
    else:
        ikb.append([
            InlineKeyboardButton(
                text=f"Добавить — {product['base_price']} ₽",
                callback_data=f"add_{product['id']}_base"
            )
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=ikb)

    # --- отправляем фото + карточку товара ---
    await callback.message.answer_photo(
        photo=photo_url,
        caption=text,
        parse_mode="HTML",
        reply_markup=kb
    )

    await callback.answer()
