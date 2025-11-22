# middlewares/stage.py

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable


class StageMiddleware(BaseMiddleware):
    """
    Безопасный middleware, который НЕ конфликтует с FSM.
    Полностью убирает ошибку "state = None".
    Хранит кастомный stage отдельно и никак не влияет на FSMContext.
    """

    # runtime-хранилище
    stage_storage: Dict[int, str] = {}

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:

        # Определяем ID
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        # Если объект не поддерживается — пропускаем
        if user_id is None:
            return await handler(event, data)

        # Получаем текущий кастомный stage
        data["custom_stage"] = self.stage_storage.get(user_id)

        # Создаём безопасную set_stage
        async def set_stage(new_stage: str | None):
            if new_stage is None:
                self.stage_storage.pop(user_id, None)
            else:
                self.stage_storage[user_id] = new_stage

        data["set_custom_stage"] = set_stage

        # 🌿 ВАЖНО — не трогаем и не переопределяем FSM
        # data["state"] остаётся нетронутым

        return await handler(event, data)
