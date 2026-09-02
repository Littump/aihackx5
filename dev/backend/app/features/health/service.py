from psycopg import AsyncConnection

from app.features.health import database
from app.features.health.models import HealthStatus


async def check(conn: AsyncConnection) -> HealthStatus:
    database_ok = await database.ping(conn)
    return HealthStatus(status="ok", database="ok" if database_ok else "error")
