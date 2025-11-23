# app/handlers/product.py

from aiogram import Router, types
from aiogram.types import CallbackQuery

from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import variants_kb, products_kb
from app.utils.formatting import product_card, variants_text

router = Router()

# Сервис каталога внедряется из main.py
catalog_service: CatalogService = None


# ==========================================================
# Обработка выбора товара
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("product:"))
async def product_selected(callback: CallbackQuery):
    product_id = int(callback.data.split("product:")[1])
    product = catalog_service.get_product(product_id)

    if not product:
        await callback.answer("Товар не найден")
        return

    # Формируем текст
    text = (
        product_card(product.name, product.description)
        + "\n"
        + variants_text(product.variants)
    )

    # Если есть фото — отправляем как фото, иначе текстом
    if product.file_id:
        await callback.message.delete()
        await callback.message.answer_photo(
            product.file_id,
            caption=text,
            reply_markup=variants_kb(product_id, product.variants)
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=variants_kb(product_id, product.variants)
        )


# ==========================================================
# Кнопка «Назад» к товару
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("back:product:"))
async def back_to_product(callback: CallbackQuery):
    product_id = int(callback.data.split("back:product:")[1])
    product = catalog_service.get_product(product_id)

    if not product:
        await callback.answer("Товар не найден")
        return

    text = (
        product_card(product.name, product.description)
        + "\n"
        + variants_text(product.variants)
    )

    if product.file_id:
        await callback.message.delete()
        await callback.message.answer_photo(
            product.file_id,
            caption=text,
            reply_markup=variants_kb(product_id, product.variants)
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=variants_kb(product_id, product.variants)
        )
