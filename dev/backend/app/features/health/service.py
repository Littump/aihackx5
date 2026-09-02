from psycopg import AsyncConnection

from app.features.health import database


async def check(conn: AsyncConnection) -> dict[str, str]:
    database_ok = await database.ping(conn)
    return {"status": "ok", "database": "ok" if database_ok else "error"}
