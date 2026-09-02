from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.users.models import StoreRow, UserRow

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
