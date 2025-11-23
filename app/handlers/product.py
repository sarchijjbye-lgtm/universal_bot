# app/handlers/product.py

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import product_kb
from app.utils.formatting import product_card, variants_text

router = Router()

# Внедряется из main.py
catalog_service: CatalogService = None


# ==========================================================
# Helper — отправка карточки товара
# ==========================================================
async def send_product_card(message: Message, product):
    text = (
        product_card(product.name, product.description)
        + "\n"
        + variants_text(product.variants)
    )

    # Фото → новое сообщение
    if product.file_id:
        await message.answer_photo(
            product.file_id,
            caption=text,
            reply_markup=product_kb(product)
        )
    else:
        await message.answer(
            text,
            reply_markup=product_kb(product)
        )


# ==========================================================
# Открытие карточки товара
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("product:"))
async def product_selected(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = catalog_service.get_product(product_id)

    if not product:
        await callback.answer("Товар не найден.")
        return

    await callback.message.delete()  # чистим
    await send_product_card(callback.message, product)


# ==========================================================
# Назад к товару
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("back:product:"))
async def back_to_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[2])
    product = catalog_service.get_product(product_id)

    if not product:
        await callback.answer("Товар не найден.")
        return

    await callback.message.delete()
    await send_product_card(callback.message, product)
