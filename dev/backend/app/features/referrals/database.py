from datetime import datetime
from decimal import Decimal

from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.referrals.models import RefereeKind, ReferralRow, ReferralStatus

REFERRAL_COLUMNS = (
    "id, referrer_user_id, referee_user_id, referee_kind, status, first_purchase_at, "
    "second_purchase_at, fraud_score, fraud_reasons, referrer_reward_points, "
    "referee_reward_points, created_at, decided_at"
)
REFERRAL_GET_BY_ID = f"SELECT {REFERRAL_COLUMNS} FROM referrals WHERE id = %(referral_id)s"
REFERRAL_GET_BY_REFEREE = (
    f"SELECT {REFERRAL_COLUMNS} FROM referrals WHERE referee_user_id = %(referee_user_id)s"
)
REFERRAL_LIST_BY_REFERRER = (
    f"SELECT {REFERRAL_COLUMNS} FROM referrals WHERE referrer_user_id = %(referrer_user_id)s "
    "ORDER BY created_at ASC, id ASC"
)
REFERRAL_INSERT = (
    "INSERT INTO referrals (referrer_user_id, referee_user_id, referee_kind, status, "
    "first_purchase_at, second_purchase_at, fraud_score, fraud_reasons, "
    "referrer_reward_points, referee_reward_points, created_at, decided_at) "
    "VALUES (%(referrer_user_id)s, %(referee_user_id)s, %(referee_kind)s, %(status)s, "
    "%(first_purchase_at)s, %(second_purchase_at)s, %(fraud_score)s, %(fraud_reasons)s, "
    "%(referrer_reward_points)s, %(referee_reward_points)s, COALESCE(%(created_at)s, now()), "
    "%(decided_at)s) "
    f"RETURNING {REFERRAL_COLUMNS}"
)
REFERRAL_MARK_FIRST_PURCHASE = (
    "UPDATE referrals SET status = 'first_purchase', "
    "first_purchase_at = %(first_purchase_at)s, "
    "referee_reward_points = %(referee_reward_points)s "
    "WHERE id = %(referral_id)s "
    f"RETURNING {REFERRAL_COLUMNS}"
)
REFERRAL_MARK_QUALIFIED = (
    "UPDATE referrals SET status = 'qualified', second_purchase_at = %(second_purchase_at)s "
    "WHERE id = %(referral_id)s "
    f"RETURNING {REFERRAL_COLUMNS}"
)
REFERRAL_MARK_DECISION = (
    "UPDATE referrals SET status = %(status)s, decided_at = %(decided_at)s, "
    "fraud_score = %(fraud_score)s, fraud_reasons = %(fraud_reasons)s, "
    "referrer_reward_points = %(referrer_reward_points)s "
    "WHERE id = %(referral_id)s "
    f"RETURNING {REFERRAL_COLUMNS}"
)
REFERRAL_COUNT_REWARDED_IN_RANGE = (
    "SELECT count(*) FROM referrals WHERE referrer_user_id = %(referrer_user_id)s "
    "AND status = 'rewarded' AND decided_at >= %(start)s AND decided_at < %(end)s"
)


async def get_referral_by_id(conn: AsyncConnection, *, referral_id: int) -> ReferralRow | None:
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_GET_BY_ID, {"referral_id": referral_id})
        return await cur.fetchone()


async def get_referral_by_referee(
    conn: AsyncConnection, *, referee_user_id: int
) -> ReferralRow | None:
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_GET_BY_REFEREE, {"referee_user_id": referee_user_id})
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


async def insert_referral(
    conn: AsyncConnection,
    *,
    referrer_user_id: int,
    referee_user_id: int,
    referee_kind: RefereeKind,
    status: ReferralStatus,
) -> ReferralRow:
    params: dict[str, object] = {
        "referrer_user_id": referrer_user_id,
        "referee_user_id": referee_user_id,
        "referee_kind": referee_kind,
        "status": status,
        "first_purchase_at": None,
        "second_purchase_at": None,
        "fraud_score": None,
        "fraud_reasons": Jsonb([]),
        "referrer_reward_points": 0,
        "referee_reward_points": 0,
        "created_at": None,
        "decided_at": None,
    }
    return await insert_referral_row(conn, params)


async def mark_first_purchase(
    conn: AsyncConnection,
    *,
    referral_id: int,
    first_purchase_at: datetime,
    referee_reward_points: int,
) -> ReferralRow:
    params = {
        "referral_id": referral_id,
        "first_purchase_at": first_purchase_at,
        "referee_reward_points": referee_reward_points,
    }
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_MARK_FIRST_PURCHASE, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def mark_qualified(
    conn: AsyncConnection, *, referral_id: int, second_purchase_at: datetime
) -> ReferralRow:
    params = {"referral_id": referral_id, "second_purchase_at": second_purchase_at}
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_MARK_QUALIFIED, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def mark_decision(
    conn: AsyncConnection,
    *,
    referral_id: int,
    status: ReferralStatus,
    decided_at: datetime,
    fraud_score: Decimal,
    fraud_reasons: list[str],
    referrer_reward_points: int,
) -> ReferralRow:
    params = {
        "referral_id": referral_id,
        "status": status,
        "decided_at": decided_at,
        "fraud_score": fraud_score,
        "fraud_reasons": Jsonb(fraud_reasons),
        "referrer_reward_points": referrer_reward_points,
    }
    async with conn.cursor(row_factory=class_row(ReferralRow)) as cur:
        await cur.execute(REFERRAL_MARK_DECISION, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def count_rewarded_in_range(
    conn: AsyncConnection, *, referrer_user_id: int, start: datetime, end: datetime
) -> int:
    params = {"referrer_user_id": referrer_user_id, "start": start, "end": end}
    async with conn.cursor() as cur:
        await cur.execute(REFERRAL_COUNT_REWARDED_IN_RANGE, params)
        row = await cur.fetchone()
        assert row is not None
        return int(row[0])
