from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.sheets import load_products

catalog_router = Router()
PRODUCTS = load_products()


@catalog_router.message(lambda m: m.text == "🛍 Каталог")
async def open_catalog(message: types.Message):
    categories = sorted(list({p["category"] for p in PRODUCTS}))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c, callback_data=f"cat_{c}")]
            for c in categories
        ]
    )

    await message.answer("Выберите категорию:", reply_markup=kb)


@catalog_router.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(callback: types.CallbackQuery):
    cat = callback.data[4:]

    items = [p for p in PRODUCTS if p["category"] == cat]

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
    item_id = callback.data[5:]
    product = next(x for x in PRODUCTS if x["id"] == item_id)

    text = f"📦 {product['name']}\n\n{product['description']}"

    ikb = []

    if product["variants"]:
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
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()
