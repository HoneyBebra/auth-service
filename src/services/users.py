from fastapi import Response

from src.core.config import settings
from src.exceptions.users import InvalidCredentials, UserAlreadyExists
from src.models.users import Users
from src.repositories.base.jwt_token import BaseJwtTokenRepository
from src.repositories.base.users import BaseUsersRepository
from src.schemas.v1.users import UserLoginSchema, UserRegisterSchema
from src.utils.encryption import encrypt_data, hash_password, hash_user_data, verify_password
from src.utils.jwt import create_token


class UsersService:
    def __init__(
        self,
        users_repository: BaseUsersRepository,
        jwt_token_repository: BaseJwtTokenRepository,
    ) -> None:
        self.users_repository = users_repository
        self.jwt_token_repository = jwt_token_repository

    async def create(self, user_data: UserRegisterSchema) -> Users:
        email_hash = hash_user_data(user_data.email) if user_data.email is not None else None
        encrypted_email = encrypt_data(user_data.email) if user_data.email is not None else None
        phone_number_hash = (
            hash_user_data(user_data.phone_number) if user_data.phone_number is not None else None
        )
        encrypted_phone_number = (
            encrypt_data(user_data.phone_number) if user_data.phone_number is not None else None
        )

        existing_user = await self.users_repository.find_existing_by_personal_hashes(
            email_hash=email_hash,
            phone_number_hash=phone_number_hash,
        )
        if existing_user is not None:
            if email_hash is not None and existing_user.email_hash == email_hash:
                raise UserAlreadyExists("email")
            raise UserAlreadyExists("phone_number")

        password_hash = hash_password(password=user_data.password)

        user = await self.users_repository.create(
            login=user_data.login,
            password_hash=password_hash,
            encrypted_email=encrypted_email,
            encrypted_phone_number=encrypted_phone_number,
            email_hash=email_hash,
            phone_number_hash=phone_number_hash,
        )
        return user

    async def authenticate(self, user_data: UserLoginSchema) -> Users:
        if user_data.email is None and user_data.phone_number is None:
            raise InvalidCredentials("email or phone number is required")

        email_hash = hash_user_data(user_data.email) if user_data.email is not None else None
        phone_number_hash = (
            hash_user_data(user_data.phone_number) if user_data.phone_number is not None else None
        )

        users = await self.users_repository.read(
            email_hash=email_hash,
            phone_number_hash=phone_number_hash,
        )

        if not users or not verify_password(user_data.password, users[0].password):
            raise InvalidCredentials

        return users[0]

    async def add_token_to_blacklist(
        self,
        token: str,
        expires_in: int,
    ) -> None:
        await self.jwt_token_repository.set_token_to_blacklist(
            token=token,
            expires_in=expires_in,
        )

    @staticmethod
    async def remove_tokens_from_response(response: Response) -> Response:
        response.delete_cookie(**settings.jwt.access_cookie_delete_settings)
        response.delete_cookie(**settings.jwt.refresh_cookie_delete_settings)

        return response

    @staticmethod
    async def add_tokens_to_response(
        user_id: str,
        response: Response,
    ) -> Response:
        access_token = await create_token(
            sub=user_id,
            token_type="access",
        )
        refresh_token = await create_token(
            sub=user_id,
            token_type="refresh",
        )

        response.set_cookie(
            value=access_token,
            **settings.jwt.access_cookie_set_settings,
        )
        response.set_cookie(
            value=refresh_token,
            **settings.jwt.refresh_cookie_set_settings,
        )

        return response
