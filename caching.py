# caching.py — modern Redis async

import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# создаём одно соединение
redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)


async def cache_get(key: str):
    try:
        return await redis_client.get(key)
    except Exception as e:
        print("[REDIS ERROR GET]", e)
        return None


async def cache_set(key: str, value: str, ttl: int = 3600):
    try:
        await redis_client.set(key, value, ex=ttl)
    except Exception as e:
        print("[REDIS ERROR SET]", e)
        return None


async def cache_delete(key: str):
    try:
        await redis_client.delete(key)
    except Exception as e:
        print("[REDIS ERROR DEL]", e)
        return None
