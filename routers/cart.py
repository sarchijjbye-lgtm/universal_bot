from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.sheets import load_products

catalog_router = Router()
PRODUCTS = load_products()

@catalog_router.message(commands=['catalog'])
async def show_categories(message: types.Message):
    cats = list(set(p["category"] for p in PRODUCTS))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c, callback_data=f"cat_{c}")]
        for c in cats
    ])
    await message.answer("Выберите категорию:", reply_markup=kb)

@catalog_router.callback_query(lambda c: c.data.startswith("cat_"))
async def show_products(callback: types.CallbackQuery):
    cat = callback.data.split("_",1)[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for p in PRODUCTS:
        if p["category"] == cat:
            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=p["name"], callback_data=f"product_{p['id']}"
                )
            ])
    await callback.message.answer(f"Товары категории {cat}:", reply_markup=kb)

@catalog_router.callback_query(lambda c: c.data.startswith("product_"))
async def product_card(callback: types.CallbackQuery):
    pid = callback.data.split("_")[1]
    p = next((x for x in PRODUCTS if x["id"] == pid), None)
    if not p:
        return await callback.answer("Товар не найден")

    caption = f"<b>{p['name']}</b>\n\n{p['description']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[])

    if p["variants"]:
        caption += "\n\n<b>Выберите вариант:</b>"
        for v in p["variants"]:
            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{v['label']} — {v['price']} ₽",
                    callback_data=f"addvar_{p['id']}_{v['id']}"
                )
            ])
    else:
        caption += f"\n\nЦена: {p['base_price']} ₽"
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text="Добавить в корзину",
                callback_data=f"addbase_{p['id']}"
            )
        ])

    await callback.message.answer_photo(
        photo=p["photo"],
        caption=caption,
        parse_mode="HTML",
        reply_markup=kb
    )
