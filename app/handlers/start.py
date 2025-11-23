# app/handlers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart

from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import categories_kb
from app.utils.keyboards import global_menu_kb

router = Router()

# Сервис каталога внедряется из main.py
catalog_service: CatalogService = None


# ==========================================================
# Команда /start
# ==========================================================
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    categories = catalog_service.get_categories()

    text = (
        "<b>Добро пожаловать!</b>\n"
        "Выберите категорию ниже:"
    )

    await message.answer(
        text,
        reply_markup=global_menu_kb(categories)
    )


# ==========================================================
# Показ категорий (кнопка «Категории» в меню)
# ==========================================================
@router.callback_query(lambda c: c.data == "open_categories")
async def show_categories(callback: types.CallbackQuery):
    categories = catalog_service.get_categories()

    await callback.message.edit_text(
        "Выберите категорию:",
        reply_markup=global_menu_kb(categories)
    )
