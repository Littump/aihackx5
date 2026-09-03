from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.users.models import StoreRow, UserBasicRow, UserRow

USER_LIST_SELECT = "SELECT id, pseudonym, segment FROM users ORDER BY id ASC LIMIT %(limit)s"
USER_GET_BY_ID = (
    "SELECT id, pseudonym, segment, favourite_store_id, referral_code, "
    "referred_by_user_id, device_fingerprint, social_propensity, created_at "
    "FROM users WHERE id = %(user_id)s"
)
PSEUDONYM_EXISTS = "SELECT EXISTS(SELECT 1 FROM users WHERE pseudonym = %(pseudonym)s)"
STORE_GET_BY_ID = "SELECT id, name, chain, district, city FROM stores WHERE id = %(store_id)s"
STORE_GET_DEFAULT = "SELECT id, name, chain, district, city FROM stores ORDER BY id LIMIT 1"
STORE_LIST_BY_IDS = (
    "SELECT id, name, chain, district, city FROM stores WHERE id = ANY(%(store_ids)s)"
)
USER_LIST_BY_IDS = (
    "SELECT id, pseudonym, segment, favourite_store_id, referral_code, "
    "referred_by_user_id, device_fingerprint, social_propensity, created_at "
    "FROM users WHERE id = ANY(%(user_ids)s)"
)
STORE_INSERT = (
    "INSERT INTO stores (name, chain, district, city) "
    "VALUES (%(name)s, %(chain)s, %(district)s, %(city)s) "
    "RETURNING id, name, chain, district, city"
)
USER_INSERT = (
    "INSERT INTO users (pseudonym, segment, favourite_store_id, referral_code, "
    "referred_by_user_id, device_fingerprint, social_propensity) "
    "VALUES (%(pseudonym)s, %(segment)s, %(favourite_store_id)s, %(referral_code)s, "
    "%(referred_by_user_id)s, %(device_fingerprint)s, %(social_propensity)s) "
    "RETURNING id, pseudonym, segment, favourite_store_id, referral_code, "
    "referred_by_user_id, device_fingerprint, social_propensity, created_at"
)


async def insert_store(conn: AsyncConnection, params: dict[str, object]) -> StoreRow:
    async with conn.cursor(row_factory=class_row(StoreRow)) as cur:
        await cur.execute(STORE_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def insert_user(conn: AsyncConnection, params: dict[str, object]) -> UserRow:
    async with conn.cursor(row_factory=class_row(UserRow)) as cur:
        await cur.execute(USER_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def list_users(conn: AsyncConnection, *, limit: int) -> list[UserBasicRow]:
    async with conn.cursor(row_factory=class_row(UserBasicRow)) as cur:
        await cur.execute(USER_LIST_SELECT, {"limit": limit})
        return await cur.fetchall()


async def get_user_by_id(conn: AsyncConnection, *, user_id: int) -> UserRow | None:
    async with conn.cursor(row_factory=class_row(UserRow)) as cur:
        await cur.execute(USER_GET_BY_ID, {"user_id": user_id})
        return await cur.fetchone()


async def list_users_by_ids(conn: AsyncConnection, *, user_ids: list[int]) -> list[UserRow]:
    async with conn.cursor(row_factory=class_row(UserRow)) as cur:
        await cur.execute(USER_LIST_BY_IDS, {"user_ids": user_ids})
        return await cur.fetchall()


async def pseudonym_exists(conn: AsyncConnection, *, pseudonym: str) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(PSEUDONYM_EXISTS, {"pseudonym": pseudonym})
        row = await cur.fetchone()
        return bool(row is not None and row[0])


async def get_store_by_id(conn: AsyncConnection, *, store_id: int) -> StoreRow | None:
    async with conn.cursor(row_factory=class_row(StoreRow)) as cur:
        await cur.execute(STORE_GET_BY_ID, {"store_id": store_id})
        return await cur.fetchone()


async def get_default_store(conn: AsyncConnection) -> StoreRow | None:
    async with conn.cursor(row_factory=class_row(StoreRow)) as cur:
        await cur.execute(STORE_GET_DEFAULT)
        return await cur.fetchone()


async def list_stores_by_ids(conn: AsyncConnection, *, store_ids: list[int]) -> list[StoreRow]:
    async with conn.cursor(row_factory=class_row(StoreRow)) as cur:
        await cur.execute(STORE_LIST_BY_IDS, {"store_ids": store_ids})
        return await cur.fetchall()
