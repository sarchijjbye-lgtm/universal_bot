# routers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from settings import get_setting

start_router = Router()


@start_router.message(CommandStart())
async def start(message: types.Message):

    welcome = get_setting("welcome_message")

    if not welcome:
        welcome = (
            "Привет! 👋\n"
            "Это магазин-бот натуральных сыродавленных масел.\n"
            "Выберите действие:"
        )

    text = f"{welcome}\n\n👇 Выберите действие:"

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🛍 Каталог")],
            [types.KeyboardButton(text="🧬 Подбор масла")],
            [types.KeyboardButton(text="🛒 Корзина")]
        ],
        resize_keyboard=True
    )

    await message.answer(text, reply_markup=kb)


# ——— Универсальный хендлер для «Подбор масла» ———
@start_router.message(lambda m: m.text and "подбор" in m.text.lower())
async def route_to_wizard(message: types.Message):
    """
    Этот хендлер просто передаёт пользователя дальше в oil_wizard.
    Нужно, чтобы не зависеть от точного текста кнопки.
    """
    from routers.oil_wizard import start_quiz
    await start_quiz(message, None)
