from psycopg import AsyncConnection

from app.features.domovoy import database
from app.features.domovoy.models import DomovoyLevelRow


async def get_levels(conn: AsyncConnection, *, user_ids: list[int]) -> list[DomovoyLevelRow]:
    if not user_ids:
        return []
    return await database.list_levels(conn, user_ids=user_ids)
