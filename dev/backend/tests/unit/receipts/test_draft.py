import random
from decimal import Decimal

import pytest

from app.core.errors import AppError
from app.features.receipts import catalog, draft
from app.features.receipts.dto import SimulateItemInput
from app.features.receipts.models import ReceiptItemDraft
from app.game_rules import (
    CATEGORIES,
    SIMULATE_DRAFT_ITEMS_MAX,
    SIMULATE_DRAFT_ITEMS_MIN,
    SIMULATE_DRAFT_PROMO_DISCOUNT,
)
from tests.unit.challenges.data import make_challenge_row
from tests.unit.receipts.data import SEED_SAMPLE, SKEWED_AFFINITY, make_features


@pytest.mark.parametrize("seed", SEED_SAMPLE)
def test_draft_items_count_within_draft_range(seed: int) -> None:
    features = make_features(avg_basket=Decimal("600"), category_affinity=SKEWED_AFFINITY)
    items = draft.draft_items(features, None, random.Random(seed))
    assert SIMULATE_DRAFT_ITEMS_MIN <= len(items) <= SIMULATE_DRAFT_ITEMS_MAX


@pytest.mark.parametrize("seed", SEED_SAMPLE)
def test_draft_items_always_contain_goal_category(seed: int) -> None:
    features = make_features(avg_basket=Decimal("600"), category_affinity=SKEWED_AFFINITY)
    items = draft.draft_items(features, "meat_fish", random.Random(seed))
    assert any(item.category == "meat_fish" for item in items)


def test_draft_items_keep_generated_basket_when_goal_category_already_present() -> None:
    features = make_features(avg_basket=Decimal("600"), category_affinity=SKEWED_AFFINITY)
    generated = draft.draft_items(features, None, random.Random(3))
    with_goal = draft.draft_items(features, generated[0].category, random.Random(3))
    assert with_goal == generated


@pytest.mark.parametrize("seed", SEED_SAMPLE)
def test_draft_items_use_catalog_names_without_repeats_inside_category(seed: int) -> None:
    features = make_features(avg_basket=Decimal("600"), category_affinity=SKEWED_AFFINITY)
    items = draft.draft_items(features, None, random.Random(seed))
    names = [item.product_name for item in items]
    assert len(names) == len(set(names))
    for item in items:
        assert item.product_name in catalog.products_for(item.category)


@pytest.mark.parametrize("seed", SEED_SAMPLE)
def test_draft_item_prices_are_whole_rubles(seed: int) -> None:
    features = make_features(avg_basket=Decimal("600"), category_affinity=SKEWED_AFFINITY)
    items = draft.draft_items(features, None, random.Random(seed))
    for item in items:
        assert draft.to_draft_item(item, None).price == item.paid_price.to_integral_value()


def test_to_draft_item_marks_goal_category_and_exposes_paid_price() -> None:
    item = ReceiptItemDraft(
        product_name="Молоко",
        category="dairy",
        qty=Decimal("1"),
        regular_price=Decimal("100.00"),
        paid_price=Decimal("80.00"),
        is_promo=True,
    )
    goal_item = draft.to_draft_item(item, "dairy")
    other_item = draft.to_draft_item(item, "bakery")
    assert goal_item.price == Decimal("80.00")
    assert goal_item.is_promo is True
    assert goal_item.matches_goal is True
    assert other_item.matches_goal is False


def test_goal_category_of_ignores_frequency_hero() -> None:
    assert draft.goal_category_of(make_challenge_row(type="frequency")) is None
    assert draft.goal_category_of(make_challenge_row(type="category", category="dairy")) == "dairy"
    assert draft.goal_category_of(None) is None


def test_goal_of_copies_title_and_progress() -> None:
    hero = make_challenge_row(
        type="category", category="dairy", progress=Decimal("1"), target=Decimal("3")
    )
    goal = draft.goal_of(hero)
    assert goal is not None
    assert goal.type == "category"
    assert goal.category == "dairy"
    assert goal.title == hero.copy_title
    assert goal.progress == Decimal("1")
    assert goal.target == Decimal("3")
    assert draft.goal_of(None) is None


def test_item_from_input_without_promo_keeps_price_as_regular() -> None:
    item = draft.item_from_input(SimulateItemInput(category="dairy", price=120.0), 1)
    assert item.regular_price == Decimal("120.00")
    assert item.paid_price == Decimal("120.00")
    assert item.qty == Decimal("1")
    assert item.is_promo is False


def test_item_from_input_with_promo_restores_regular_price_by_configured_discount() -> None:
    item = draft.item_from_input(SimulateItemInput(category="dairy", price=80.0, is_promo=True), 1)
    expected = (Decimal("80.00") / Decimal(str(1 - SIMULATE_DRAFT_PROMO_DISCOUNT))).quantize(
        Decimal("0.01")
    )
    assert item.regular_price == expected
    assert item.paid_price == Decimal("80.00")
    assert item.regular_price > item.paid_price


def test_item_from_input_generates_product_name_from_catalog_when_missing() -> None:
    item = draft.item_from_input(SimulateItemInput(category="bakery", price=50.0), 2)
    assert item.product_name == catalog.products_for("bakery")[1]


def test_item_from_input_keeps_given_product_name() -> None:
    item = draft.item_from_input(
        SimulateItemInput(product_name="Молоко 3.2%", category="dairy", price=99.9), 1
    )
    assert item.product_name == "Молоко 3.2%"


def test_item_from_input_rejects_unknown_category() -> None:
    with pytest.raises(AppError) as exc:
        draft.item_from_input(SimulateItemInput(category="crypto", price=10.0), 1)
    assert exc.value.code == "unknown_category"
    assert exc.value.status == 422


@pytest.mark.parametrize("category", CATEGORIES)
def test_items_from_input_accepts_every_domain_category(category: str) -> None:
    items = draft.items_from_input([SimulateItemInput(category=category, price=10.0)])
    assert items[0].category == category
