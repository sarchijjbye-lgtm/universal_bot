# main.py

from fastapi import FastAPI, Request
from aiogram.types import Update

from bot_init import bot, dp
from config import WEBHOOK_URL, WEBHOOK_PATH

app = FastAPI()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    update = Update(**(await req.json()))
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "running", "webhook": WEBHOOK_URL}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print(f"[WEBHOOK] Set to {WEBHOOK_URL}")
