# app/core/middleware.py

from aiogram import Dispatcher

from app.middlewares.error_handler import ErrorHandlingMiddleware
from app.middlewares.logging_mw import LoggingMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.session import SessionMiddleware


def setup_middlewares(dp: Dispatcher):

    # 1. Логирование — всегда первым
    dp.update.middleware(LoggingMiddleware())

    # 2. Ошибки — вторыми
    dp.errors.middleware(ErrorHandlingMiddleware())

    # 3. FSM/Session
    dp.update.middleware(SessionMiddleware())

    # 4. Антифлуд
    dp.update.middleware(ThrottlingMiddleware(rate_limit=0.3))
