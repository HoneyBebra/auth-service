from fastapi import Depends
from redis.asyncio import Redis

from src.db.redis import get_redis_client
from src.repositories.rate_limit import RateLimitRepository
from src.services.rate_limit import RateLimitService


def get_rate_limit_repository(
        redis_session: Redis = Depends(get_redis_client),
) -> RateLimitRepository:
    return RateLimitRepository(redis_session)


def get_rate_limit_service(
        rate_limit_repository: RateLimitRepository = Depends(get_rate_limit_repository),
) -> RateLimitService:
    return RateLimitService(rate_limit_repository)
