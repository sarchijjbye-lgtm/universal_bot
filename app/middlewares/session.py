# app/middlewares/session.py

from aiogram import BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update


class SessionMiddleware(BaseMiddleware):
    """
    FSM-хранилище в памяти.
    """

    storage = MemoryStorage()

    async def __call__(self, handler, event: Update, data: dict):
        user_id = None
        chat_id = None

        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id

        if hasattr(event, "chat") and event.chat:
            chat_id = event.chat.id

        data["state"] = self.storage.create_context(
            bot=data["bot"],
            user_id=user_id,
            chat_id=chat_id,
        )

        return await handler(event, data)
