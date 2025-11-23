# app/middlewares/session.py

from aiogram import BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Callable, Dict, Any, Awaitable


class SessionMiddleware(BaseMiddleware):
    """
    Обёртка вокруг MemoryStorage.
    Aiogram 3.x ХРАНИТ state внутри Dispatcher сам.
    Мы просто добавляем удобный доступ к FSM в data.
    """

    def __init__(self, storage: MemoryStorage = None):
        super().__init__()
        self.storage = storage or MemoryStorage()

    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any]
    ) -> Any:

        # FSM обрабатывается Aiogram автоматически
        # Мы просто кладём ссылку на storage (если нужно)
        data["storage"] = self.storage

        return await handler(event, data)
