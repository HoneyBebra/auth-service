from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry

from src.core.config import settings
from src.core.config.postgres import sqlalchemy_backoff_decorator_settings
from src.models.users import Users
from src.repositories.base.users import BaseUsersRepository


class UsersRepository(BaseUsersRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @retry(**sqlalchemy_backoff_decorator_settings(settings.app.backoff_retries_count))
    async def create(
        self,
        login: str,
        password_hash: str,
        encrypted_email: str | None = None,
        encrypted_phone_number: str | None = None,
        email_hash: str | None = None,
        phone_number_hash: str | None = None,
    ) -> Users:
        user = Users()

        user.login = login
        user.password = password_hash
        user.encrypted_email = encrypted_email
        user.encrypted_phone_number = encrypted_phone_number
        user.email_hash = email_hash
        user.phone_number_hash = phone_number_hash

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    @retry(**sqlalchemy_backoff_decorator_settings(settings.app.backoff_retries_count))
    async def read(
        self,
        login: str | None = None,
        phone_number_hash: str | None = None,
        email_hash: str | None = None,
    ) -> list[Users]:
        query = select(Users)

        if login is not None:
            query = query.where(Users.login == login)
        if phone_number_hash is not None:
            query = query.where(Users.phone_number_hash == phone_number_hash)
        if email_hash is not None:
            query = query.where(Users.email_hash == email_hash)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    @retry(**sqlalchemy_backoff_decorator_settings(settings.app.backoff_retries_count))
    async def find_existing_by_personal_hashes(
        self,
        email_hash: str | None = None,
        phone_number_hash: str | None = None,
    ) -> Users | None:
        if email_hash is None and phone_number_hash is None:
            return None

        conditions = []
        if email_hash is not None:
            conditions.append(Users.email_hash == email_hash)
        if phone_number_hash is not None:
            conditions.append(Users.phone_number_hash == phone_number_hash)

        query = select(Users).where(or_(*conditions))
        result = await self.session.execute(query)
        return result.scalars().first()

    @retry(**sqlalchemy_backoff_decorator_settings(settings.app.backoff_retries_count))
    async def update(  # type: ignore[empty-body]
        self,
        user_id: UUID,
        login: str | None = None,
        password: str | None = None,
        phone_number: str | None = None,
        email: str | None = None,
    ) -> Users: ...

    @retry(**sqlalchemy_backoff_decorator_settings(settings.app.backoff_retries_count))
    async def delete(self, user_id: UUID) -> None:  # type: ignore[empty-body]
        ...
