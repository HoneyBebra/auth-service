from redis.asyncio import Redis

from src.core.config import settings
from src.repositories.base.rate_limit import BaseRateLimitRepository


class RateLimitRepository(BaseRateLimitRepository):
    def __init__(self, session: Redis) -> None:
        self.session = session

    async def lock(
            self,
            identifier_hash: str,
            operation: str,
            expires_in: int,
    ) -> None:
        key = self._rate_limit_key(
            identifier_hash=identifier_hash,
            operation=operation,
            kind="lock",
        )
        await self.session.setex(
            name=key,
            time=expires_in,
            value="none",
        )

    async def is_exists(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
    ) -> bool:
        key = self._rate_limit_key(
            identifier_hash=identifier_hash,
            operation=operation,
            kind=kind,
        )
        return bool(await self.session.exists(key))

    async def increment_counter(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
            expires_in_only_after_first_increment: int,
    ) -> int:
        """returns the final count"""

        key = self._rate_limit_key(
            identifier_hash=identifier_hash,
            operation=operation,
            kind=kind,
        )

        count = await self.session.incr(key)
        await self.session.expire(key, expires_in_only_after_first_increment, nx=True)
        return count

    async def delete(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
    ) -> None:
        key = self._rate_limit_key(
            identifier_hash=identifier_hash,
            operation=operation,
            kind=kind,
        )
        await self.session.delete(key)

    async def get_ttl(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
    ) -> int:
        """
        returns the Time To Live
        >= 0 - ttl (sec)
        -1 - the key without a ttl
        -2 - there is no this key
        """
        key = self._rate_limit_key(
            identifier_hash=identifier_hash,
            operation=operation,
            kind=kind,
        )
        return await self.session.ttl(key)

    @staticmethod
    def _rate_limit_key(
            identifier_hash: str,
            operation: str,
            kind: str,
    ) -> str:
        return (
            f"{settings.rate_limit.rate_limit_redis_prefix}:"
            f"{operation}:"
            f"{kind}:"
            f"{identifier_hash}"
        )
