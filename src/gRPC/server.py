import grpc

from src.exceptions.jwt import (
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
    TokenRevokedError,
    TokenWrongTypeError,
)
from src.gRPC.protos import user_pb2, user_pb2_grpc
from src.services.jwt import TokenValidator


class GrpcServer(user_pb2_grpc.UserServicer):  # type: ignore[name-defined]
    def __init__(self, token_validator: TokenValidator) -> None:
        super().__init__()
        self._token_validator = token_validator

    async def GetUserInfoByToken(  # noqa: N802
        self,
        request: user_pb2.GetUserInfoByTokenRequest,  # type: ignore[name-defined]
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.GetUserInfoByTokenResponse:  # type: ignore[name-defined]
        try:
            user_data, _ = await self._token_validator.validate(
                raw_token=request.access_token,
                expected_type="access",
            )
        except (TokenMissingError, TokenExpiredError, TokenInvalidError) as e:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(e.message)
            return user_pb2.GetUserInfoByTokenResponse()  # type: ignore[name-defined]
        except (TokenRevokedError, TokenWrongTypeError) as e:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(e.message)
            return user_pb2.GetUserInfoByTokenResponse()  # type: ignore[name-defined]

        return user_pb2.GetUserInfoByTokenResponse(id=str(user_data.sub))  # type: ignore[name-defined]
