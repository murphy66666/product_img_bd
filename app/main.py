from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.cache.redis import close_redis_client
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.responses import UTF8JSONResponse
from app.db.mysql import mysql_sessions
from app.services.generation_queue import start_generation_queue, stop_generation_queue


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await start_generation_queue()
    yield
    await stop_generation_queue()
    await close_redis_client()
    await mysql_sessions.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        default_response_class=UTF8JSONResponse,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.mount("/storage", StaticFiles(directory="storage", check_dir=False), name="storage")
    return app


app = create_app()
