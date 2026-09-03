from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.antifraud import service as antifraud_service
from app.features.antifraud.models import FraudCheckRow
from app.features.challenges import service as challenges_service
from app.features.challenges.models import (
    ChallengeListResult,
    RewardLedgerEntry,
    RewardLedgerTotals,
)
from app.features.domovoy import service as domovoy_service
from app.features.pm import database, service
from app.features.pm.models import MechanicDecisionReasons, MechanicDecisionRow
from app.features.user_features import service as user_features_service
from app.features.users import service as users_service
from tests.unit.challenges.data import make_challenge_row, make_features, make_user_row
from tests.unit.domovoy.data import make_domovoy_state_row

CREATED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def _patch_common(monkeypatch: pytest.MonkeyPatch, *, hero: object) -> None:
    async def fake_get_user(_: AsyncConnection, user_id: int) -> object:
        return make_user_row(user_id=user_id)

    async def fake_get_state(_: AsyncConnection, user_id: int) -> object:
        return make_domovoy_state_row(user_id=user_id, xp=120)

    async def fake_features_get(_: AsyncConnection, user_id: int) -> object:
        return make_features()

    async def fake_get_list(_: AsyncConnection, user_id: int) -> ChallengeListResult:
        return ChallengeListResult(hero=hero, side=[], history=[])  # type: ignore[arg-type]

    async def fake_sum_ledger(_: AsyncConnection, user_id: int) -> RewardLedgerTotals:
        return RewardLedgerTotals(points=100, xp=250)

    async def fake_sum_margin(_: AsyncConnection, user_id: int) -> Decimal:
        return Decimal("135.5")

    async def fake_list_for_user(
        _: AsyncConnection, user_id: int, limit: int
    ) -> list[FraudCheckRow]:
        return []

    async def fake_list_ledger(
        _: AsyncConnection, user_id: int, limit: int
    ) -> list[RewardLedgerEntry]:
        return []

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(domovoy_service, "get_state", fake_get_state)
    monkeypatch.setattr(user_features_service, "get", fake_features_get)
    monkeypatch.setattr(challenges_service, "get_list", fake_get_list)
    monkeypatch.setattr(challenges_service, "sum_ledger_for_user", fake_sum_ledger)
    monkeypatch.setattr(challenges_service, "sum_expected_margin_for_month", fake_sum_margin)
    monkeypatch.setattr(antifraud_service, "list_for_user", fake_list_for_user)
    monkeypatch.setattr(challenges_service, "list_ledger_for_user", fake_list_ledger)


async def test_get_user_card_uses_latest_mechanic_decision_reasons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hero = make_challenge_row(id=1)
    _patch_common(monkeypatch, hero=hero)
    decision = MechanicDecisionRow(
        id=1,
        user_id=1,
        mechanic="referral",
        reasons=MechanicDecisionReasons(
            reason="Пригласи друзей",
            completed_challenges_count=3,
            has_league=True,
            social_propensity=Decimal("0.8"),
        ),
        created_at=CREATED_AT,
    )

    async def fake_latest(_: AsyncConnection, user_id: int) -> MechanicDecisionRow:
        return decision

    monkeypatch.setattr(database, "get_latest_mechanic_decision", fake_latest)

    card = await service.get_user_card(None, 1)  # type: ignore[arg-type]

    assert card.level > 0
    assert card.hero_challenge == hero
    assert card.rewards_total_points == 100
    assert card.rewards_total_xp == 250
    assert card.expected_incremental_margin_month == Decimal("135.5")
    assert card.recommended_mechanic.mechanic == "referral"
    assert card.recommended_mechanic.reasons[0] == "Пригласи друзей"
    assert "выполнено челленджей: 3" in card.recommended_mechanic.reasons


async def test_get_user_card_falls_back_when_no_decision_recorded_yet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_common(monkeypatch, hero=None)

    async def fake_latest(_: AsyncConnection, user_id: int) -> None:
        return None

    monkeypatch.setattr(database, "get_latest_mechanic_decision", fake_latest)

    card = await service.get_user_card(None, 1)  # type: ignore[arg-type]

    assert card.hero_challenge is None
    assert card.recommended_mechanic.mechanic == "challenge"
    assert card.recommended_mechanic.reasons == ["ещё не заходил на Home"]
