# middlewares/antiflood.py

import time
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable


class AntiFloodMiddleware(BaseMiddleware):
    """
    Блокирует флуд — одинаковые сообщения чаще, чем 1 раз в limit секунд.
    """

    def __init__(self, limit: float = 0.5):
        super().__init__()
        self.limit = limit
        self.last_message_time: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:

        user_id = event.from_user.id
        now = time.time()

        last_time = self.last_message_time.get(user_id, 0)

        if now - last_time < self.limit:
            # Игнорируем сообщение (не спамим в Telegram API)
            return

        self.last_message_time[user_id] = now

        return await handler(event, data)
