from abc import ABC, abstractmethod


class BaseRateLimitRepository(ABC):
    @abstractmethod
    async def lock(
            self,
            identifier_hash: str,
            operation: str,
            expires_in: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def is_exists(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def increment_counter(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
            expires_in_only_after_first_increment: int,
    ) -> int:
        """returns the final count"""
        raise NotImplementedError

    @abstractmethod
    async def delete(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_ttl(
            self,
            identifier_hash: str,
            kind: str,
            operation: str,
    ) -> int:
        raise NotImplementedError
