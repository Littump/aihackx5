from decimal import Decimal

from app.features.user_features import calc
from app.game_rules import USER_FEATURES_RECENCY_NO_HISTORY_DAYS
from tests.unit.user_features.data import NOW, STORE_CHAINS, WINDOW_WEEKS


def test_frequency_per_week_is_zero_without_receipts() -> None:
    assert calc.compute_frequency_per_week([], window_weeks=WINDOW_WEEKS) == Decimal("0")


def test_recency_days_is_sentinel_without_receipts() -> None:
    assert calc.compute_recency_days([], now=NOW) == USER_FEATURES_RECENCY_NO_HISTORY_DAYS


def test_avg_basket_is_zero_without_receipts() -> None:
    assert calc.compute_avg_basket([]) == Decimal("0")


def test_promo_sensitivity_is_zero_without_receipts() -> None:
    assert calc.compute_promo_sensitivity([]) == Decimal("0")


def test_cadence_days_is_none_without_receipts() -> None:
    assert calc.compute_cadence_days([]) is None


def test_category_affinity_is_empty_without_receipts() -> None:
    assert calc.compute_category_affinity([]) == {}


def test_favourite_store_id_is_none_without_receipts() -> None:
    assert calc.compute_favourite_store_id([]) is None


def test_cross_chain_share_is_zero_without_receipts() -> None:
    result = calc.compute_cross_chain_share([], store_chains=STORE_CHAINS, favourite_store_id=None)
    assert result == Decimal("0")


def test_realized_savings_30d_is_zero_without_receipts() -> None:
    assert calc.compute_realized_savings_30d([]) == Decimal("0")


def test_weekday_pattern_is_all_zero_without_receipts() -> None:
    assert calc.compute_weekday_pattern([]) == [0.0] * 7


def test_compute_returns_all_defaults_without_receipts() -> None:
    features = calc.compute([], [], now=NOW, window_weeks=WINDOW_WEEKS, store_chains=STORE_CHAINS)

    assert features.frequency_per_week == Decimal("0")
    assert features.recency_days == USER_FEATURES_RECENCY_NO_HISTORY_DAYS
    assert features.avg_basket == Decimal("0")
    assert features.promo_sensitivity == Decimal("0")
    assert features.cadence_days is None
    assert features.category_affinity == {}
    assert features.favourite_store_id is None
    assert features.cross_chain_share == Decimal("0")
    assert features.realized_savings_30d == Decimal("0")
    assert features.weekday_pattern == [0.0] * 7
