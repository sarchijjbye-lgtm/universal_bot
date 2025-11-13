from aiogram import Router, types
from aiogram.filters import Command
from utils.sheets import load_products

catalog_router = Router()


def get_products():
    return load_products()


@catalog_router.message(Command("catalog"))
async def show_catalog(message: types.Message):
    products = get_products()

    if not products:
        await message.answer("Каталог пуст.")
        return

    text = "🌿 *Каталог масел:*\n\n"
    for p in products:
        text += f"• <b>{p['name']}</b> — {p['base_price']} ₽\n"

    await message.answer(text)
