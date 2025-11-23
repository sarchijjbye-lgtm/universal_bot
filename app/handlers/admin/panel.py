# app/handlers/admin/panel.py

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from app.core.config import config
from app.utils.is_admin import is_admin
from app.services.sheets.catalog import CatalogService

router = Router()

# Внедряется из main.py
catalog_service: CatalogService = None


# ==========================================================
# Команда /admin — вход в панель администратора
# ==========================================================
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет доступа к админ-панели.")

    text = (
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите действие:"
    )

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="📦 Список товаров",
                    callback_data="admin_products"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="📸 Прикрепить фото к товару",
                    callback_data="admin_photo"
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=kb)


# ==========================================================
# Список товаров (только parent)
# ==========================================================
@router.callback_query(lambda c: c.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа")

    # Загружаем все parent товары
    products = catalog_service.all_products()

    text = "📦 <b>Список товаров (parent)</b>\n\n"

    for p in products:
        text += f"• <b>{p.id}</b> — {p.name}\n"

    await callback.message.edit_text(text)


# ==========================================================
# Переход в photo upload
# ==========================================================
@router.callback_query(lambda c: c.data == "admin_photo")
async def admin_photo_mode(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа")

    text = (
        "📸 <b>Режим загрузки фото</b>\n\n"
        "Отправьте боту фотографию товара,\n"
        "затем отправьте ID товара (parent)."
    )

    await callback.message.edit_text(text)

    # Передаём работу в photo_upload.py
