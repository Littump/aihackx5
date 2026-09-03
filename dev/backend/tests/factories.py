from datetime import datetime
from decimal import Decimal
from itertools import count

from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from app.core.clock import now, week_end, week_start
from app.features.challenges import database as challenges_db
from app.features.challenges.models import ChallengeRow
from app.features.domovoy import database as domovoy_db
from app.features.domovoy.models import DomovoyStateRow
from app.features.receipts import database as receipts_db
from app.features.receipts.models import ReceiptItemRow, ReceiptRow
from app.features.user_features import database as user_features_db
from app.features.user_features.models import UserFeaturesRow
from app.features.users import database as users_db
from app.features.users.models import StoreRow, UserRow
from app.game_rules import FEATURES_WINDOW_WEEKS

_seq = count(1)


def _default_receipt_items() -> list[dict[str, object]]:
    return [
        {
            "product_name": "Молоко",
            "category": "dairy",
            "qty": Decimal("1"),
            "regular_price": Decimal("89.90"),
            "paid_price": Decimal("79.90"),
        },
        {
            "product_name": "Творог",
            "category": "dairy",
            "qty": Decimal("2"),
            "regular_price": Decimal("120.00"),
            "paid_price": Decimal("110.00"),
        },
        {
            "product_name": "Багет",
            "category": "bakery",
            "qty": Decimal("1"),
            "regular_price": Decimal("59.90"),
            "paid_price": Decimal("49.90"),
            "is_promo": True,
        },
    ]


def _line_total(item: dict[str, object], price_key: str) -> Decimal:
    return Decimal(str(item[price_key])) * Decimal(str(item["qty"]))


async def make_store(conn: AsyncConnection, **overrides: object) -> StoreRow:
    n = next(_seq)
    params: dict[str, object] = {
        "name": f"Пятёрочка, Тестовая {n}",
        "chain": "pyaterochka",
        "district": "Центр",
        "city": "Москва",
    }
    params.update(overrides)
    return await users_db.insert_store(conn, params)


async def make_user(conn: AsyncConnection, **overrides: object) -> UserRow:
    n = next(_seq)
    params: dict[str, object] = {
        "pseudonym": f"Домовой-{n}",
        "segment": "regular_mid",
        "favourite_store_id": None,
        "referral_code": f"CODE{n}",
        "referred_by_user_id": None,
        "device_fingerprint": None,
        "social_propensity": Decimal("0"),
    }
    params.update(overrides)
    return await users_db.insert_user(conn, params)


async def _insert_receipt_item(
    conn: AsyncConnection, receipt_id: int, item: dict[str, object]
) -> ReceiptItemRow:
    params: dict[str, object] = {"receipt_id": receipt_id, "is_promo": False}
    params.update(item)
    return await receipts_db.insert_receipt_item(conn, params)


async def make_receipt(
    conn: AsyncConnection,
    user_id: int,
    *,
    items: list[dict[str, object]] | None = None,
    purchased_at: datetime | None = None,
    store_id: int | None = None,
    **overrides: object,
) -> ReceiptRow:
    if store_id is None:
        store_id = (await make_store(conn)).id
    item_specs = items if items is not None else _default_receipt_items()
    cents = Decimal("0.01")
    raw_regular = sum((_line_total(i, "regular_price") for i in item_specs), Decimal("0"))
    raw_paid = sum((_line_total(i, "paid_price") for i in item_specs), Decimal("0"))
    regular_total = raw_regular.quantize(cents)
    paid_total = raw_paid.quantize(cents)
    params: dict[str, object] = {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at or now(),
        "regular_total": regular_total,
        "paid_total": paid_total,
        "discount_total": regular_total - paid_total,
        "points_earned": 0,
        "points_spent": 0,
        "counted": True,
        "is_returned": False,
        "returned_at": None,
        "source": "api",
        "pos_id": None,
    }
    params.update(overrides)
    receipt = await receipts_db.insert_receipt(conn, params)
    for item in item_specs:
        await _insert_receipt_item(conn, receipt.id, item)
    return receipt


async def make_challenge(conn: AsyncConnection, user_id: int, **overrides: object) -> ChallengeRow:
    params: dict[str, object] = {
        "user_id": user_id,
        "type": "frequency",
        "category": None,
        "status": "active",
        "is_hero": True,
        "baseline": Decimal("2"),
        "target": Decimal("3"),
        "progress": Decimal("0"),
        "period_start": week_start(),
        "period_end": week_end(),
        "reward_xp": 50,
        "reward_points": 0,
        "economics": Jsonb(
            {
                "avg_basket": 0.0,
                "expected_incremental_purchases": 0.0,
                "expected_incremental_margin": 0.0,
                "max_reward_rub": 0.0,
                "contribution_margin": 0.0,
                "reward_share_max": 0.0,
            }
        ),
        "rationale_features": Jsonb({}),
        "copy_title": "Заголовок",
        "copy_body": "Текст",
        "copy_explanation": "Почему",
        "copy_source": "template",
    }
    params.update(overrides)
    return await challenges_db.insert_challenge_row(conn, params)


async def make_domovoy_state(
    conn: AsyncConnection, user_id: int, **overrides: object
) -> DomovoyStateRow:
    params: dict[str, object] = {
        "user_id": user_id,
        "xp": 0,
        "level": 1,
        "mood": "cozy",
        "mood_reason": "",
        "streak_weeks": 0,
        "streak_freeze_available": True,
        "items": Jsonb([]),
    }
    params.update(overrides)
    return await domovoy_db.insert_domovoy_state(conn, params)


async def make_user_features(
    conn: AsyncConnection, user_id: int, **overrides: object
) -> UserFeaturesRow:
    params: dict[str, object] = {
        "user_id": user_id,
        "window_weeks": FEATURES_WINDOW_WEEKS,
        "frequency_per_week": Decimal("0"),
        "recency_days": None,
        "avg_basket": Decimal("0"),
        "promo_sensitivity": Decimal("0"),
        "cadence_days": None,
        "category_affinity": Jsonb({}),
        "weekday_pattern": Jsonb([]),
        "realized_savings_30d": Decimal("0"),
        "favourite_store_id": None,
        "cross_chain_share": Decimal("0"),
    }
    params.update(overrides)
    return await user_features_db.insert_user_features(conn, params)
