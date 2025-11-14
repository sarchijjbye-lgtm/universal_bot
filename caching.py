# caching.py

import aioredis
from config import REDIS_URL

redis_client = aioredis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

async def cache_set(key, value, ttl=3600):
    await redis_client.set(key, value, ex=ttl)

async def cache_get(key):
    return await redis_client.get(key)

async def cache_delete(key):
    return await redis_client.delete(key)
