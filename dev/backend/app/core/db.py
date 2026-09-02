from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool


def create_pool(dsn: str) -> AsyncConnectionPool:
    return AsyncConnectionPool(dsn, min_size=1, max_size=10, open=False)


async def get_conn(request: Request) -> AsyncIterator[AsyncConnection]:
    pool: AsyncConnectionPool = request.app.state.pool
    async with pool.connection() as conn, conn.transaction():
        yield conn


Conn = Annotated[AsyncConnection, Depends(get_conn)]
