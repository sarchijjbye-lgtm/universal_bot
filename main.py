from fastapi import FastAPI, Request
from aiogram.types import Update

from bot_init import bot, dp
from config import WEBHOOK_URL, WEBHOOK_PATH

# ===== CREATE FASTAPI APP =====
app = FastAPI()


# ===== TELEGRAM WEBHOOK HANDLER =====
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update(**data)

    # Обрабатываем update
    await dp.feed_update(bot, update)

    return {"ok": True}


# ===== ROOT CHECK =====
@app.get("/")
def root():
    return {"status": "running", "webhook": WEBHOOK_URL}


# ===== STARTUP: SET WEBHOOK =====
@app.on_event("startup")
async def on_startup():
    try:
        await bot.set_webhook(WEBHOOK_URL)
        print(f"[WEBHOOK] Set to {WEBHOOK_URL}")
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
