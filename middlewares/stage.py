# middlewares/stage.py

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable


class StageMiddleware(BaseMiddleware):
    """
    Универсальный middleware для хранения шага (stage)
    подходит для Message и CallbackQuery.
    """

    # Runtime-хранилище (на сервере)
    stage_storage: Dict[int, str] = {}

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:

        # Универсально получаем user_id
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return await handler(event, data)

        # Текущий stage
        stage = self.stage_storage.get(user_id)
        data["stage"] = stage

        # Функция изменения stage
        async def set_stage(new_stage: str | None):
            if new_stage is None:
                self.stage_storage.pop(user_id, None)
            else:
                self.stage_storage[user_id] = new_stage

        data["set_stage"] = set_stage

        return await handler(event, data)
