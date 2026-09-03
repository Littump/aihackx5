from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.challenges import service as challenges_service
from app.features.challenges.models import ChallengeProgressDelta
from app.features.domovoy import service as domovoy_service
from app.features.domovoy.models import DomovoyDelta, DomovoyStateRow
from app.features.receipts import database as receipts_db
from app.features.receipts import service
from app.features.receipts.dto import ReceiptItemInput
from app.features.receipts.models import ReceiptDetail, ReceiptItemRow, ReceiptRow
from app.features.users import service as users_service
from app.features.users.models import StoreRow, UserRow

CREATED_AT = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
PURCHASED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _user_row() -> UserRow:
    return UserRow(
        id=1,
        pseudonym="Уютный Домовой",
        segment="regular_mid",
        favourite_store_id=None,
        referral_code="CODE1",
        referred_by_user_id=None,
        device_fingerprint=None,
        social_propensity=Decimal("0"),
        created_at=CREATED_AT,
    )


def _store_row() -> StoreRow:
    return StoreRow(
        id=5, name="Пятёрочка, Ленина 12", chain="pyaterochka", district="Центр", city="Москва"
    )


def _receipt_row() -> ReceiptRow:
    return ReceiptRow(
        id=10,
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
        regular_total=Decimal("100.00"),
        paid_total=Decimal("90.00"),
        discount_total=Decimal("10.00"),
        points_earned=0,
        points_spent=0,
        counted=True,
        is_returned=False,
        returned_at=None,
        source="api",
        pos_id=None,
        created_at=CREATED_AT,
    )


def _item_row() -> ReceiptItemRow:
    return ReceiptItemRow(
        id=1,
        receipt_id=10,
        product_name="Молоко",
        category="dairy",
        qty=Decimal("1"),
        regular_price=Decimal("100.00"),
        paid_price=Decimal("90.00"),
        is_promo=False,
    )


def _domovoy_delta() -> DomovoyDelta:
    return DomovoyDelta(
        xp_delta=10, xp=60, level=1, mood="cozy", mood_reason="", last_fed_at=PURCHASED_AT
    )


def _domovoy_final_state() -> DomovoyStateRow:
    return DomovoyStateRow(
        user_id=1,
        xp=110,
        level=1,
        mood="cheerful",
        mood_reason="5 разных категорий за неделю",
        streak_weeks=1,
        streak_freeze_available=True,
        items=[],
        last_fed_at=PURCHASED_AT,
        updated_at=PURCHASED_AT,
    )


def _completed_challenge_delta() -> ChallengeProgressDelta:
    return ChallengeProgressDelta(
        challenge_id=7,
        progress_before=Decimal("2"),
        progress_after=Decimal("3"),
        target=Decimal("3"),
        completed=True,
        reward_points=30,
        reward_xp=50,
    )


async def _fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
    assert user_id == 1
    return _user_row()


async def _fake_get_store(_: AsyncConnection, store_id: int) -> StoreRow:
    assert store_id == 5
    return _store_row()


async def _fake_no_dedup(*args: object, **kwargs: object) -> bool:
    return False


async def _fake_no_daily_limit(*args: object, **kwargs: object) -> int:
    return 0


async def _fake_insert_receipt(_: AsyncConnection, params: dict[str, object]) -> ReceiptRow:
    assert params["counted"] is True
    return _receipt_row()


async def _fake_insert_item(_: AsyncConnection, params: dict[str, object]) -> ReceiptItemRow:
    return _item_row()


async def _fake_recompute_user_features(_: AsyncConnection, user_id: int) -> None:
    assert user_id == 1


async def _fake_domovoy_on_receipt(
    _: AsyncConnection, user_id: int, receipt: ReceiptRow
) -> DomovoyDelta:
    assert user_id == 1
    assert receipt.id == 10
    return _domovoy_delta()


async def _fake_domovoy_get_state(_: AsyncConnection, user_id: int) -> DomovoyStateRow:
    assert user_id == 1
    return _domovoy_final_state()


async def _fake_challenges_on_receipt(
    _: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> list[ChallengeProgressDelta]:
    assert user_id == 1
    assert receipt.counted is True
    return [_completed_challenge_delta()]


def _patch_process_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(users_service, "get_user", _fake_get_user)
    monkeypatch.setattr(users_service, "get_store", _fake_get_store)
    monkeypatch.setattr(
        receipts_db, "exists_counted_receipt_in_store_within_window", _fake_no_dedup
    )
    monkeypatch.setattr(receipts_db, "count_counted_receipts_in_range", _fake_no_daily_limit)
    monkeypatch.setattr(receipts_db, "insert_receipt", _fake_insert_receipt)
    monkeypatch.setattr(receipts_db, "insert_receipt_item", _fake_insert_item)
    monkeypatch.setattr(service, "_recompute_user_features", _fake_recompute_user_features)
    monkeypatch.setattr(domovoy_service, "on_receipt", _fake_domovoy_on_receipt)
    monkeypatch.setattr(domovoy_service, "get_state", _fake_domovoy_get_state)
    monkeypatch.setattr(challenges_service, "on_receipt", _fake_challenges_on_receipt)


async def test_process_receipt_happy_path_combines_domovoy_and_challenges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_process_receipt(monkeypatch)
    items = [
        ReceiptItemInput(
            product_name="Молоко",
            category="dairy",
            qty=1,
            regular_price=100.00,
            paid_price=90.00,
        )
    ]

    outcome = await service.process_receipt(
        None,  # type: ignore[arg-type]
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
        points_earned=0,
        points_spent=0,
        pos_id=None,
        items=items,
    )

    assert outcome.counted is True
    assert outcome.counted_reason is None
    assert outcome.xp_delta == 60
    assert outcome.domovoy.xp == 110
    assert outcome.domovoy.mood == "cheerful"
    assert outcome.domovoy.streak_weeks == 1
    assert outcome.savings_delta == Decimal("10.00")
    assert len(outcome.challenges) == 1
    assert outcome.challenges[0].challenge_id == 7
    assert outcome.challenges[0].completed is True
    assert outcome.fraud.decision == "approve"
    assert outcome.receipt.store_name == "Пятёрочка, Ленина 12"
    assert outcome.receipt.items == [_item_row()]
    assert outcome.league_rank_before is None
    assert outcome.referral_status is None
    assert outcome.achievements_unlocked == []
