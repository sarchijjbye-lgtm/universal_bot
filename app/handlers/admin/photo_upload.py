# app/handlers/admin/photo_upload.py

from aiogram import Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.utils.is_admin import is_admin
from app.services.photos import PhotoManager
from app.services.sheets.catalog import CatalogService

router = Router()

# Внедряется из main.py
photo_manager: PhotoManager = None
catalog_service: CatalogService = None


# ==========================================================
# FSM для загрузки фото
# ==========================================================
class PhotoUploadState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_product_id = State()


# ==========================================================
# Вход в режим загрузки фото (после кнопки в админ-панели)
# ==========================================================
@router.callback_query(lambda c: c.data == "admin_photo")
async def enter_photo_mode(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа")

    await state.set_state(PhotoUploadState.waiting_for_photo)

    await callback.message.edit_text(
        "📸 <b>Загрузка фото товара</b>\n\n"
        "Отправьте фотографию товара.\n"
        "После этого бот попросит ID товара."
    )


# ==========================================================
# Шаг 1 — принимаем фото
# ==========================================================
@router.message(PhotoUploadState.waiting_for_photo)
async def receive_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if not message.photo:
        return await message.answer("Пожалуйста, отправьте изображение.")

    file_id = message.photo[-1].file_id

    # сохраняем временно в FSM
    await state.update_data(file_id=file_id)

    await message.answer(
        "Фото принято! Теперь отправьте ID товара (parent_id), "
        "к которому хотите прикрепить фото."
    )

    await state.set_state(PhotoUploadState.waiting_for_product_id)


# ==========================================================
# Шаг 2 — принимаем ID товара
# ==========================================================
@router.message(PhotoUploadState.waiting_for_product_id)
async def receive_product_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        product_id = int(message.text.strip())
    except ValueError:
        return await message.answer("Введите корректный числовой ID товара.")

    data = await state.get_data()
    file_id = data.get("file_id")

    if not file_id:
        await state.clear()
        return await message.answer("Ошибка: file_id потерян, начните заново.")

    # Сохраняем file_id в Sheets
    success = photo_manager.save_file_id(product_id, file_id)

    if not success:
        return await message.answer("❌ Не удалось сохранить фото. Проверьте ID товара.")

    await state.clear()
    await message.answer("✅ Фото успешно прикреплено к товару!")

    # Перезагрузим каталог, чтобы фото применилось
    catalog_service.load()
