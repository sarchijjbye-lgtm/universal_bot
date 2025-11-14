# middlewares/stage.py

from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable


class StageMiddleware(BaseMiddleware):
    """
    Middleware для хранения шага оформления заказа в FSM-подобном стиле.
    Хранится в user_data, не требует FSM.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        user_id = event.from_user.id

        if "stage_storage" not in data:
            data["stage_storage"] = {}  # runtime storage

        stage_storage = data["stage_storage"]

        # Получаем текущий шаг
        stage = stage_storage.get(user_id, None)
        data["stage"] = stage

        # Функция изменения шага
        async def set_stage(new_stage: str | None):
            if new_stage is None:
                stage_storage.pop(user_id, None)
            else:
                stage_storage[user_id] = new_stage

        data["set_stage"] = set_stage

        return await handler(event, data)
