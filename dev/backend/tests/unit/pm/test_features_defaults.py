from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.features.pm import service
from app.features.user_features.models import UserFeaturesRow

COMPUTED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def _features(*, cadence_days: Decimal | None, favourite_store_id: int | None) -> UserFeaturesRow:
    return UserFeaturesRow(
        user_id=1,
        computed_at=COMPUTED_AT,
        window_weeks=10,
        frequency_per_week=Decimal("0"),
        recency_days=999,
        avg_basket=Decimal("0"),
        promo_sensitivity=Decimal("0"),
        cadence_days=cadence_days,
        category_affinity={},
        weekday_pattern=[0.0] * 7,
        realized_savings_30d=Decimal("0"),
        favourite_store_id=favourite_store_id,
        cross_chain_share=Decimal("0"),
    )


FEATURES_DEFAULTS_CASES: list[tuple[Decimal | None, int | None, Decimal, int]] = [
    (None, None, Decimal("0"), 0),
    (Decimal("3.50"), 12, Decimal("3.50"), 12),
    (None, 12, Decimal("0"), 12),
    (Decimal("3.50"), None, Decimal("3.50"), 0),
]


@pytest.mark.parametrize(
    ("cadence_days", "favourite_store_id", "expected_cadence", "expected_store"),
    FEATURES_DEFAULTS_CASES,
)
def test_features_with_defaults_replaces_none_with_zero(
    cadence_days: Decimal | None,
    favourite_store_id: int | None,
    expected_cadence: Decimal,
    expected_store: int,
) -> None:
    features = _features(cadence_days=cadence_days, favourite_store_id=favourite_store_id)

    result = service._features_with_defaults(features)

    assert result.cadence_days == expected_cadence
    assert result.favourite_store_id == expected_store
    assert result.user_id == features.user_id
