from aiogram import Router
from aiogram.types import CallbackQuery

from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import product_kb
from app.utils.formatting import product_card, variants_text

router = Router()

catalog_service: CatalogService = None


# ==========================================================
# Показ товара
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("product:"))
async def product_selected(callback: CallbackQuery):
    product_id = int(callback.data.split("product:")[1])
    product = catalog_service.get_product(product_id)

    if not product:
        await callback.answer("Товар не найден")
        return

    # Форматируем цену (без копеек)
    for variant in product.variants:
        variant["price"] = int(float(variant["price"]))

    text = (
        product_card(product.name, product.description)
        + "\n"
        + variants_text(product.variants)
    )

    await callback.message.delete()

    if product.file_id:
        await callback.message.answer_photo(
            product.file_id,
            caption=text,
            reply_markup=product_kb(product_id, product.variants)
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=product_kb(product_id, product.variants)
        )


# ==========================================================
# Возврат к категории
# ==========================================================
@router.callback_query(lambda c: c.data == "catalog_back")
async def back_to_catalog(callback: CallbackQuery):
    from app.handlers.catalog import send_categories

    await callback.message.delete()
    await send_categories(callback.message)
