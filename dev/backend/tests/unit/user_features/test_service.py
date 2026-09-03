from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptWithItems
from app.features.user_features import database, service
from app.features.user_features.models import UserFeaturesCalc, UserFeaturesRow
from app.features.users import service as users_service
from app.features.users.models import StoreRow

NOW = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)
PURCHASED_AT = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)


def _store() -> StoreRow:
    return StoreRow(id=1, name="Пятёрочка", chain="pyaterochka", district="Центр", city="Москва")


def _receipt() -> ReceiptWithItems:
    return ReceiptWithItems(
        id=1,
        store_id=1,
        purchased_at=PURCHASED_AT,
        regular_total=Decimal("100.00"),
        paid_total=Decimal("90.00"),
        points_earned=0,
        points_spent=0,
        items=[],
    )


def _row() -> UserFeaturesRow:
    return UserFeaturesRow(
        user_id=1,
        computed_at=NOW,
        window_weeks=10,
        frequency_per_week=Decimal("0.100"),
        recency_days=5,
        avg_basket=Decimal("90.00"),
        promo_sensitivity=Decimal("0"),
        cadence_days=None,
        category_affinity={},
        weekday_pattern=[0.0] * 7,
        realized_savings_30d=Decimal("10.00"),
        favourite_store_id=1,
        cross_chain_share=Decimal("0"),
    )


async def test_recompute_upserts_features_built_from_receipts(
    monkeypatch: pytest.MonkeyPatch, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    captured: dict[str, UserFeaturesCalc | int] = {}

    async def fake_list_receipts(
        _: AsyncConnection, *, user_id: int, since: datetime
    ) -> list[ReceiptWithItems]:
        assert user_id == 1
        return [_receipt()]

    async def fake_get_stores(_: AsyncConnection, *, store_ids: list[int]) -> list[StoreRow]:
        assert store_ids == [1]
        return [_store()]

    async def fake_upsert(
        _: AsyncConnection, user_id: int, features: UserFeaturesCalc
    ) -> UserFeaturesRow:
        captured["user_id"] = user_id
        captured["features"] = features
        return _row()

    monkeypatch.setattr(receipts_service, "list_counted_receipts_with_items", fake_list_receipts)
    monkeypatch.setattr(users_service, "get_stores_by_ids", fake_get_stores)
    monkeypatch.setattr(database, "upsert_user_features", fake_upsert)

    result = await service.recompute(None, 1)  # type: ignore[arg-type]

    assert result == _row()
    assert captured["user_id"] == 1
    features = captured["features"]
    assert isinstance(features, UserFeaturesCalc)
    assert features.favourite_store_id == 1
    assert features.frequency_per_week == Decimal("0.100")
    assert features.avg_basket == Decimal("90.00")


async def test_get_returns_existing_row_without_recompute(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(_: AsyncConnection, *, user_id: int) -> UserFeaturesRow:
        return _row()

    async def fail_recompute(*args: object, **kwargs: object) -> UserFeaturesRow:
        raise AssertionError("recompute must not run when a row already exists")

    monkeypatch.setattr(database, "get_user_features_by_user_id", fake_get)
    monkeypatch.setattr(service, "recompute", fail_recompute)

    result = await service.get(None, 1)  # type: ignore[arg-type]
    assert result == _row()


async def test_get_recomputes_when_row_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(_: AsyncConnection, *, user_id: int) -> UserFeaturesRow | None:
        return None

    async def fake_recompute(_: AsyncConnection, user_id: int) -> UserFeaturesRow:
        assert user_id == 1
        return _row()

    monkeypatch.setattr(database, "get_user_features_by_user_id", fake_get)
    monkeypatch.setattr(service, "recompute", fake_recompute)

    result = await service.get(None, 1)  # type: ignore[arg-type]
    assert result == _row()
