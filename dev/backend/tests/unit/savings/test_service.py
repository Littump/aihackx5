from datetime import datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.core.errors import AppError
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptWithItems
from app.features.savings import service
from app.features.savings.models import SavingsSummary
from app.features.users import service as users_service
from app.features.users.models import UserRow
from tests.unit.savings.data import AC_RECEIPT, BASE_TIME


def _user() -> UserRow:
    return UserRow(
        id=1,
        pseudonym="Домовой",
        segment="regular_mid",
        favourite_store_id=None,
        referral_code="CODE1",
        referred_by_user_id=None,
        device_fingerprint=None,
        social_propensity=Decimal("0"),
        created_at=BASE_TIME,
    )


async def test_summary_matches_ac_example_with_no_previous_period(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[datetime | None] = []

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        assert user_id == 1
        return _user()

    async def fake_list_receipts(
        _: AsyncConnection, *, user_id: int, since: datetime, until: datetime | None
    ) -> list[ReceiptWithItems]:
        calls.append(until)
        return [AC_RECEIPT] if len(calls) == 1 else []

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(receipts_service, "list_counted_receipts_with_items", fake_list_receipts)

    result = await service.summary(None, 1, "month")  # type: ignore[arg-type]

    assert isinstance(result, SavingsSummary)
    assert result.amount == Decimal("210.00")
    assert result.previous_amount == Decimal("0")
    assert result.delta == Decimal("210.00")
    assert result.discount_amount == Decimal("150.00")
    assert result.points_earned == 10
    assert result.points_spent == 50
    assert result.top_categories == []
    assert len(calls) == 2


async def test_summary_propagates_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        raise AppError("user_not_found", "пользователь не найден", 404)

    monkeypatch.setattr(users_service, "get_user", fake_get_user)

    with pytest.raises(AppError):
        await service.summary(None, 999, "month")  # type: ignore[arg-type]
