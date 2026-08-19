import hashlib

from redis.asyncio import Redis
from redis.exceptions import RedisError

from aiimage.config import Settings


def _key(email: str) -> str:
    digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    return f"aiimage:auth:failures:{digest}"


async def login_is_limited(email: str, settings: Settings) -> bool:
    redis = Redis.from_url(settings.redis_url)
    try:
        value = await redis.get(_key(email))
        return int(value or 0) >= settings.login_max_attempts
    except RedisError:
        return False
    finally:
        await redis.aclose()


async def record_login_failure(email: str, settings: Settings) -> None:
    redis = Redis.from_url(settings.redis_url)
    try:
        key = _key(email)
        async with redis.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, settings.login_window_seconds)
            await pipeline.execute()
    except RedisError:
        return
    finally:
        await redis.aclose()


async def clear_login_failures(email: str, settings: Settings) -> None:
    redis = Redis.from_url(settings.redis_url)
    try:
        await redis.delete(_key(email))
    except RedisError:
        return
    finally:
        await redis.aclose()
