# routers/debug_photos.py
from aiogram import Router, F, types

debug_photos_router = Router()

@debug_photos_router.message(F.photo)
async def get_file_id(message: types.Message):
    # Берём самое большое фото (последний элемент)
    photo = message.photo[-1]
    file_id = photo.file_id

    # Отправляем тебе в чат, чтобы было удобно копировать
    await message.answer(
        f"📸 Вот file_id для этой картинки:\n<code>{file_id}</code>",
        parse_mode="HTML"
    )

    # И продублируем в логи (на всякий случай)
    print(f"[PHOTO_FILE_ID] {file_id}")
