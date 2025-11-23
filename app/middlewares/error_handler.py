# app/middlewares/error_handler.py

import logging
from aiogram import BaseMiddleware
from aiogram.types import Update


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Глобальный перехват ошибок. Не даёт боту упасть.
    """

    async def __call__(self, handler, event: Update, data: dict):
        try:
            return await handler(event, data)

        except Exception as e:
            logging.error(f"[ERROR] {e}", exc_info=True)

            try:
                if hasattr(event, "message") and event.message:
                    await event.message.answer("⚠️ Ошибка. Попробуйте позже.")
                elif hasattr(event, "callback_query") and event.callback_query:
                    await event.callback_query.answer("Произошла ошибка.", show_alert=True)
            except:
                pass

            return None
