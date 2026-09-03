from datetime import UTC, datetime, timedelta
from decimal import Decimal

from psycopg import AsyncConnection

from app.game_rules import REFERRAL_MIN_FIRST_PURCHASE, REFERRAL_REWARDS

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
REFERRER_CREATED_AT = NOW - timedelta(days=90)
REFEREE_CREATED_AT = NOW - timedelta(days=30)
NEW_REWARD = REFERRAL_REWARDS["new"]
BELOW_THRESHOLD = Decimal(REFERRAL_MIN_FIRST_PURCHASE - 50)
AT_THRESHOLD = Decimal(REFERRAL_MIN_FIRST_PURCHASE)


def receipt_payload(
    user_id: int, store_id: int, purchased_at: datetime, paid_total: Decimal
) -> dict[str, object]:
    price = float(paid_total)
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at.isoformat(),
        "points_earned": 0,
        "points_spent": 0,
        "items": [
            {
                "product_name": "Товар",
                "category": "grocery",
                "qty": 1,
                "regular_price": price,
                "paid_price": price,
            }
        ],
    }


async def reward_ledger_rows(conn: AsyncConnection, *, user_id: int) -> list[tuple[str, int, int]]:
    cursor = await conn.execute(
        "SELECT kind, xp_delta, points_delta FROM reward_ledger "
        "WHERE user_id = %s ORDER BY created_at ASC, id ASC",
        (user_id,),
    )
    return [(row[0], row[1], row[2]) for row in await cursor.fetchall()]
