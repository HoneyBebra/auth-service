from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.rate_limit import RateLimitService
from src.db.postgres import get_session
from src.db.redis import get_redis_client
from src.repositories.jwt_token import JwtTokenRepository
from src.repositories.rate_limit import RateLimitRepository
from src.repositories.users import UsersRepository
from src.services.jwt import JwtService
from src.services.users import UsersService


def _get_users_repository(
    session: AsyncSession = Depends(get_session),
) -> UsersRepository:
    return UsersRepository(session=session)


def _get_jwt_token_repository(
    redis_session: Redis = Depends(get_redis_client),
) -> JwtTokenRepository:
    return JwtTokenRepository(session=redis_session)


def _get_rate_limit_repository(
    redis_session: Redis = Depends(get_redis_client),
) -> RateLimitRepository:
    return RateLimitRepository(session=redis_session)


def get_users_service(
    users_repository: UsersRepository = Depends(_get_users_repository),
    jwt_token_repository: JwtTokenRepository = Depends(_get_jwt_token_repository),
) -> UsersService:
    return UsersService(
        users_repository=users_repository,
        jwt_token_repository=jwt_token_repository,
    )


def get_jwt_service(
    jwt_token_repository: JwtTokenRepository = Depends(_get_jwt_token_repository)
) -> JwtService:
    return JwtService(jwt_token_repository=jwt_token_repository)


def get_rate_limit_service(
        rate_limit_repository: RateLimitRepository = Depends(_get_rate_limit_repository),
) -> RateLimitService:
    return RateLimitService(rate_limit_repository=rate_limit_repository)
