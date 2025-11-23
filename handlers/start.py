# app/handlers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart

from app.core.config import config
from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import categories_kb

router = Router()

# CatalogService будет внедрён в main.py
catalog_service: CatalogService = None


@router.message(CommandStart())
async def start_handler(message: types.Message):
    """Приветственное сообщение + кнопки категорий."""

    # Если после старта каталог ещё не загружен — загружаем
    if not catalog_service._cache:
        catalog_service.load()

    categories = catalog_service.get_categories()

    welcome = config.WELCOME_MESSAGE or "Добро пожаловать!"
    brand = config.BRAND_NAME or config.BRAND

    text = (
        f"<b>{brand}</b>\n\n"
        f"{welcome}\n\n"
        f"Выберите категорию:"
    )

    await message.answer(text, reply_markup=categories_kb(categories))
