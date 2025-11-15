from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

USER_STAGES = {}   # user_id → "stage_name"


class StageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Dict[str, Any], Any], Awaitable[Any]],
        event,
        data
    ):
        user_id = None

        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user_id = event.message.from_user.id

        # методы для работы с stage
        async def set_stage(value: str | None):
            if value is None:
                USER_STAGES.pop(user_id, None)
            else:
                USER_STAGES[user_id] = value

        def get_stage():
            return USER_STAGES.get(user_id)

        # прокидываем в handlers
        data["set_stage"] = set_stage
        data["stage"] = get_stage()

        return await handler(event, data)
