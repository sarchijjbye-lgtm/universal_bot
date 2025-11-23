# app/middlewares/session.py

from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext


class SessionMiddleware(BaseMiddleware):
    """
    FSM middleware для корректного получения/создания состояния пользователя.
    Работает для всех типов апдейтов: message, callback_query.
    """

    def __init__(self, storage: MemoryStorage):
        super().__init__()
        self.storage = storage

    async def __call__(self, handler, event: Update, data: dict):
        user_id = None
        chat_id = None

        # Определяем контекст (user_id / chat_id)
        if event.message:
            user_id = event.message.from_user.id
            chat_id = event.message.chat.id
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            chat_id = event.callback_query.message.chat.id
        else:
            return await handler(event, data)

        # Создаём объект FSMContext (aiogram 3)
        data["state"] = FSMContext(
            storage=self.storage,
            key=f"{chat_id}:{user_id}"
        )

        return await handler(event, data)
