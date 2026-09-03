import random
from datetime import datetime, timedelta
from decimal import Decimal

from psycopg import AsyncConnection

from app.core.clock import now as clock_now
from app.features.challenges import service as challenges_service
from app.features.receipts.models import (
    ReceiptItemDraft,
    ReceiptProcessingOutcome,
    SimulateScenario,
)
from app.features.user_features import service as user_features_service
from app.features.user_features.models import CategoryAffinity, UserFeaturesRow
from app.features.users import service as users_service
from app.game_rules import (
    SIMULATE_BASKET_VARIATION_MAX,
    SIMULATE_BASKET_VARIATION_MIN,
    SIMULATE_BOOST_ITEM_PRICE,
    SIMULATE_CATEGORY_BOOST_ITEMS,
    SIMULATE_DEFAULT_AVG_BASKET,
    SIMULATE_DEFAULT_CATEGORIES,
    SIMULATE_FRAUD_BURST_AMOUNT,
    SIMULATE_FRAUD_BURST_CATEGORY,
    SIMULATE_FRAUD_BURST_COUNT,
    SIMULATE_FRAUD_BURST_INTERVAL_MIN,
    SIMULATE_ITEM_WEIGHT_MAX,
    SIMULATE_ITEM_WEIGHT_MIN,
    SIMULATE_ITEMS_MAX,
    SIMULATE_ITEMS_MIN,
    SIMULATE_PROMO_DISCOUNT_MAX,
    SIMULATE_PROMO_DISCOUNT_MIN,
)

CENT = Decimal("0.01")
PRODUCT_LABELS: dict[str, str] = {
    "dairy": "Молочный",
    "bakery": "Хлебный",
    "fruits_veg": "Овощной",
    "meat_fish": "Мясной",
    "grocery": "Бакалейный",
    "snacks": "Снековый",
    "drinks": "Напиток",
    "alcohol": "Алкогольный",
    "household": "Хозяйственный",
    "beauty": "Косметический",
    "ready_food": "Готовый",
    "other": "Прочий",
}


def pick_store_id(store_id: int | None, favourite_store_id: int | None) -> int | None:
    if store_id is not None:
        return store_id
    return favourite_store_id


def pick_item_count(rng: random.Random) -> int:
    return rng.randint(SIMULATE_ITEMS_MIN, SIMULATE_ITEMS_MAX)


def pick_categories(
    affinity: dict[str, CategoryAffinity], count: int, rng: random.Random
) -> list[str]:
    if not affinity:
        return [rng.choice(SIMULATE_DEFAULT_CATEGORIES) for _ in range(count)]
    categories = list(affinity.keys())
    weights = [affinity[c].share for c in categories]
    if sum(weights) <= 0:
        weights = [1.0] * len(categories)
    return rng.choices(categories, weights=weights, k=count)


def pick_target_total(avg_basket: Decimal, rng: random.Random) -> Decimal:
    base = avg_basket if avg_basket > 0 else Decimal(str(SIMULATE_DEFAULT_AVG_BASKET))
    factor = rng.uniform(SIMULATE_BASKET_VARIATION_MIN, SIMULATE_BASKET_VARIATION_MAX)
    return (base * Decimal(str(factor))).quantize(CENT)


def split_amount(total: Decimal, count: int, rng: random.Random) -> list[Decimal]:
    weight_bounds = (SIMULATE_ITEM_WEIGHT_MIN, SIMULATE_ITEM_WEIGHT_MAX)
    raw_weights = [rng.uniform(*weight_bounds) for _ in range(count)]
    weight_sum = sum(raw_weights)
    amounts = [(total * Decimal(str(w / weight_sum))).quantize(CENT) for w in raw_weights]
    amounts[-1] += total - sum(amounts)
    return amounts


def apply_promo(
    regular_price: Decimal, promo_sensitivity: float, rng: random.Random
) -> tuple[Decimal, bool]:
    if rng.random() >= promo_sensitivity:
        return regular_price, False
    discount = rng.uniform(SIMULATE_PROMO_DISCOUNT_MIN, SIMULATE_PROMO_DISCOUNT_MAX)
    paid_price = (regular_price * Decimal(str(1 - discount))).quantize(CENT)
    return paid_price, True


def build_item(
    category: str, index: int, regular_price: Decimal, paid_price: Decimal, is_promo: bool
) -> ReceiptItemDraft:
    label = PRODUCT_LABELS.get(category, category)
    return ReceiptItemDraft(
        product_name=f"{label} товар {index}",
        category=category,
        qty=Decimal("1"),
        regular_price=regular_price,
        paid_price=paid_price,
        is_promo=is_promo,
    )


def generate_typical_items(features: UserFeaturesRow, rng: random.Random) -> list[ReceiptItemDraft]:
    count = pick_item_count(rng)
    categories = pick_categories(features.category_affinity, count, rng)
    target_total = pick_target_total(features.avg_basket, rng)
    amounts = split_amount(target_total, count, rng)
    promo_sensitivity = float(features.promo_sensitivity)
    items = []
    for index, (category, regular_price) in enumerate(zip(categories, amounts, strict=True), 1):
        paid_price, is_promo = apply_promo(regular_price, promo_sensitivity, rng)
        items.append(build_item(category, index, regular_price, paid_price, is_promo))
    return items


def boost_items(
    category: str, promo_sensitivity: float, rng: random.Random
) -> list[ReceiptItemDraft]:
    items = []
    price = Decimal(str(SIMULATE_BOOST_ITEM_PRICE))
    for index in range(1, SIMULATE_CATEGORY_BOOST_ITEMS + 1):
        paid_price, is_promo = apply_promo(price, promo_sensitivity, rng)
        items.append(build_item(category, index, price, paid_price, is_promo))
    return items


def fraud_burst_item() -> ReceiptItemDraft:
    amount = Decimal(str(SIMULATE_FRAUD_BURST_AMOUNT))
    return ReceiptItemDraft(
        product_name="Фрод-товар",
        category=SIMULATE_FRAUD_BURST_CATEGORY,
        qty=Decimal("1"),
        regular_price=amount,
        paid_price=amount,
        is_promo=False,
    )


def fraud_burst_times(reference: datetime) -> list[datetime]:
    interval = timedelta(minutes=SIMULATE_FRAUD_BURST_INTERVAL_MIN)
    offsets = range(SIMULATE_FRAUD_BURST_COUNT - 1, -1, -1)
    return [reference - interval * offset for offset in offsets]


async def simulate_receipt(
    conn: AsyncConnection,
    *,
    user_id: int,
    scenario: SimulateScenario,
    store_id: int | None,
) -> ReceiptProcessingOutcome:
    # отложенный импорт разрывает цикл: service.py зовёт simulate_receipt
    from app.features.receipts import service as receipts_service

    await users_service.get_user(conn, user_id)
    features = await user_features_service.get(conn, user_id)
    resolved_store_id = await _resolve_store_id(conn, store_id=store_id, features=features)
    if scenario == "fraud_burst":
        return await _simulate_fraud_burst(conn, user_id=user_id, store_id=resolved_store_id)
    rng = random.Random()
    items = generate_typical_items(features, rng)
    if scenario == "category_boost":
        hero_category = await _hero_boost_category(conn, user_id)
        if hero_category is not None:
            items = items + boost_items(hero_category, float(features.promo_sensitivity), rng)
    return await receipts_service.process_receipt(
        conn,
        user_id=user_id,
        store_id=resolved_store_id,
        purchased_at=clock_now(),
        points_earned=0,
        points_spent=0,
        pos_id=None,
        items=items,
    )


async def _resolve_store_id(
    conn: AsyncConnection, *, store_id: int | None, features: UserFeaturesRow
) -> int:
    picked = pick_store_id(store_id, features.favourite_store_id)
    if picked is not None:
        return picked
    default_store = await users_service.get_default_store(conn)
    return default_store.id


async def _hero_boost_category(conn: AsyncConnection, user_id: int) -> str | None:
    hero = (await challenges_service.get_list(conn, user_id)).hero
    if hero is None or hero.type != "category" or hero.category is None:
        return None
    return hero.category


async def _simulate_fraud_burst(
    conn: AsyncConnection, *, user_id: int, store_id: int
) -> ReceiptProcessingOutcome:
    from app.features.receipts import service as receipts_service

    outcome: ReceiptProcessingOutcome | None = None
    for purchased_at in fraud_burst_times(clock_now()):
        outcome = await receipts_service.process_receipt(
            conn,
            user_id=user_id,
            store_id=store_id,
            purchased_at=purchased_at,
            points_earned=0,
            points_spent=0,
            pos_id=None,
            items=[fraud_burst_item()],
        )
    assert outcome is not None
    return outcome
