from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.pm import database, service
from app.features.pm.models import (
    Mechanic,
    MechanicDecisionContext,
    MechanicDecisionReasons,
    MechanicDecisionRow,
)

CREATED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


async def test_record_decision_writes_reason_and_context_to_reasons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    async def fake_insert(
        _: AsyncConnection, *, user_id: int, mechanic: Mechanic, reasons: MechanicDecisionReasons
    ) -> MechanicDecisionRow:
        calls.append({"user_id": user_id, "mechanic": mechanic, "reasons": reasons})
        return MechanicDecisionRow(
            id=1, user_id=user_id, mechanic=mechanic, reasons=reasons, created_at=CREATED_AT
        )

    monkeypatch.setattr(database, "insert_mechanic_decision", fake_insert)

    result = await service.record_decision(
        None,  # type: ignore[arg-type]
        user_id=7,
        mechanic="referral",
        reason="Пригласи друзей",
        context=MechanicDecisionContext(
            completed_challenges_count=2, has_league=False, social_propensity=Decimal("0.7")
        ),
    )

    assert len(calls) == 1
    assert calls[0]["user_id"] == 7
    assert calls[0]["mechanic"] == "referral"
    reasons = calls[0]["reasons"]
    assert isinstance(reasons, MechanicDecisionReasons)
    assert reasons.reason == "Пригласи друзей"
    assert reasons.completed_challenges_count == 2
    assert reasons.has_league is False
    assert reasons.social_propensity == Decimal("0.7")
    assert result.mechanic == "referral"
