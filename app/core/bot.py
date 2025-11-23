# app/core/bot.py

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.core.config import config


def create_bot() -> Bot:
    """Создание экземпляра бота с корректным parse_mode."""
    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )


def create_dispatcher() -> Dispatcher:
    """Создание экземпляра диспетчера."""
    return Dispatcher()


# Singleton-объекты, которые будут использоваться по всему проекту
bot = create_bot()
dp = create_dispatcher()
