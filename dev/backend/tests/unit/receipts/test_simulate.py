import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.features.receipts import simulate
from app.features.user_features.models import CategoryAffinity
from app.game_rules import (
    SIMULATE_BASKET_VARIATION_MAX,
    SIMULATE_BASKET_VARIATION_MIN,
    SIMULATE_CATEGORY_BOOST_ITEMS,
    SIMULATE_DEFAULT_AVG_BASKET,
    SIMULATE_DEFAULT_CATEGORIES,
    SIMULATE_ITEMS_MAX,
    SIMULATE_ITEMS_MIN,
    SIMULATE_PROMO_DISCOUNT_MAX,
    SIMULATE_PROMO_DISCOUNT_MIN,
)
from tests.unit.receipts.data import (
    AVG_BASKET_CASES,
    PICK_STORE_CASES,
    SEED_SAMPLE,
    SKEWED_AFFINITY,
    make_features,
)


@pytest.mark.parametrize(("store_id", "favourite_store_id", "expected"), PICK_STORE_CASES)
def test_pick_store_id(
    store_id: int | None, favourite_store_id: int | None, expected: int | None
) -> None:
    assert simulate.pick_store_id(store_id, favourite_store_id) == expected


@pytest.mark.parametrize("seed", SEED_SAMPLE)
def test_pick_item_count_within_range(seed: int) -> None:
    rng = random.Random(seed)
    count = simulate.pick_item_count(rng)
    assert SIMULATE_ITEMS_MIN <= count <= SIMULATE_ITEMS_MAX


def test_pick_categories_defaults_when_affinity_empty() -> None:
    rng = random.Random(7)
    categories = simulate.pick_categories({}, 6, rng)
    assert len(categories) == 6
    assert set(categories) <= set(SIMULATE_DEFAULT_CATEGORIES)


def test_pick_categories_favours_higher_share() -> None:
    rng = random.Random(42)
    picks = simulate.pick_categories(SKEWED_AFFINITY, 2000, rng)
    dairy_share = picks.count("dairy") / len(picks)
    assert dairy_share > 0.8


def test_pick_categories_falls_back_to_equal_weights_when_shares_are_zero() -> None:
    affinity = {
        "dairy": CategoryAffinity(share=0.0, visits=1, cadence_days=1.0),
        "bakery": CategoryAffinity(share=0.0, visits=1, cadence_days=1.0),
    }
    rng = random.Random(1)
    picks = simulate.pick_categories(affinity, 10, rng)
    assert len(picks) == 10
    assert set(picks) <= {"dairy", "bakery"}


def test_pick_target_total_matches_hand_computed_value_for_known_seed() -> None:
    rng = random.Random(100)
    total = simulate.pick_target_total(Decimal("600"), rng)
    assert total == Decimal("472.44")


@pytest.mark.parametrize("avg_basket", AVG_BASKET_CASES)
def test_generate_typical_items_sum_within_avg_basket_range(avg_basket: Decimal) -> None:
    features = make_features(avg_basket=avg_basket)
    rng = random.Random(1)
    items = simulate.generate_typical_items(features, rng)

    assert SIMULATE_ITEMS_MIN <= len(items) <= SIMULATE_ITEMS_MAX
    total = sum((item.regular_price * item.qty for item in items), Decimal("0"))
    base = avg_basket if avg_basket > 0 else Decimal(str(SIMULATE_DEFAULT_AVG_BASKET))
    lower = base * Decimal(str(SIMULATE_BASKET_VARIATION_MIN))
    upper = base * Decimal(str(SIMULATE_BASKET_VARIATION_MAX))
    assert lower <= total <= upper


def test_split_amount_sums_exactly_to_total() -> None:
    rng = random.Random(11)
    total = Decimal("543.21")
    amounts = simulate.split_amount(total, 5, rng)
    assert len(amounts) == 5
    assert sum(amounts) == total


def test_apply_promo_frequency_close_to_promo_sensitivity() -> None:
    rng = random.Random(5)
    promo_sensitivity = 0.4
    regular_price = Decimal("100.00")
    outcomes = [simulate.apply_promo(regular_price, promo_sensitivity, rng) for _ in range(3000)]
    observed = sum(1 for _, is_promo in outcomes if is_promo) / len(outcomes)
    assert abs(observed - promo_sensitivity) < 0.03
    for paid_price, is_promo in outcomes:
        if is_promo:
            assert Decimal("0") < paid_price < regular_price
        else:
            assert paid_price == regular_price


def test_apply_promo_matches_hand_computed_value_for_known_seed() -> None:
    rng = random.Random(100)
    paid_price, is_promo = simulate.apply_promo(Decimal("100.00"), 1.0, rng)
    assert is_promo is True
    assert paid_price == Decimal("80.90")


def test_apply_promo_zero_sensitivity_never_discounts() -> None:
    rng = random.Random(9)
    regular_price = Decimal("100.00")
    for _ in range(50):
        paid_price, is_promo = simulate.apply_promo(regular_price, 0.0, rng)
        assert is_promo is False
        assert paid_price == regular_price


def test_apply_promo_discount_stays_within_configured_bounds() -> None:
    rng = random.Random(13)
    regular_price = Decimal("100.00")
    lower = regular_price * Decimal(str(1 - SIMULATE_PROMO_DISCOUNT_MAX))
    upper = regular_price * Decimal(str(1 - SIMULATE_PROMO_DISCOUNT_MIN))
    for _ in range(500):
        paid_price, is_promo = simulate.apply_promo(regular_price, 1.0, rng)
        assert is_promo is True
        assert lower <= paid_price <= upper


def test_boost_items_returns_fixed_count_of_hero_category() -> None:
    rng = random.Random(2)
    items = simulate.boost_items("dairy", 0.0, rng)
    assert len(items) == SIMULATE_CATEGORY_BOOST_ITEMS
    assert all(item.category == "dairy" for item in items)


def test_fraud_burst_item_is_single_100_rub_item() -> None:
    item = simulate.fraud_burst_item()
    assert item.regular_price == item.paid_price == Decimal("100")
    assert item.qty == Decimal("1")
    assert item.is_promo is False


def test_fraud_burst_times_are_increasing_and_spaced_by_3_minutes() -> None:
    reference = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
    times = simulate.fraud_burst_times(reference)
    assert times == [
        reference - timedelta(minutes=9),
        reference - timedelta(minutes=6),
        reference - timedelta(minutes=3),
        reference,
    ]
