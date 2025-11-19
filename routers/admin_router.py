# routers/admin_router.py

from aiogram import Router, types
import os

from google_sheets import update_file_id, load_products_safe

admin_router = Router()

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# Временное хранилище:
# admin_id → file_id
PHOTO_BUFFER = {}    # {admin_id: file_id}
WAIT_ID = {}         # {admin_id: True}


# =====================================================
#   ACCESS CHECK
# =====================================================

def is_admin(uid: int):
    return uid == ADMIN_CHAT_ID


# =====================================================
#   STEP 1 — ADMIN SENDS PHOTO
# =====================================================

@admin_router.message(lambda m: m.from_user.id == ADMIN_CHAT_ID and m.photo)
async def admin_photo_received(message: types.Message):

    file_id = message.photo[-1].file_id
    admin_id = message.from_user.id

    # сохраняем file_id
    PHOTO_BUFFER[admin_id] = file_id
    WAIT_ID[admin_id] = True  # ждём id товара

    await message.answer(
        "📸 Фото получено.\n"
        "Теперь отправьте <b>ID товара</b>, чтобы прикрепить фото.\n\n"
        "Например: <code>17</code>"
    )


# =====================================================
#   STEP 2 — ADMIN SENDS PRODUCT ID
# =====================================================

@admin_router.message(lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text and m.from_user.id in WAIT_ID)
async def admin_process_product_id(message: types.Message):

    admin_id = message.from_user.id

    product_id = message.text.strip()
    file_id = PHOTO_BUFFER.get(admin_id)

    if not file_id:
        return await message.answer("❌ Ошибка: фото не найдено. Отправьте фото заново.")

    # Проверяем, что товар существует
    products = load_products_safe()
    prod = next((p for p in products if p["id"] == product_id), None)

    if not prod:
        return await message.answer(f"❌ Товар с ID <b>{product_id}</b> не найден.")

    # Пытаемся записать в таблицу
    ok = update_file_id(product_id, file_id)

    if ok:
        await message.answer(
            f"✅ Фото успешно прикреплено к товару:\n"
            f"<b>{prod['name']}</b>\n"
            f"ID: <code>{product_id}</code>"
        )
    else:
        await message.answer(
            f"❌ Ошибка обновления Google Sheets для ID {product_id}"
        )

    # очищаем состояние
    PHOTO_BUFFER.pop(admin_id, None)
    WAIT_ID.pop(admin_id, None)


# =====================================================
#   NOT PHOTO — REMINDER
# =====================================================

@admin_router.message(lambda m: m.from_user.id == ADMIN_CHAT_ID and m.from_user.id not in WAIT_ID)
async def admin_wrong_flow(message: types.Message):
    await message.answer(
        "Чтобы прикрепить фото к товару:\n"
        "1️⃣ Отправьте фото\n"
        "2️⃣ Затем отправьте ID товара"
    )
