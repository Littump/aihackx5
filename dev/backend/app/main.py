from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import create_pool
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.features.health.router import router as health_router
from app.features.users.router import router as users_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = create_pool(app.state.database_url)
    await pool.open()
    app.state.pool = pool
    try:
        yield
    finally:
        await pool.close()


def create_app(database_url: str | None = None) -> FastAPI:
    configure_logging()
    app = FastAPI(title="Domovoy API", version="0.1.0", lifespan=lifespan)
    app.state.database_url = database_url or settings.database_url
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(users_router, prefix=API_PREFIX)
    return app


app = create_app()
