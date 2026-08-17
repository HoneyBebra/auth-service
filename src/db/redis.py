from redis.asyncio import Redis

from src.core.config import settings

_redis_client: Redis | None = None


async def init_redis() -> Redis:
    global _redis_client
    _redis_client = Redis(**settings.redis.client_settings(settings.app.backoff_retries_count))
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def get_redis_client() -> Redis:
    if _redis_client is None:
        raise RuntimeError(
            "Redis client is not initialized. "
            "Did you forget to call init_redis() in lifespan?"
        )
    return _redis_client
