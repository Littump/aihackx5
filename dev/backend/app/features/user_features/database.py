from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.user_features.models import UserFeaturesCalc, UserFeaturesRow

USER_FEATURES_COLUMNS = (
    "user_id, computed_at, window_weeks, frequency_per_week, recency_days, "
    "avg_basket, promo_sensitivity, cadence_days, category_affinity, weekday_pattern, "
    "realized_savings_30d, favourite_store_id, cross_chain_share"
)
USER_FEATURES_INSERT = (
    "INSERT INTO user_features (user_id, window_weeks, frequency_per_week, recency_days, "
    "avg_basket, promo_sensitivity, cadence_days, category_affinity, weekday_pattern, "
    "realized_savings_30d, favourite_store_id, cross_chain_share) "
    "VALUES (%(user_id)s, %(window_weeks)s, %(frequency_per_week)s, %(recency_days)s, "
    "%(avg_basket)s, %(promo_sensitivity)s, %(cadence_days)s, %(category_affinity)s, "
    "%(weekday_pattern)s, %(realized_savings_30d)s, %(favourite_store_id)s, "
    "%(cross_chain_share)s) "
    f"RETURNING {USER_FEATURES_COLUMNS}"
)
USER_FEATURES_UPSERT = (
    "INSERT INTO user_features (user_id, window_weeks, frequency_per_week, recency_days, "
    "avg_basket, promo_sensitivity, cadence_days, category_affinity, weekday_pattern, "
    "realized_savings_30d, favourite_store_id, cross_chain_share) "
    "VALUES (%(user_id)s, %(window_weeks)s, %(frequency_per_week)s, %(recency_days)s, "
    "%(avg_basket)s, %(promo_sensitivity)s, %(cadence_days)s, %(category_affinity)s, "
    "%(weekday_pattern)s, %(realized_savings_30d)s, %(favourite_store_id)s, "
    "%(cross_chain_share)s) "
    "ON CONFLICT (user_id) DO UPDATE SET "
    "computed_at = now(), window_weeks = EXCLUDED.window_weeks, "
    "frequency_per_week = EXCLUDED.frequency_per_week, recency_days = EXCLUDED.recency_days, "
    "avg_basket = EXCLUDED.avg_basket, promo_sensitivity = EXCLUDED.promo_sensitivity, "
    "cadence_days = EXCLUDED.cadence_days, category_affinity = EXCLUDED.category_affinity, "
    "weekday_pattern = EXCLUDED.weekday_pattern, "
    "realized_savings_30d = EXCLUDED.realized_savings_30d, "
    "favourite_store_id = EXCLUDED.favourite_store_id, "
    "cross_chain_share = EXCLUDED.cross_chain_share "
    f"RETURNING {USER_FEATURES_COLUMNS}"
)
USER_FEATURES_GET_BY_USER_ID = (
    f"SELECT {USER_FEATURES_COLUMNS} FROM user_features WHERE user_id = %(user_id)s"
)


async def insert_user_features(conn: AsyncConnection, params: dict[str, object]) -> UserFeaturesRow:
    async with conn.cursor(row_factory=class_row(UserFeaturesRow)) as cur:
        await cur.execute(USER_FEATURES_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def upsert_user_features(
    conn: AsyncConnection, user_id: int, features: UserFeaturesCalc
) -> UserFeaturesRow:
    params = _to_upsert_params(user_id, features)
    async with conn.cursor(row_factory=class_row(UserFeaturesRow)) as cur:
        await cur.execute(USER_FEATURES_UPSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


def _to_upsert_params(user_id: int, features: UserFeaturesCalc) -> dict[str, object]:
    return {
        "user_id": user_id,
        "window_weeks": features.window_weeks,
        "frequency_per_week": features.frequency_per_week,
        "recency_days": features.recency_days,
        "avg_basket": features.avg_basket,
        "promo_sensitivity": features.promo_sensitivity,
        "cadence_days": features.cadence_days,
        "category_affinity": Jsonb(
            {
                name: affinity.model_dump(mode="json")
                for name, affinity in features.category_affinity.items()
            }
        ),
        "weekday_pattern": Jsonb(features.weekday_pattern),
        "realized_savings_30d": features.realized_savings_30d,
        "favourite_store_id": features.favourite_store_id,
        "cross_chain_share": features.cross_chain_share,
    }


async def get_user_features_by_user_id(
    conn: AsyncConnection, *, user_id: int
) -> UserFeaturesRow | None:
    async with conn.cursor(row_factory=class_row(UserFeaturesRow)) as cur:
        await cur.execute(USER_FEATURES_GET_BY_USER_ID, {"user_id": user_id})
        return await cur.fetchone()
