import random
from collections.abc import Sequence
from decimal import Decimal

from psycopg import AsyncConnection

from app.core.errors import AppError
from app.features.challenges.models import ChallengeRow
from app.features.receipts import simulate
from app.features.receipts.models import (
    ReceiptItemDraft,
    SimulateDraft,
    SimulateDraftGoal,
    SimulateDraftItem,
    SimulateItemInputLike,
)
from app.features.user_features import service as user_features_service
from app.features.user_features.models import UserFeaturesRow
from app.features.users import service as users_service
from app.game_rules import (
    CATEGORIES,
    SIMULATE_DRAFT_DEFAULT_PRICE,
    SIMULATE_DRAFT_ITEMS_MAX,
    SIMULATE_DRAFT_ITEMS_MIN,
    SIMULATE_DRAFT_PROMO_DISCOUNT,
)

CENT = Decimal("0.01")


async def build_draft(
    conn: AsyncConnection, *, user_id: int, store_id: int | None
) -> SimulateDraft:
    await users_service.get_user(conn, user_id)
    features = await user_features_service.get(conn, user_id)
    resolved_store_id = await simulate.resolve_store_id(conn, store_id=store_id, features=features)
    store = await users_service.get_store(conn, resolved_store_id)
    hero = await simulate.hero_challenge(conn, user_id)
    goal_category = goal_category_of(hero)
    items = draft_items(features, goal_category, random.Random())
    return SimulateDraft(
        store_id=store.id,
        store_name=store.name,
        goal=goal_of(hero),
        items=[to_draft_item(item, goal_category) for item in items],
        categories=list(CATEGORIES),
        default_price=Decimal(SIMULATE_DRAFT_DEFAULT_PRICE),
    )


def goal_category_of(hero: ChallengeRow | None) -> str | None:
    if hero is None or hero.type != "category":
        return None
    return hero.category


def goal_of(hero: ChallengeRow | None) -> SimulateDraftGoal | None:
    if hero is None:
        return None
    return SimulateDraftGoal(
        type=hero.type,
        category=hero.category,
        title=hero.copy_title,
        progress=hero.progress,
        target=hero.target,
    )


def draft_items(
    features: UserFeaturesRow, goal_category: str | None, rng: random.Random
) -> list[ReceiptItemDraft]:
    count = rng.randint(SIMULATE_DRAFT_ITEMS_MIN, SIMULATE_DRAFT_ITEMS_MAX)
    items = simulate.generate_typical_items(features, rng, count=count)
    if goal_category is None or any(item.category == goal_category for item in items):
        return items
    head = items[0]
    goal_item = simulate.build_item(
        goal_category, 1, head.regular_price, head.paid_price, head.is_promo
    )
    return [goal_item, *items[1:]]


def to_draft_item(item: ReceiptItemDraft, goal_category: str | None) -> SimulateDraftItem:
    return SimulateDraftItem(
        product_name=item.product_name,
        category=item.category,
        price=item.paid_price,
        is_promo=item.is_promo,
        matches_goal=goal_category is not None and item.category == goal_category,
    )


def items_from_input(items: Sequence[SimulateItemInputLike]) -> list[ReceiptItemDraft]:
    return [item_from_input(item, index) for index, item in enumerate(items, 1)]


def item_from_input(item: SimulateItemInputLike, index: int) -> ReceiptItemDraft:
    if item.category not in CATEGORIES:
        raise AppError("unknown_category", f"Неизвестная категория: {item.category}", status=422)
    paid_price = Decimal(str(item.price)).quantize(CENT)
    return ReceiptItemDraft(
        product_name=item.product_name or simulate.default_product_name(item.category, index),
        category=item.category,
        qty=Decimal("1"),
        regular_price=regular_price_for(paid_price, item.is_promo),
        paid_price=paid_price,
        is_promo=item.is_promo,
    )


def regular_price_for(paid_price: Decimal, is_promo: bool) -> Decimal:
    if not is_promo:
        return paid_price
    return (paid_price / Decimal(str(1 - SIMULATE_DRAFT_PROMO_DISCOUNT))).quantize(CENT)
