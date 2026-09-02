from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.user_features.models import UserFeaturesRow

USER_FEATURES_INSERT = (
    "INSERT INTO user_features (user_id, window_weeks, frequency_per_week, recency_days, "
    "avg_basket, promo_sensitivity, cadence_days, category_affinity, weekday_pattern, "
    "realized_savings_30d, favourite_store_id, cross_chain_share) "
    "VALUES (%(user_id)s, %(window_weeks)s, %(frequency_per_week)s, %(recency_days)s, "
    "%(avg_basket)s, %(promo_sensitivity)s, %(cadence_days)s, %(category_affinity)s, "
    "%(weekday_pattern)s, %(realized_savings_30d)s, %(favourite_store_id)s, "
    "%(cross_chain_share)s) "
    "RETURNING user_id, computed_at, window_weeks, frequency_per_week, recency_days, "
    "avg_basket, promo_sensitivity, cadence_days, category_affinity, weekday_pattern, "
    "realized_savings_30d, favourite_store_id, cross_chain_share"
)


async def insert_user_features(conn: AsyncConnection, params: dict[str, object]) -> UserFeaturesRow:
    async with conn.cursor(row_factory=class_row(UserFeaturesRow)) as cur:
        await cur.execute(USER_FEATURES_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row
