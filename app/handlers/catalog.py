from aiogram import Router
from aiogram.types import CallbackQuery, Message

from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import categories_kb, products_kb

router = Router()
catalog_service: CatalogService = None


# ==========================================================
# Функция для показа категорий
# ==========================================================
async def send_categories(message: Message):
    categories = catalog_service.get_categories()

    await message.answer(
        "Выберите категорию:",
        reply_markup=categories_kb(categories)
    )


# ==========================================================
# Показ товаров из категории
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("cat:"))
async def category_selected(callback: CallbackQuery):
    category = callback.data.split("cat:")[1]
    products = catalog_service.get_products_by_category(category)

    if not products:
        await callback.answer("В категории пока нет товаров.")
        return

    await callback.message.edit_text(
        f"<b>{category}</b>\nВыберите товар:",
        reply_markup=products_kb(products)
    )


# ==========================================================
# Вернуться к списку категорий
# ==========================================================
@router.callback_query(lambda c: c.data == "back:catalog")
async def back_to_catalog(callback: CallbackQuery):
    await send_categories(callback.message)
