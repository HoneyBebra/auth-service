# ruff: noqa: I001

from contextlib import asynccontextmanager
from typing import AsyncIterator

import grpc
import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse

from src.api.v1.users import router as users_router
from src.core.config import settings
from src.core.logger import LOGGING
from src.db.postgres import engine
from src.db.redis import close_redis, get_redis_client, init_redis
from src.gRPC.protos import user_pb2_grpc
from src.gRPC.server import GrpcServer
from src.repositories.jwt_token import JwtTokenRepository
from src.services.jwt import TokenValidator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa
    await init_redis()

    jwt_token_repository = JwtTokenRepository(session=get_redis_client())
    token_validator = TokenValidator(jwt_token_repository=jwt_token_repository)

    grpc_server = grpc.aio.server()
    user_pb2_grpc.add_UserServicer_to_server(
        GrpcServer(token_validator=token_validator),
        grpc_server,
    )
    grpc_server.add_insecure_port(f"[::]:{settings.app.grpc_port}")

    await grpc_server.start()
    try:
        yield
    finally:
        await grpc_server.stop(grace=5)
        await close_redis()
        await engine.dispose()


app = FastAPI(
    title=settings.app.name,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=f"{settings.app.api_v1_prefix}/openapi",
    openapi_url=f"{settings.app.api_v1_prefix}/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

router = APIRouter(prefix=settings.app.api_v1_prefix)
router.include_router(users_router)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=LOGGING,
        log_level="debug",
    )
