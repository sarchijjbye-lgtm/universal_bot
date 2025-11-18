# routers/admin_router.py

from aiogram import Router, types
from aiogram.filters import Command
import os

from google_sheets import update_file_id, load_products_safe

admin_router = Router()

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

PHOTO_WAIT = {}   # {admin_id: product_id}


# ================================
#   ACCESS CHECK
# ================================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_CHAT_ID


# ================================
#   /photo <id>
# ================================

@admin_router.message(Command("photo"))
async def admin_photo_start(message: types.Message):

    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет доступа")

    parts = message.text.strip().split()

    if len(parts) != 2:
        return await message.answer("⚠️ Использование:\n/photo <id>")

    product_id = parts[1]

    # Проверяем, что товар существует
    products = load_products_safe()
    exists = any(p["id"] == product_id for p in products)

    if not exists:
        return await message.answer(f"❌ Товар с id <b>{product_id}</b> не найден")

    # Сохраняем ожидание
    PHOTO_WAIT[message.from_user.id] = product_id

    await message.answer(
        f"📸 Отправьте фотографию для товара <b>ID {product_id}</b>\n"
        f"Я сохраню file_id в Google Sheets."
    )


# ================================
#   Process photo
# ================================

@admin_router.message(lambda m: m.from_user.id in PHOTO_WAIT and m.photo)
async def admin_photo_received(message: types.Message):

    admin_id = message.from_user.id
    product_id = PHOTO_WAIT.get(admin_id)

    if not product_id:
        return

    # Берем самое большое фото
    file_id = message.photo[-1].file_id

    # Записываем в Sheets
    ok = update_file_id(product_id, file_id)

    if ok:
        await message.answer(
            f"✅ Фото успешно сохранено для товара ID <b>{product_id}</b>\n"
            f"file_id обновлён в Google Sheets."
        )
    else:
        await message.answer(
            f"❌ Ошибка: не удалось обновить Google Sheets для товара ID {product_id}"
        )

    PHOTO_WAIT.pop(admin_id, None)


# ================================
#   NON-PHOTO HANDLING
# ================================

@admin_router.message(lambda m: m.from_user.id in PHOTO_WAIT)
async def admin_expect_photo(message: types.Message):
    await message.answer("⚠️ Пожалуйста, отправьте фотографию файл *photo*, не текст.")
# routers/admin_router.py

from aiogram import Router, types
from aiogram.filters import Command
import os

from google_sheets import update_file_id, load_products_safe

admin_router = Router()

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

PHOTO_WAIT = {}   # {admin_id: product_id}


# ================================
#   ACCESS CHECK
# ================================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_CHAT_ID


# ================================
#   /photo <id>
# ================================

@admin_router.message(Command("photo"))
async def admin_photo_start(message: types.Message):

    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет доступа")

    parts = message.text.strip().split()

    if len(parts) != 2:
        return await message.answer("⚠️ Использование:\n/photo <id>")

    product_id = parts[1]

    # Проверяем, что товар существует
    products = load_products_safe()
    exists = any(p["id"] == product_id for p in products)

    if not exists:
        return await message.answer(f"❌ Товар с id <b>{product_id}</b> не найден")

    # Сохраняем ожидание
    PHOTO_WAIT[message.from_user.id] = product_id

    await message.answer(
        f"📸 Отправьте фотографию для товара <b>ID {product_id}</b>\n"
        f"Я сохраню file_id в Google Sheets."
    )


# ================================
#   Process photo
# ================================

@admin_router.message(lambda m: m.from_user.id in PHOTO_WAIT and m.photo)
async def admin_photo_received(message: types.Message):

    admin_id = message.from_user.id
    product_id = PHOTO_WAIT.get(admin_id)

    if not product_id:
        return

    # Берем самое большое фото
    file_id = message.photo[-1].file_id

    # Записываем в Sheets
    ok = update_file_id(product_id, file_id)

    if ok:
        await message.answer(
            f"✅ Фото успешно сохранено для товара ID <b>{product_id}</b>\n"
            f"file_id обновлён в Google Sheets."
        )
    else:
        await message.answer(
            f"❌ Ошибка: не удалось обновить Google Sheets для товара ID {product_id}"
        )

    PHOTO_WAIT.pop(admin_id, None)


# ================================
#   NON-PHOTO HANDLING
# ================================

@admin_router.message(lambda m: m.from_user.id in PHOTO_WAIT)
async def admin_expect_photo(message: types.Message):
    await message.answer("⚠️ Пожалуйста, отправьте фотографию файл *photo*, не текст.")
