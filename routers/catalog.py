# routers/catalog.py

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google_sheets import load_products_safe

catalog_router = Router()


async def load_products_fresh():
    return load_products_safe()


# ===== Helpers =====

def is_parent(p: dict) -> bool:
    return p["parent_id"] == ""  # parent row: parent_id = ""


def get_children(products, parent_id):
    return [p for p in products if p["parent_id"] == parent_id and p["price"] > 0]


# ===== UX: MAIN CATALOG =====

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
        kb.button(text=f"📂 {c}", callback_data=f"cat:{c}")

    kb.adjust(1)
    await msg.answer(
        "<b>🛍 Каталог</b>\nВыберите категорию:",
        reply_markup=kb.as_markup()
    )


# ===== UX: CATEGORY SCREEN =====

@catalog_router.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(cb: types.CallbackQuery):
    _, category = cb.data.split(":", 1)

    products = await load_products_fresh()
    parents = [
        p for p in products
        if is_parent(p) and p["category"] == category
    ]

    kb = InlineKeyboardBuilder()
    for p in parents:
        kb.button(text=p["name"], callback_data=f"prod:{p['id']}")

    # Навигация
    kb.button(text="⬅️ Назад", callback_data="catalog_back")
    kb.button(text="🛒 Корзина", callback_data="cart_open")
    kb.adjust(1)

    await cb.message.edit_text(
        f"<b>{category}</b>\nВыберите товар:",
        reply_markup=kb.as_markup()
    )
    await cb.answer()


@catalog_router.callback_query(lambda c: c.data == "catalog_back")
async def back_to_catalog(cb: types.CallbackQuery):
    await show_catalog(cb.message)
    await cb.answer()


# ===== UX: PRODUCT CARD =====

@catalog_router.callback_query(lambda c: c.data.startswith("prod:"))
async def product_card(cb: types.CallbackQuery):
    _, parent_id = cb.data.split(":", 1)

    products = await load_products_fresh()
    parent = next((x for x in products if x["id"] == parent_id), None)

    if not parent:
        return await cb.answer("Товар не найден", show_alert=True)

    children = get_children(products, parent_id)

    # ======= Клавиатура =======
    kb = InlineKeyboardBuilder()

    # --- Товар без вариаций ---
    if not children:
        kb.button(
            text=f"🛒 Добавить — {parent['price']}₽",
            callback_data=f"addcart:{parent_id}:{parent_id}"
        )
    else:
        # --- Вариации ---
        for v in children:
            kb.button(
                text=f"{v['variant_label']} — {v['price']}₽",
                callback_data=f"addcart:{parent_id}:{v['id']}"
            )

    # Навигация
    kb.button(text="⬅️ Назад к товарам", callback_data=f"cat:{parent['category']}")
    kb.button(text="🛒 Корзина", callback_data="cart_open")
    kb.adjust(1)

    # ======= Единая карточка товара =======
    caption = (
        f"<b>{parent['name']}</b>\n"
        f"{parent['description']}\n"
    )

    # Вместо отправки нового сообщения → редактируем текущее
    try:
        await cb.message.delete()  # удаляем прошлую кнопку
    except:
        pass

    if parent["file_id"]:
        await cb.message.answer_photo(
            parent["file_id"],
            caption,
            reply_markup=kb.as_markup()
        )
    elif parent["photo_url"]:
        msg = await cb.message.answer_photo(
            parent["photo_url"],
            caption,
            reply_markup=kb.as_markup()
        )

        try:
            parent["file_id"] = msg.photo[-1].file_id
        except:
            pass
    else:
        await cb.message.answer(caption, reply_markup=kb.as_markup())

    await cb.answer()
