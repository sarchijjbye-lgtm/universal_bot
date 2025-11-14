# middlewares/error_handler.py

import logging
from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable


class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Middleware перехватывает ошибки, логирует и не дает боту упасть.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)

        except Exception as e:
            logging.error(f"[ERROR MIDDLEWARE] {type(e).__name__}: {e}")
            return  # не падаем
