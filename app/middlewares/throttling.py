# app/middlewares/throttling.py

import time
from aiogram import BaseMiddleware
from aiogram.types import Update


class ThrottlingMiddleware(BaseMiddleware):
    """
    Антифлуд. Ограничивает количество запросов от пользователя.
    """

    def __init__(self, rate_limit: float = 0.5):
        super().__init__()
        self.rate_limit = rate_limit
        self._last_time = {}

    async def __call__(self, handler, event: Update, data: dict):
        user_id = None

        # Выясняем user_id из разных типов событий
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id

        if user_id:
            now = time.time()
            last = self._last_time.get(user_id)

            if last and now - last < self.rate_limit:
                return  # просто игнорируем сообщение

            self._last_time[user_id] = now

        return await handler(event, data)
