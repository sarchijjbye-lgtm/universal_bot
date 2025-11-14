from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.sheets import load_products

catalog_router = Router()

# — КЭШ ТОВАРОВ —
PRODUCTS_CACHE = None


def get_products():
    global PRODUCTS_CACHE
    if PRODUCTS_CACHE is None:
        print("[CATALOG] Loading products from Google Sheets...")
        PRODUCTS_CACHE = load_products()
        print(f"[CATALOG] Loaded {len(PRODUCTS_CACHE)} items")
    return PRODUCTS_CACHE


# === Открыть каталог ===
@catalog_router.message(lambda m: m.text == "🛍 Каталог")
async def open_catalog(message: types.Message):
    products = get_products()
    categories = sorted({p["category"] for p in products})

    if not categories:
        await message.answer("Каталог пока пуст 😔")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"cat_{name}")]
            for name in categories
        ]
    )
    await message.answer("Выберите категорию:", reply_markup=kb)


# === Показать товары категории ===
@catalog_router.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(callback: types.CallbackQuery):
    products = get_products()
    cat = callback.data[4:]

    items = [p for p in products if p["category"] == cat]

    if not items:
        await callback.message.answer("В этой категории товаров пока нет.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=p["name"], callback_data=f"item_{p['id']}")]
            for p in items
        ]
    )

    await callback.message.answer(f"Категория: {cat}", reply_markup=kb)
    await callback.answer()


# === Показать товар ===
@catalog_router.callback_query(lambda c: c.data.startswith("item_"))
async def show_item(callback: types.CallbackQuery):
    products = get_products()
    item_id = callback.data[5:]

    product = next((x for x in products if str(x["id"]) == item_id), None)

    if not product:
        await callback.message.answer("Ошибка: товар не найден 😔")
        await callback.answer()
        return

    # Основной текст
    text = f"📦 <b>{product['name']}</b>\n\n{product['description']}"

    # Собираем клавиатуру
    ikb = []

    if product["variants"]:
        for v in product["variants"]:
            ikb.append([
                InlineKeyboardButton(
                    text=f"{v['label']} — {v['price']} ₽",
                    callback_data=f"add_{product['id']}_{v['id']}"
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

    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()
