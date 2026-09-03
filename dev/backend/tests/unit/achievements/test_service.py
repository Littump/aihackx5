from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.achievements import database as achievements_db
from app.features.achievements import service
from app.features.achievements.models import AchievementRow
from app.features.challenges.models import ChallengeProgressDelta
from app.features.domovoy import service as domovoy_service
from app.features.domovoy.models import DomovoyStateRow
from app.game_rules import ACHIEVEMENT_CODES

UNLOCKED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def test_achievement_titles_cover_exactly_the_game_rules_codes() -> None:
    assert set(service.ACHIEVEMENT_TITLES) == set(ACHIEVEMENT_CODES)


def _completed_delta() -> ChallengeProgressDelta:
    return ChallengeProgressDelta(
        challenge_id=1,
        progress_before=Decimal("1"),
        progress_after=Decimal("2"),
        target=Decimal("2"),
        completed=True,
        reward_points=0,
        reward_xp=0,
    )


def _active_delta() -> ChallengeProgressDelta:
    return ChallengeProgressDelta(
        challenge_id=2,
        progress_before=Decimal("0"),
        progress_after=Decimal("1"),
        target=Decimal("2"),
        completed=False,
        reward_points=0,
        reward_xp=0,
    )


async def test_on_challenge_completed_returns_empty_when_nothing_completed() -> None:
    result = await service.on_challenge_completed(None, 1, [_active_delta()])  # type: ignore[arg-type]

    assert result == []


async def test_on_challenge_completed_unlocks_first_challenge_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_insert(_: AsyncConnection, *, user_id: int, code: str) -> AchievementRow | None:
        assert user_id == 1
        assert code == "first_challenge"
        return AchievementRow(id=1, user_id=1, code=code, unlocked_at=UNLOCKED_AT)

    async def fake_add_xp(*args: object, **kwargs: object) -> DomovoyStateRow:
        return DomovoyStateRow(
            user_id=1,
            xp=25,
            level=1,
            mood="cozy",
            mood_reason="",
            streak_weeks=0,
            streak_freeze_available=True,
            items=[],
            last_fed_at=None,
            updated_at=UNLOCKED_AT,
        )

    monkeypatch.setattr(achievements_db, "insert_achievement", fake_insert)
    monkeypatch.setattr(domovoy_service, "add_xp", fake_add_xp)

    result = await service.on_challenge_completed(
        None,  # type: ignore[arg-type]
        1,
        [_completed_delta()],
    )

    assert result == ["first_challenge"]


async def test_on_challenge_completed_skips_already_unlocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_insert_conflict(
        _: AsyncConnection, *, user_id: int, code: str
    ) -> AchievementRow | None:
        return None

    monkeypatch.setattr(achievements_db, "insert_achievement", fake_insert_conflict)

    result = await service.on_challenge_completed(
        None,  # type: ignore[arg-type]
        1,
        [_completed_delta()],
    )

    assert result == []
