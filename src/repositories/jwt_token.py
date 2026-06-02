from redis.asyncio import Redis

from src.repositories.base.jwt_token import BaseJwtTokenRepository


class JwtTokenRepository(BaseJwtTokenRepository):
    def __init__(self, session: Redis) -> None:
        self.session = session

    async def set_token_to_blacklist(self, token: str, expires_in: int) -> None:
        await self.session.setex(
            name=token,
            time=expires_in,
            value="none",
        )

    async def is_token_in_blacklist(self, token: str) -> bool:
        return bool(await self.session.exists(token))
