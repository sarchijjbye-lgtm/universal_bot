from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

# Инициализация бота и диспетчера Aiogram
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
