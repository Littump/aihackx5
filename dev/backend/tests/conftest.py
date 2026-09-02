import sys
from collections.abc import AsyncIterator, Callable, Iterator
from datetime import datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from app.core import clock
from app.core.config import settings
from app.core.db import create_pool
from app.main import create_app
from migrate import migrate

TEST_DSN = settings.test_database_url


@pytest.fixture(scope="session", autouse=True)
async def migrated_db() -> None:
    await migrate(TEST_DSN)


@pytest.fixture
async def pool() -> AsyncIterator[AsyncConnectionPool]:
    pool = create_pool(TEST_DSN)
    await pool.open()
    try:
        yield pool
    finally:
        await pool.close()


@pytest.fixture
async def conn(pool: AsyncConnectionPool) -> AsyncIterator[AsyncConnection]:
    async with pool.connection() as connection:
        await connection.set_autocommit(True)
        yield connection


@pytest.fixture
async def client(pool: AsyncConnectionPool) -> AsyncIterator[AsyncClient]:
    app = create_app(TEST_DSN)
    app.state.pool = pool
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture(autouse=True)
async def clean_tables(pool: AsyncConnectionPool) -> AsyncIterator[None]:
    yield
    async with pool.connection() as connection:
        await connection.set_autocommit(True)
        cur = await connection.execute(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename <> 'schema_migrations'"
        )
        tables = [row[0] for row in await cur.fetchall()]
        if tables:
            joined = ", ".join(f'"{name}"' for name in tables)
            await connection.execute(f"TRUNCATE {joined} RESTART IDENTITY CASCADE")


@pytest.fixture
def freeze_time() -> Iterator[Callable[[datetime], None]]:
    yield clock.set_override
    clock.set_override(None)
