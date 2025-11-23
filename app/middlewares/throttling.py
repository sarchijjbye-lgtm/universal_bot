# app/middlewares/throttling.py

import time
from aiogram import BaseMiddleware
from aiogram.types import Update


class ThrottlingMiddleware(BaseMiddleware):
    """
    Простой антифлуд.
    Ограничивает частоту запросов от одного пользователя.
    """

    def __init__(self, rate_limit: float = 0.5):
        super().__init__()
        self.rate_limit = rate_limit
        self.last_time = {}

    async def __call__(self, handler, event: Update, data: dict):

        user_id = None

        if event.message:
            user_id = event.message.from_user.id
        elif event.callback_query:
            user_id = event.callback_query.from_user.id

        if user_id:
            now = time.time()
            last = self.last_time.get(user_id, 0)

            if now - last < self.rate_limit:
                # тихо игнорируем
                return

            self.last_time[user_id] = now

        return await handler(event, data)
