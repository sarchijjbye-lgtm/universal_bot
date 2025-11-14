from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google_sheets import load_products_safe
from settings import get_setting

catalog_router = Router()

# ===== КЭШ ПРОДУКТОВ =====
PRODUCTS_CACHE = []


async def load_products_cached():
    global PRODUCTS_CACHE

    if not PRODUCTS_CACHE:
        PRODUCTS_CACHE = await load_products_safe()

    return PRODUCTS_CACHE


# ===== /catalog (кнопка) =====
@catalog_router.message(lambda m: m.text == "🛍️ Каталог")
async def show_catalog(message: types.Message):
    products = await load_products_cached()

    # Получаем уникальные категории
    categories = sorted({p["category"] for p in products})

    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=c, callback_data=f"cat:{c}")
    kb.adjust(1)

    await message.answer("Выберите категорию:", reply_markup=kb.as_markup())


# ===== Выбор категории =====
@catalog_router.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(callback: types.CallbackQuery):
    _, category = callback.data.split(":", 1)

    products = await load_products_cached()
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


# ===== Открыть карточку товара =====
@catalog_router.callback_query(lambda c: c.data.startswith("prod:"))
async def product_card(callback: types.CallbackQuery):
    _, product_id = callback.data.split(":", 1)

    products = await load_products_cached()
    p = next((x for x in products if str(x["id"]) == product_id), None)

    if not p:
        return await callback.answer("Ошибка: товар не найден", show_alert=True)

    caption = f"<b>{p['name']}</b>\n\n{p['description']}"

    # ===== Если есть file_id (кеш Telegram) =====
    if p.get("file_id"):
        await callback.message.answer_photo(
            p["file_id"],
            caption=caption,
            reply_markup=_variants_keyboard(p)
        )
    # ===== Если фото — URL =====
    elif p.get("photo_url") and p["photo_url"].startswith("http"):
        msg = await callback.message.answer_photo(
            p["photo_url"],
            caption=caption,
            reply_markup=_variants_keyboard(p)
        )
        # сохраняем file_id для ускорения
        try:
            file_id = msg.photo[-1].file_id
            p["file_id"] = file_id
        except:
            pass

    # ===== Если фото нет =====
    else:
        await callback.message.answer(
            caption,
            reply_markup=_variants_keyboard(p)
        )

    await callback.answer()


# ===== Генератор клавиатуры вариантов =====
def _variants_keyboard(product):
    kb = InlineKeyboardBuilder()
    for v in product["variants"]:
        kb.button(
            text=v["label"],
            callback_data=f"addcart:{product['id']}:{v['id']}"
        )

    kb.adjust(1)
    return kb.as_markup()

