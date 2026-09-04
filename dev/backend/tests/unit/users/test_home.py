from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.challenges import service as challenges_service
from app.features.challenges.models import ChallengeListResult
from app.features.domovoy import service as domovoy_service
from app.features.domovoy.models import DomovoyStateRow
from app.features.pm import service as pm_service
from app.features.pm.models import (
    Mechanic,
    MechanicDecisionContext,
    MechanicDecisionReasons,
    MechanicDecisionRow,
)
from app.features.rewards import service as rewards_service
from app.features.savings import service as savings_service
from app.features.savings.models import SavingsSummary
from app.features.user_features import service as user_features_service
from app.features.user_features.models import UserFeaturesRow
from app.features.users import home, recommend
from app.features.users import service as users_service
from app.features.users.models import UserRow
from app.llm import domovoy_copy
from tests.unit.challenges.data import NO_HISTORY_FEATURES, make_challenge_row, make_user_row

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
POINTS_BALANCE = 250


def _savings_summary() -> SavingsSummary:
    return SavingsSummary(
        period="month",
        amount=Decimal("210.00"),
        previous_amount=Decimal("0"),
        delta=Decimal("210.00"),
        discount_amount=Decimal("150.00"),
        points_earned=10,
        points_spent=50,
        receipts_count=3,
        top_categories=[],
    )


def _patch_points_balance(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_points_balance(_: AsyncConnection, user_id: int) -> int:
        return POINTS_BALANCE

    monkeypatch.setattr(rewards_service, "points_balance", fake_points_balance)


def _domovoy_state() -> DomovoyStateRow:
    return DomovoyStateRow(
        user_id=1,
        xp=120,
        level=2,
        mood="cozy",
        mood_reason="",
        streak_weeks=1,
        streak_freeze_available=True,
        items=[],
        last_fed_at=None,
        updated_at=NOW,
    )


async def test_get_home_happy_path_reuses_active_hero_and_records_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user_row(user_id=1)
    hero = make_challenge_row(id=9, is_hero=True, status="active")
    domovoy_state = _domovoy_state()
    savings = _savings_summary()
    decision_calls: list[dict[str, object]] = []

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return user

    async def fake_get_state(_: AsyncConnection, user_id: int) -> DomovoyStateRow:
        return domovoy_state

    async def fake_summary(_: AsyncConnection, user_id: int, period: str) -> SavingsSummary:
        assert period == "month"
        return savings

    async def fake_get_list(_: AsyncConnection, user_id: int) -> ChallengeListResult:
        return ChallengeListResult(hero=hero, side=[], history=[])

    async def fake_refresh(_: AsyncConnection, user_id: int) -> ChallengeListResult:
        raise AssertionError("refresh_weekly must not run when a hero is already active")

    async def fake_count_completed(_: AsyncConnection, user_id: int) -> int:
        return 3

    async def fake_features_get(_: AsyncConnection, user_id: int) -> UserFeaturesRow:
        return NO_HISTORY_FEATURES

    async def fake_render_insight(*, features: UserFeaturesRow, savings: SavingsSummary) -> str:
        return "инсайт"

    async def fake_record_decision(
        _: AsyncConnection,
        *,
        user_id: int,
        mechanic: Mechanic,
        reason: str,
        context: MechanicDecisionContext,
    ) -> MechanicDecisionRow:
        decision_calls.append({"user_id": user_id, "mechanic": mechanic, "context": context})
        reasons = MechanicDecisionReasons(
            reason=reason,
            completed_challenges_count=context.completed_challenges_count,
            has_league=context.has_league,
            social_propensity=context.social_propensity,
        )
        return MechanicDecisionRow(
            id=1,
            user_id=user_id,
            mechanic=mechanic,
            reasons=reasons,
            created_at=NOW,
        )

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(domovoy_service, "get_state", fake_get_state)
    monkeypatch.setattr(savings_service, "summary", fake_summary)
    monkeypatch.setattr(challenges_service, "get_list", fake_get_list)
    monkeypatch.setattr(challenges_service, "refresh_weekly", fake_refresh)
    monkeypatch.setattr(challenges_service, "count_completed", fake_count_completed)
    monkeypatch.setattr(user_features_service, "get", fake_features_get)
    monkeypatch.setattr(domovoy_copy, "render_insight", fake_render_insight)
    monkeypatch.setattr(pm_service, "record_decision", fake_record_decision)
    _patch_points_balance(monkeypatch)

    result = await home.get_home(None, 1)  # type: ignore[arg-type]

    assert result.hero_challenge == hero
    assert result.points_balance == POINTS_BALANCE
    assert result.domovoy.xp == domovoy_state.xp
    assert result.savings == savings
    assert result.insight == "инсайт"
    assert result.referral.code == user.referral_code
    assert result.referral.invited_count == 0

    expected_mechanic = recommend.choose_mechanic(
        completed_challenges_count=3, has_league=False, social_propensity=user.social_propensity
    )
    assert result.recommended_mechanic == expected_mechanic
    assert len(decision_calls) == 1
    assert decision_calls[0]["mechanic"] == expected_mechanic.mechanic
    context = decision_calls[0]["context"]
    assert isinstance(context, MechanicDecisionContext)
    assert context.completed_challenges_count == 3
    assert context.has_league is False


async def test_get_home_refreshes_challenges_when_no_active_hero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user_row(user_id=1)
    refreshed_hero = make_challenge_row(id=42, is_hero=True, status="active")
    domovoy_state = _domovoy_state()
    savings = _savings_summary()

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return user

    async def fake_get_state(_: AsyncConnection, user_id: int) -> DomovoyStateRow:
        return domovoy_state

    async def fake_summary(_: AsyncConnection, user_id: int, period: str) -> SavingsSummary:
        return savings

    async def fake_get_list(_: AsyncConnection, user_id: int) -> ChallengeListResult:
        return ChallengeListResult(hero=None, side=[], history=[])

    async def fake_refresh(_: AsyncConnection, user_id: int) -> ChallengeListResult:
        return ChallengeListResult(hero=refreshed_hero, side=[], history=[])

    async def fake_count_completed(_: AsyncConnection, user_id: int) -> int:
        return 0

    async def fake_features_get(_: AsyncConnection, user_id: int) -> UserFeaturesRow:
        return NO_HISTORY_FEATURES

    async def fake_render_insight(*, features: UserFeaturesRow, savings: SavingsSummary) -> str:
        return "инсайт"

    async def fake_record_decision(
        _: AsyncConnection,
        *,
        user_id: int,
        mechanic: Mechanic,
        reason: str,
        context: MechanicDecisionContext,
    ) -> MechanicDecisionRow:
        reasons = MechanicDecisionReasons(
            reason=reason,
            completed_challenges_count=context.completed_challenges_count,
            has_league=context.has_league,
            social_propensity=context.social_propensity,
        )
        return MechanicDecisionRow(
            id=1,
            user_id=user_id,
            mechanic=mechanic,
            reasons=reasons,
            created_at=NOW,
        )

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(domovoy_service, "get_state", fake_get_state)
    monkeypatch.setattr(savings_service, "summary", fake_summary)
    monkeypatch.setattr(challenges_service, "get_list", fake_get_list)
    monkeypatch.setattr(challenges_service, "refresh_weekly", fake_refresh)
    monkeypatch.setattr(challenges_service, "count_completed", fake_count_completed)
    monkeypatch.setattr(user_features_service, "get", fake_features_get)
    monkeypatch.setattr(domovoy_copy, "render_insight", fake_render_insight)
    monkeypatch.setattr(pm_service, "record_decision", fake_record_decision)
    _patch_points_balance(monkeypatch)

    result = await home.get_home(None, 1)  # type: ignore[arg-type]

    assert result.hero_challenge == refreshed_hero
    assert result.recommended_mechanic.mechanic == "challenge"
    assert result.recommended_mechanic.reason == recommend.REASON_FIRST_CHALLENGE


async def test_get_home_does_not_refresh_when_side_is_still_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user_row(user_id=1)
    side = make_challenge_row(id=7, is_hero=False, status="active")
    domovoy_state = _domovoy_state()
    savings = _savings_summary()

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return user

    async def fake_get_state(_: AsyncConnection, user_id: int) -> DomovoyStateRow:
        return domovoy_state

    async def fake_summary(_: AsyncConnection, user_id: int, period: str) -> SavingsSummary:
        return savings

    async def fake_get_list(_: AsyncConnection, user_id: int) -> ChallengeListResult:
        return ChallengeListResult(hero=None, side=[side], history=[])

    async def fake_refresh(_: AsyncConnection, user_id: int) -> ChallengeListResult:
        raise AssertionError("refresh_weekly must not run while a side challenge is still active")

    async def fake_count_completed(_: AsyncConnection, user_id: int) -> int:
        return 0

    async def fake_features_get(_: AsyncConnection, user_id: int) -> UserFeaturesRow:
        return NO_HISTORY_FEATURES

    async def fake_render_insight(*, features: UserFeaturesRow, savings: SavingsSummary) -> str:
        return "инсайт"

    async def fake_record_decision(
        _: AsyncConnection,
        *,
        user_id: int,
        mechanic: Mechanic,
        reason: str,
        context: MechanicDecisionContext,
    ) -> MechanicDecisionRow:
        reasons = MechanicDecisionReasons(
            reason=reason,
            completed_challenges_count=context.completed_challenges_count,
            has_league=context.has_league,
            social_propensity=context.social_propensity,
        )
        return MechanicDecisionRow(
            id=1, user_id=user_id, mechanic=mechanic, reasons=reasons, created_at=NOW
        )

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(domovoy_service, "get_state", fake_get_state)
    monkeypatch.setattr(savings_service, "summary", fake_summary)
    monkeypatch.setattr(challenges_service, "get_list", fake_get_list)
    monkeypatch.setattr(challenges_service, "refresh_weekly", fake_refresh)
    monkeypatch.setattr(challenges_service, "count_completed", fake_count_completed)
    monkeypatch.setattr(user_features_service, "get", fake_features_get)
    monkeypatch.setattr(domovoy_copy, "render_insight", fake_render_insight)
    monkeypatch.setattr(pm_service, "record_decision", fake_record_decision)
    _patch_points_balance(monkeypatch)

    result = await home.get_home(None, 1)  # type: ignore[arg-type]

    assert result.hero_challenge is None
