from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.referrals.models import ReferralRow

REFERRAL_COLUMNS = (
    "id, referrer_user_id, referee_user_id, referee_kind, status, first_purchase_at, "
    "second_purchase_at, fraud_score, fraud_reasons, referrer_reward_points, "
    "referee_reward_points, created_at, decided_at"
)
REFERRAL_GET_BY_ID = f"SELECT {REFERRAL_COLUMNS} FROM referrals WHERE id = %(referral_id)s"
REFERRAL_LIST_BY_REFERRER = (
    f"SELECT {REFERRAL_COLUMNS} FROM referrals WHERE referrer_user_id = %(referrer_user_id)s "
    "ORDER BY created_at ASC, id ASC"
)
REFERRAL_INSERT = (
    "INSERT INTO referrals (referrer_user_id, referee_user_id, referee_kind, status, "
    "first_purchase_at, second_purchase_at, fraud_score, fraud_reasons, "
    "referrer_reward_points, referee_reward_points, created_at) "
    "VALUES (%(referrer_user_id)s, %(referee_user_id)s, %(referee_kind)s, %(status)s, "
    "%(first_purchase_at)s, %(second_purchase_at)s, %(fraud_score)s, %(fraud_reasons)s, "
    "%(referrer_reward_points)s, %(referee_reward_points)s, COALESCE(%(created_at)s, now())) "
    f"RETURNING {REFERRAL_COLUMNS}"
)


async def get_referral_by_id(conn: AsyncConnection, *, referral_id: int) -> ReferralRow | None:
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_GET_BY_ID, {"referral_id": referral_id})
        return await cur.fetchone()


async def list_by_referrer(conn: AsyncConnection, *, referrer_user_id: int) -> list[ReferralRow]:
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_LIST_BY_REFERRER, {"referrer_user_id": referrer_user_id})
        return await cur.fetchall()


async def insert_referral_row(conn: AsyncConnection, params: dict[str, object]) -> ReferralRow:
    # raw-параметры нужны только tests/factories.make_referral для гибких фикстур
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row
