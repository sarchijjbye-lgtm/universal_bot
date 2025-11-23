# app/middlewares/logging_mw.py

import logging
from aiogram import BaseMiddleware
from aiogram.types import Update


class LoggingMiddleware(BaseMiddleware):
    """
    Логирует все апдейты в консоль.
    Работает первым в цепочке middlewares.
    """

    async def __call__(self, handler, event: Update, data: dict):
        logging.info(f"[UPDATE] {event.model_dump(exclude_none=True)}")
        return await handler(event, data)
