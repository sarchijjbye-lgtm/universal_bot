# app/utils/is_admin.py

from aiogram.types import Message, CallbackQuery
from app.core.config import config


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id == config.ADMIN_CHAT_ID


def admin_only(message: Message | CallbackQuery) -> bool:
    """
    Быстрая проверка прямо в хендлерах.
    Использование:
    
        if not admin_only(message):
            await message.answer("❌ Доступ запрещён")
            return
    """
    uid = message.from_user.id
    return uid == config.ADMIN_CHAT_ID
