from psycopg import AsyncConnection

from app.core.errors import AppError
from app.features.domovoy import service as domovoy_service
from app.features.users import database
from app.features.users.models import StoreRow, UserRow, UserSummary
from app.features.users.pseudonyms import generate_unique_pseudonym
from app.game_rules import level_for_xp


async def list_users(conn: AsyncConnection, *, limit: int) -> list[UserSummary]:
    basics = await database.list_users(conn, limit=limit)
    if not basics:
        return []
    levels = await domovoy_service.get_levels(conn, user_ids=[basic.id for basic in basics])
    level_by_user = {row.user_id: row.level for row in levels}
    default_level = level_for_xp(0)
    return [
        UserSummary(
            id=basic.id,
            pseudonym=basic.pseudonym,
            segment=basic.segment,
            level=level_by_user.get(basic.id, default_level),
        )
        for basic in basics
    ]


async def get_user(conn: AsyncConnection, user_id: int) -> UserRow:
    user = await database.get_user_by_id(conn, user_id=user_id)
    if user is None:
        raise AppError("user_not_found", "пользователь не найден", 404)
    return user


async def get_store(conn: AsyncConnection, store_id: int) -> StoreRow:
    store = await database.get_store_by_id(conn, store_id=store_id)
    if store is None:
        raise AppError("store_not_found", "магазин не найден", 404)
    return store


async def generate_pseudonym(conn: AsyncConnection) -> str:
    async def is_taken(candidate: str) -> bool:
        return await database.pseudonym_exists(conn, pseudonym=candidate)

    return await generate_unique_pseudonym(is_taken)
