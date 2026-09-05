import json
import logging
from typing import Optional, Any
import redis.asyncio as aioredis
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

redis_pool: Optional[aioredis.Redis] = None
_redis_tested: bool = False
_redis_available: bool = False

async def init_redis():
    global redis_pool, _redis_tested, _redis_available
    _redis_tested = True
    try:
        redis_pool = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=0.5
        )
        await redis_pool.ping()
        _redis_available = True
        logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. System will fallback to PostgreSQL.")
        redis_pool = None
        _redis_available = False

async def get_redis() -> Optional[aioredis.Redis]:
    global redis_pool, _redis_tested
    if not _redis_tested:
        await init_redis()
    return redis_pool

async def cache_get(key: str) -> Optional[str]:
    try:
        client = await get_redis()
        if client:
            return await client.get(key)
    except Exception as e:
        logger.warning(f"Redis cache_get error for key '{key}': {e}")
    return None

async def cache_set(key: str, value: Any, ttl_seconds: int = 300):
    try:
        client = await get_redis()
        if client:
            val_str = json.dumps(value) if not isinstance(value, str) else value
            await client.set(key, val_str, ex=ttl_seconds)
    except Exception as e:
        logger.warning(f"Redis cache_set error for key '{key}': {e}")

async def cache_delete(key: str):
    try:
        client = await get_redis()
        if client:
            await client.delete(key)
    except Exception as e:
        logger.warning(f"Redis cache_delete error for key '{key}': {e}")

async def cache_delete_pattern(pattern: str):
    try:
        client = await get_redis()
        if client:
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis cache_delete_pattern error for pattern '{pattern}': {e}")

