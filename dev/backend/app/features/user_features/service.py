from datetime import timedelta

from psycopg import AsyncConnection

from app.core.clock import now as clock_now
from app.features.receipts import service as receipts_service
from app.features.user_features import calc, database
from app.features.user_features.models import UserFeaturesRow
from app.features.users import service as users_service
from app.game_rules import FEATURES_WINDOW_WEEKS, REALIZED_SAVINGS_WINDOW_DAYS


async def get(conn: AsyncConnection, user_id: int) -> UserFeaturesRow:
    existing = await database.get_user_features_by_user_id(conn, user_id=user_id)
    if existing is not None:
        return existing
    return await recompute(conn, user_id)


async def recompute(conn: AsyncConnection, user_id: int) -> UserFeaturesRow:
    moment = clock_now()
    window_start = moment - timedelta(weeks=FEATURES_WINDOW_WEEKS)
    savings_start = moment - timedelta(days=REALIZED_SAVINGS_WINDOW_DAYS)
    receipts = await receipts_service.list_counted_receipts_with_items(
        conn, user_id=user_id, since=min(window_start, savings_start)
    )
    window_receipts = [r for r in receipts if r.purchased_at >= window_start]
    savings_receipts = [r for r in receipts if r.purchased_at >= savings_start]
    store_chains = await users_service.get_stores_by_ids(
        conn, store_ids=sorted({r.store_id for r in window_receipts})
    )
    features = calc.compute(
        window_receipts,
        savings_receipts,
        now=moment,
        window_weeks=FEATURES_WINDOW_WEEKS,
        store_chains=store_chains,
    )
    return await database.upsert_user_features(conn, user_id, features)
