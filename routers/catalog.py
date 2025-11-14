# routers/catalog.py

from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from google_sheets import load_products_safe
from settings import get_setting

catalog_router = Router()

PRODUCT_CACHE = None

def load_catalog():
    global PRODUCT_CACHE
    if PRODUCT_CACHE is None:
        PRODUCT_CACHE = load_products_safe()
    return PRODUCT_CACHE


@catalog_router.message(lambda m: m.text == "🛍 Каталог")
async def open_catalog(msg: Message):
    products = load_catalog()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=prod["name"], callback_data=f"product:{prod['id']}")]
            for prod in products
        ]
    )

    await msg.answer(
        f"🛍 <b>{get_setting('shop_name')}</b>\nВыберите товар:",
        reply_markup=kb
    )


@catalog_router.callback_query(lambda c: c.data.startswith("product:"))
async def show_product(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]
    products = load_catalog()

    prod = next((p for p in products if str(p["id"]) == str(product_id)), None)

    if not prod:
        return await callback.answer("❌ Товар не найден")

    # варианты
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{v['label']} — {v['price']}₽",
                callback_data=f"addcart:{prod['id']}:{v['id']}"
            )]
            for v in prod["variants"]
        ]
    )

    text = f"""
<b>{prod['name']}</b>

{prod['description']}

Выберите объём:
"""

    await callback.message.answer_photo(
        photo=prod["photo_file_id"],
        caption=text,
        reply_markup=kb
    )
    await callback.answer()
