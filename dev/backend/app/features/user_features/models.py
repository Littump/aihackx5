from datetime import datetime
from decimal import Decimal

from app.core.models import AppModel


class CategoryAffinity(AppModel):
    share: float
    visits: int
    cadence_days: float


class UserFeaturesRow(AppModel):
    user_id: int
    computed_at: datetime
    window_weeks: int
    frequency_per_week: Decimal
    recency_days: int | None
    avg_basket: Decimal
    promo_sensitivity: Decimal
    cadence_days: Decimal | None
    category_affinity: dict[str, CategoryAffinity]
    weekday_pattern: list[float]
    realized_savings_30d: Decimal
    favourite_store_id: int | None
    cross_chain_share: Decimal


class UserFeaturesCalc(AppModel):
    window_weeks: int
    frequency_per_week: Decimal
    recency_days: int
    avg_basket: Decimal
    promo_sensitivity: Decimal
    cadence_days: Decimal | None
    category_affinity: dict[str, CategoryAffinity]
    weekday_pattern: list[float]
    realized_savings_30d: Decimal
    favourite_store_id: int | None
    cross_chain_share: Decimal
