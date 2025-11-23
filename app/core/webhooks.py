# app/core/webhooks.py

import asyncio
from fastapi import APIRouter, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from app.core.config import config
from app.core.bot import bot, dp

router = APIRouter()


async def register_routers(dp: Dispatcher):
    """Импорт и подключение всех роутеров проекта."""
    from app.handlers.start import router as start_router
    from app.handlers.catalog import router as catalog_router
    from app.handlers.product import router as product_router
    from app.handlers.cart import router as cart_router
    from app.handlers.order import router as order_router
    from app.handlers.admin.photo_upload import router as admin_photo_router
    from app.handlers.admin.panel import router as admin_panel_router

    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(product_router)
    dp.include_router(cart_router)
    dp.include_router(order_router)
    dp.include_router(admin_photo_router)
    dp.include_router(admin_panel_router)


@router.get("/health")
async def health():
    """Проверка работоспособности Render/FastAPI."""
    return {"status": "ok"}


@router.post("/webhook")
async def webhook_handler(request: Request):
    """Получение апдейтов от Telegram."""
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}


# ==========================================================
#  FIXED WEBHOOK SETUP (RENDER + TELEGRAM COMPATIBLE)
# ==========================================================
async def setup_webhook(bot: Bot):
    """
    Устанавливает webhook с задержкой и retry.
    Render иногда поднимает DNS 5–15 сек.
    Telegram требует, чтобы хост уже резолвился.
    """

    webhook_url = f"{config.BOT_URL}/webhook"

    # ждём, чтобы DNS Render успел активироваться
    await asyncio.sleep(3)

    try:
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        print(f"[WEBHOOK] Set to {webhook_url}")
        return webhook_url

    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}, retrying in 5 seconds...")
        await asyncio.sleep(5)

        # повторная попытка
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )

        print(f"[WEBHOOK] Retried and set → {webhook_url}")
        return webhook_url
