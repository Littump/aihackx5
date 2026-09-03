import pytest

from app.features.user_features import calc
from tests.unit.user_features.data import (
    EXPECTED_AVG_BASKET,
    EXPECTED_CADENCE_DAYS,
    EXPECTED_CATEGORY_CADENCE,
    EXPECTED_CATEGORY_SHARE,
    EXPECTED_CATEGORY_VISITS,
    EXPECTED_CROSS_CHAIN_SHARE,
    EXPECTED_FAVOURITE_STORE_ID,
    EXPECTED_FREQUENCY_PER_WEEK,
    EXPECTED_MULTI_CATEGORY_PROMO_SENSITIVITY,
    EXPECTED_MULTI_CATEGORY_SHARE,
    EXPECTED_POINTS_SPENT_SAVINGS,
    EXPECTED_PROMO_SENSITIVITY,
    EXPECTED_REALIZED_SAVINGS_30D,
    EXPECTED_RECENCY_DAYS,
    EXPECTED_WEEKDAY_PATTERN,
    MULTI_CATEGORY_RECEIPT,
    NOW,
    POINTS_SPENT_RECEIPT,
    SAME_CATEGORY_RECEIPT,
    SIX_RECEIPTS,
    STORE_CHAINS,
    STORE_PEREKRESTOK,
    TIE_RECEIPTS,
    TIE_WITH_NON_MAX_LATEST_RECEIPTS,
    WINDOW_WEEKS,
)


def test_frequency_per_week_matches_hand_calc() -> None:
    result = calc.compute_frequency_per_week(SIX_RECEIPTS, window_weeks=WINDOW_WEEKS)
    assert result == EXPECTED_FREQUENCY_PER_WEEK


def test_recency_days_matches_hand_calc() -> None:
    assert calc.compute_recency_days(SIX_RECEIPTS, now=NOW) == EXPECTED_RECENCY_DAYS


def test_avg_basket_matches_hand_calc() -> None:
    assert calc.compute_avg_basket(SIX_RECEIPTS) == EXPECTED_AVG_BASKET


def test_promo_sensitivity_matches_hand_calc() -> None:
    assert calc.compute_promo_sensitivity(SIX_RECEIPTS) == EXPECTED_PROMO_SENSITIVITY


def test_cadence_days_matches_hand_calc() -> None:
    assert calc.compute_cadence_days(SIX_RECEIPTS) == EXPECTED_CADENCE_DAYS


def test_category_affinity_matches_hand_calc() -> None:
    affinity = calc.compute_category_affinity(SIX_RECEIPTS)

    assert set(affinity) == set(EXPECTED_CATEGORY_SHARE)
    for category, expected_share in EXPECTED_CATEGORY_SHARE.items():
        assert affinity[category].share == pytest.approx(expected_share)
        assert affinity[category].visits == EXPECTED_CATEGORY_VISITS[category]
        cadence = affinity[category].cadence_days
        assert cadence == pytest.approx(EXPECTED_CATEGORY_CADENCE[category])


def test_favourite_store_id_matches_hand_calc() -> None:
    assert calc.compute_favourite_store_id(SIX_RECEIPTS) == EXPECTED_FAVOURITE_STORE_ID


def test_cross_chain_share_matches_hand_calc() -> None:
    favourite = calc.compute_favourite_store_id(SIX_RECEIPTS)
    result = calc.compute_cross_chain_share(
        SIX_RECEIPTS, store_chains=STORE_CHAINS, favourite_store_id=favourite
    )
    assert result == EXPECTED_CROSS_CHAIN_SHARE


def test_realized_savings_30d_matches_hand_calc() -> None:
    assert calc.compute_realized_savings_30d(SIX_RECEIPTS) == EXPECTED_REALIZED_SAVINGS_30D


def test_realized_savings_30d_adds_points_spent_per_domain_rules() -> None:
    result = calc.compute_realized_savings_30d(POINTS_SPENT_RECEIPT)
    assert result == EXPECTED_POINTS_SPENT_SAVINGS


def test_weekday_pattern_matches_hand_calc() -> None:
    pattern = calc.compute_weekday_pattern(SIX_RECEIPTS)
    assert pattern == pytest.approx(EXPECTED_WEEKDAY_PATTERN)


def test_favourite_store_id_tie_goes_to_last_receipt() -> None:
    assert calc.compute_favourite_store_id(TIE_RECEIPTS) == STORE_PEREKRESTOK.id


def test_favourite_store_id_tie_skips_non_max_store_latest_receipt() -> None:
    result = calc.compute_favourite_store_id(TIE_WITH_NON_MAX_LATEST_RECEIPTS)
    assert result == STORE_PEREKRESTOK.id


def test_category_affinity_aggregates_multiple_items_in_one_receipt() -> None:
    affinity = calc.compute_category_affinity(MULTI_CATEGORY_RECEIPT)
    assert affinity["dairy"].share == pytest.approx(EXPECTED_MULTI_CATEGORY_SHARE["dairy"])
    assert affinity["bakery"].share == pytest.approx(EXPECTED_MULTI_CATEGORY_SHARE["bakery"])
    assert affinity["dairy"].visits == 1
    assert affinity["bakery"].visits == 1


def test_promo_sensitivity_sums_items_within_one_receipt() -> None:
    result = calc.compute_promo_sensitivity(MULTI_CATEGORY_RECEIPT)
    assert result == EXPECTED_MULTI_CATEGORY_PROMO_SENSITIVITY


def test_category_affinity_dedupes_same_category_items_in_one_receipt() -> None:
    affinity = calc.compute_category_affinity(SAME_CATEGORY_RECEIPT)
    assert affinity["dairy"].visits == 1


def test_compute_assembles_all_formulas_for_six_receipts() -> None:
    features = calc.compute(
        SIX_RECEIPTS,
        SIX_RECEIPTS,
        now=NOW,
        window_weeks=WINDOW_WEEKS,
        store_chains=STORE_CHAINS,
    )

    assert features.frequency_per_week == EXPECTED_FREQUENCY_PER_WEEK
    assert features.favourite_store_id == EXPECTED_FAVOURITE_STORE_ID
    assert features.cross_chain_share == EXPECTED_CROSS_CHAIN_SHARE
    assert features.realized_savings_30d == EXPECTED_REALIZED_SAVINGS_30D
