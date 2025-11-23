# app/handlers/catalog.py

from aiogram import Router, types
from aiogram.types import CallbackQuery

from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import products_kb, global_menu_kb

router = Router()

catalog_service: CatalogService = None


# ==========================================================
# Выбор категории
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("cat:"))
async def category_selected(callback: CallbackQuery):
    category = callback.data.split("cat:")[1]
    products = catalog_service.get_products_by_category(category)

    if not products:
        await callback.answer("Пока нет товаров.")
        return

    await callback.message.edit_text(
        f"<b>{category}</b>\nВыберите товар:",
        reply_markup=products_kb(products)
    )


# ==========================================================
# Назад к списку категорий
# ==========================================================
@router.callback_query(lambda c: c.data == "back:catalog")
async def back_to_catalog(callback: CallbackQuery):
    categories = catalog_service.get_categories()

    await callback.message.edit_text(
        "Выберите категорию:",
        reply_markup=global_menu_kb(categories)
    )
