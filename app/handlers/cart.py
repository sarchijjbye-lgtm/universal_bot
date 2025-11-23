# app/handlers/cart.py

from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.cart import CartService
from app.services.sheets.catalog import CatalogService
from app.utils.keyboards import cart_kb
from app.utils.formatting import cart_text, total_text

router = Router()

# Внедряется из main.py
catalog_service: CatalogService = None
cart_service: CartService = None


# ==========================================================
# Добавление варианта товара в корзину
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("variant:"))
async def add_variant_to_cart(callback: CallbackQuery, state: FSMContext):
    variant_id = int(callback.data.split(":")[1])

    added = await cart_service.add(state, variant_id)

    if not added:
        await callback.answer("Ошибка: товар не найден.")
        return

    await callback.answer("Добавлено в корзину 🧺")


# ==========================================================
# Открыть корзину (через текст)
# ==========================================================
@router.message(lambda m: m.text and m.text.lower() in ("корзина", "🧺 корзина"))
async def open_cart_text(message: types.Message, state: FSMContext):
    items = await cart_service.list(state)
    text = cart_text(items)

    await message.answer(
        text,
        reply_markup=cart_kb(items)
    )


# ==========================================================
# Открыть корзину (через кнопку)
# ==========================================================
@router.callback_query(lambda c: c.data == "cart")
async def open_cart_callback(callback: CallbackQuery, state: FSMContext):
    items = await cart_service.list(state)

    await callback.message.edit_text(
        cart_text(items),
        reply_markup=cart_kb(items)
    )


# ==========================================================
# Удаление варианта из корзины
# ==========================================================
@router.callback_query(lambda c: c.data.startswith("del:"))
async def delete_item(callback: CallbackQuery, state: FSMContext):
    variant_id = int(callback.data.split(":")[1])

    removed = await cart_service.remove(state, variant_id)

    if not removed:
        await callback.answer("Этот товар уже удалён.")
        return

    items = await cart_service.list(state)

    await callback.message.edit_text(
        cart_text(items),
        reply_markup=cart_kb(items)
    )


# ==========================================================
# Очистка корзины
# ==========================================================
@router.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, state: FSMContext):
    await cart_service.clear(state)

    text = "<i>Корзина пуста.</i>"

    await callback.message.edit_text(
        text,
        reply_markup=cart_kb([])
    )


# ==========================================================
# Переход к оформлению заказа
# ==========================================================
@router.callback_query(lambda c: c.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    items = await cart_service.list(state)
    total = await cart_service.total(state)

    if not items:
        await callback.answer("Корзина пуста!")
        return

    checkout_text = (
        cart_text(items)
        + total_text(total)
        + "\n\nВведите ваше <b>имя</b>."
    )

    await callback.message.edit_text(checkout_text)

    # Переход к следующему шагу FSM
    from app.handlers.order import OrderState
    await state.set_state(OrderState.waiting_for_name)
