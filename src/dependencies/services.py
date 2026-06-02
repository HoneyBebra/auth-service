from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import get_session
from src.db.redis import get_redis_client
from src.repositories.jwt_token import JwtTokenRepository
from src.repositories.users import UsersRepository
from src.services.jwt import TokenValidator
from src.services.users import UsersService


def get_users_repository(
    session: AsyncSession = Depends(get_session),
) -> UsersRepository:
    return UsersRepository(session=session)


def get_jwt_token_repository(
    redis_session: Redis = Depends(get_redis_client),
) -> JwtTokenRepository:
    return JwtTokenRepository(session=redis_session)


def get_users_service(
    users_repository: UsersRepository = Depends(get_users_repository),
    jwt_token_repository: JwtTokenRepository = Depends(get_jwt_token_repository),
) -> UsersService:
    return UsersService(
        users_repository=users_repository,
        jwt_token_repository=jwt_token_repository,
    )


def get_token_validator(
    jwt_token_repository: JwtTokenRepository = Depends(get_jwt_token_repository)
) -> TokenValidator:
    return TokenValidator(jwt_token_repository=jwt_token_repository)
