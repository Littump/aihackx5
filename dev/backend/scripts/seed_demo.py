import asyncio
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

import psycopg
from psycopg import AsyncConnection

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.clock import now
from app.core.config import settings
from app.core.models import AppModel
from app.features.challenges import service as challenges_service
from app.features.domovoy import service as domovoy_service
from app.features.receipts import service as receipts_service
from app.features.receipts import simulate as receipts_simulate
from app.features.savings import service as savings_service
from app.features.user_features import service as user_features_service
from app.features.users import database as users_db
from app.features.users import service as users_service
from app.features.users.models import StoreRow, UserRow
from app.game_rules import level_for_xp

Segment = Literal["regular_mid", "light", "heavy", "dormant"]

DEMO_STORE_NAME = "Пятёрочка, Демо-Хакатон 1"
RECENT_WINDOW_DAYS = 6
RECENT_SMALL_OFFSET_MAX = 4


class DemoProfileSpec(AppModel):
    alias: str
    segment: Segment
    receipt_count: int
    weeks_span: int
    basket_min: int
    basket_max: int
    promo_sensitivity_min: float
    promo_sensitivity_max: float


class SeedResult(AppModel):
    alias: str
    user_id: int
    receipts_created: int
    xp: int
    level: int
    savings_month: float


PROFILES: list[DemoProfileSpec] = [
    DemoProfileSpec(
        alias="Активный Кузя",
        segment="regular_mid",
        receipt_count=13,
        weeks_span=5,
        basket_min=350,
        basket_max=700,
        promo_sensitivity_min=0.25,
        promo_sensitivity_max=0.45,
    ),
    DemoProfileSpec(
        alias="Крупный Барабашка",
        segment="heavy",
        receipt_count=9,
        weeks_span=5,
        basket_min=1200,
        basket_max=2200,
        promo_sensitivity_min=0.10,
        promo_sensitivity_max=0.25,
    ),
    DemoProfileSpec(
        alias="Лёгкий Лешик",
        segment="light",
        receipt_count=8,
        weeks_span=3,
        basket_min=250,
        basket_max=450,
        promo_sensitivity_min=0.35,
        promo_sensitivity_max=0.55,
    ),
]


async def _get_or_create_store(conn: AsyncConnection) -> StoreRow:
    existing = await users_db.get_default_store(conn)
    if existing is not None:
        return existing
    return await users_db.insert_store(
        conn,
        {
            "name": DEMO_STORE_NAME,
            "chain": "pyaterochka",
            "district": "Центр",
            "city": "Москва",
        },
    )


async def _get_or_create_user(conn: AsyncConnection, *, alias: str, segment: Segment) -> UserRow:
    existing_users = await users_db.list_users(conn, limit=1000)
    match = next((u for u in existing_users if u.pseudonym == alias), None)
    if match is not None:
        user = await users_db.get_user_by_id(conn, user_id=match.id)
        assert user is not None
        return user
    return await users_service.create_user(conn, segment=segment, pseudonym=alias)


def _plan_offsets(
    rng: random.Random, *, weeks_span: int, count: int
) -> tuple[list[int], list[int]]:
    total_days = weeks_span * 7
    recent = sorted({0, rng.randint(1, RECENT_SMALL_OFFSET_MAX)}, reverse=True)
    pool = [d for d in range(RECENT_WINDOW_DAYS, total_days) if d not in recent]
    rng.shuffle(pool)
    older_count = max(count - len(recent), 0)
    older = sorted(pool[:older_count], reverse=True)
    return older, recent


def _purchase_moment(offset_days: int, rng: random.Random) -> datetime:
    base = now() - timedelta(days=offset_days)
    hour = rng.randint(9, 21)
    minute = rng.randint(0, 59)
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


async def _seed_receipt(
    conn: AsyncConnection,
    *,
    user_id: int,
    store_id: int,
    offset_days: int,
    profile: DemoProfileSpec,
    rng: random.Random,
) -> None:
    purchased_at = _purchase_moment(offset_days, rng)
    features = await user_features_service.get(conn, user_id)
    target_basket = Decimal(str(rng.randint(profile.basket_min, profile.basket_max)))
    target_promo = rng.uniform(profile.promo_sensitivity_min, profile.promo_sensitivity_max)
    seeded_features = features.model_copy(
        update={
            "avg_basket": target_basket,
            "promo_sensitivity": Decimal(str(round(target_promo, 3))),
        }
    )
    items = receipts_simulate.generate_typical_items(seeded_features, rng)
    async with conn.transaction():
        await receipts_service.process_receipt(
            conn,
            user_id=user_id,
            store_id=store_id,
            purchased_at=purchased_at,
            points_earned=0,
            points_spent=0,
            pos_id=None,
            items=items,
        )


async def _summarize(
    conn: AsyncConnection, *, alias: str, user_id: int, receipts_created: int
) -> SeedResult:
    state = await domovoy_service.get_state(conn, user_id)
    savings = await savings_service.summary(conn, user_id, "month")
    return SeedResult(
        alias=alias,
        user_id=user_id,
        receipts_created=receipts_created,
        xp=state.xp,
        level=level_for_xp(state.xp),
        savings_month=float(savings.amount),
    )


async def _seed_profile(
    conn: AsyncConnection, *, store_id: int, profile: DemoProfileSpec, rng: random.Random
) -> SeedResult:
    user = await _get_or_create_user(conn, alias=profile.alias, segment=profile.segment)
    older_offsets, recent_offsets = _plan_offsets(
        rng, weeks_span=profile.weeks_span, count=profile.receipt_count
    )
    for offset in older_offsets:
        await _seed_receipt(
            conn, user_id=user.id, store_id=store_id, offset_days=offset, profile=profile, rng=rng
        )
    async with conn.transaction():
        await challenges_service.refresh_weekly(conn, user.id)
    for offset in recent_offsets:
        await _seed_receipt(
            conn, user_id=user.id, store_id=store_id, offset_days=offset, profile=profile, rng=rng
        )
    return await _summarize(
        conn,
        alias=profile.alias,
        user_id=user.id,
        receipts_created=len(older_offsets) + len(recent_offsets),
    )


def _print_summary(results: list[SeedResult]) -> None:
    header = (
        f"{'alias':<24}{'user_id':>8}{'receipts':>10}{'xp':>8}{'level':>7}{'savings_month':>16}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r.alias:<24}{r.user_id:>8}{r.receipts_created:>10}"
            f"{r.xp:>8}{r.level:>7}{r.savings_month:>16.2f}"
        )


async def seed(dsn: str) -> list[SeedResult]:
    rng = random.Random()
    async with await psycopg.AsyncConnection.connect(dsn, autocommit=True) as conn:
        store = await _get_or_create_store(conn)
        results = []
        for profile in PROFILES:
            results.append(await _seed_profile(conn, store_id=store.id, profile=profile, rng=rng))
        return results


def main() -> None:
    dsn = sys.argv[1] if len(sys.argv) > 1 else settings.database_url
    results = asyncio.run(seed(dsn))
    _print_summary(results)


if __name__ == "__main__":
    main()
