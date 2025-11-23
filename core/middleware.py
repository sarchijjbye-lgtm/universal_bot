# app/core/middleware.py

from aiogram import Dispatcher

from app.middlewares.logging_mw import LoggingMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.session import SessionMiddleware
from app.middlewares.error_handler import ErrorHandlingMiddleware


def setup_middlewares(dp: Dispatcher):
    """
    Подключает все middlewares проекта в правильном порядке.
    Вызывается один раз при запуске приложения.
    """

    # 1. Логирование — всегда первым
    dp.update.middleware(LoggingMiddleware())

    # 2. Обработка ошибок — перехватывает исключения
    dp.errors.middleware(ErrorHandlingMiddleware())

    # 3. FSM Session (хранилище контекста пользователя)
    dp.update.middleware(SessionMiddleware())

    # 4. Антифлуд
    dp.update.middleware(ThrottlingMiddleware(rate_limit=0.5))
