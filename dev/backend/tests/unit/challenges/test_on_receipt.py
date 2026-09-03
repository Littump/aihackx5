from datetime import datetime
from decimal import Decimal
from typing import Literal

import pytest
from psycopg import AsyncConnection

from app.features.challenges import database, service
from app.features.challenges.models import ChallengeRow
from app.features.domovoy import service as domovoy_service
from app.features.domovoy.models import DomovoyStateRow
from tests.unit.challenges.data import COMPUTED_AT, make_challenge_row, make_receipt_with_items

Status = Literal["active", "completed", "failed", "expired"]


def _domovoy_state(**overrides: object) -> DomovoyStateRow:
    base: dict[str, object] = {
        "user_id": 1,
        "xp": 50,
        "level": 1,
        "mood": "bored",
        "mood_reason": "",
        "streak_weeks": 1,
        "streak_freeze_available": True,
        "items": [],
        "last_fed_at": None,
        "updated_at": COMPUTED_AT,
    }
    base.update(overrides)
    return DomovoyStateRow.model_validate(base)


async def _echo_update_progress(
    _: AsyncConnection,
    *,
    challenge_id: int,
    progress: Decimal,
    status: Status,
    completed_at: datetime | None,
) -> ChallengeRow:
    return make_challenge_row(id=challenge_id, progress=progress, status=status)


async def test_on_receipt_not_counted_skips_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_list(*args: object, **kwargs: object) -> list[ChallengeRow]:
        raise AssertionError("must not query challenges for a not counted receipt")

    monkeypatch.setattr(database, "list_active_challenges_for_period", fail_list)

    deltas = await service.on_receipt(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_with_items(),
        counted=False,
    )

    assert deltas == []


async def test_on_receipt_frequency_challenge_moves_on_any_counted_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = make_challenge_row(
        id=1, type="frequency", progress=Decimal("1"), target=Decimal("3")
    )

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime
    ) -> list[ChallengeRow]:
        return [challenge]

    async def fail_add_xp(*args: object, **kwargs: object) -> DomovoyStateRow:
        raise AssertionError("add_xp must not run before the target is reached")

    monkeypatch.setattr(database, "list_active_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", _echo_update_progress)
    monkeypatch.setattr(domovoy_service, "add_xp", fail_add_xp)

    deltas = await service.on_receipt(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_with_items(categories=["bakery"]),
        counted=True,
    )

    assert len(deltas) == 1
    assert deltas[0].progress_before == Decimal("1")
    assert deltas[0].progress_after == Decimal("2")
    assert deltas[0].completed is False
    assert deltas[0].reward_points == 0
    assert deltas[0].reward_xp == 0


CATEGORY_MATCH_CASES: list[tuple[str, list[str], bool]] = [
    ("category present moves progress", ["dairy", "bakery"], True),
    ("category absent keeps progress", ["bakery"], False),
]


@pytest.mark.parametrize("name, categories, moves", CATEGORY_MATCH_CASES)
async def test_on_receipt_category_challenge_matches_only_with_category(
    name: str, categories: list[str], moves: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    challenge = make_challenge_row(
        id=2, type="category", category="dairy", progress=Decimal("0"), target=Decimal("2")
    )

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime
    ) -> list[ChallengeRow]:
        return [challenge]

    monkeypatch.setattr(database, "list_active_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", _echo_update_progress)

    deltas = await service.on_receipt(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_with_items(categories=categories),
        counted=True,
    )

    assert (len(deltas) == 1) is moves


async def test_on_receipt_completion_rewards_hero_and_advances_streak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = make_challenge_row(
        id=3, type="frequency", is_hero=True, progress=Decimal("2"), target=Decimal("3")
    )
    add_xp_calls: list[dict[str, object]] = []
    streak_calls: list[bool] = []

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime
    ) -> list[ChallengeRow]:
        return [challenge]

    async def fake_add_xp(
        _: AsyncConnection,
        user_id: int,
        xp: int,
        *,
        kind: str,
        ref_type: str | None,
        ref_id: int | None,
        points_delta: int = 0,
    ) -> DomovoyStateRow:
        add_xp_calls.append(
            {
                "user_id": user_id,
                "xp": xp,
                "kind": kind,
                "ref_type": ref_type,
                "ref_id": ref_id,
                "points_delta": points_delta,
            }
        )
        return _domovoy_state()

    async def fake_advance_streak(
        _: AsyncConnection, user_id: int, *, completed_this_week: bool
    ) -> DomovoyStateRow:
        streak_calls.append(completed_this_week)
        return _domovoy_state()

    monkeypatch.setattr(database, "list_active_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", _echo_update_progress)
    monkeypatch.setattr(domovoy_service, "add_xp", fake_add_xp)
    monkeypatch.setattr(domovoy_service, "advance_streak", fake_advance_streak)

    deltas = await service.on_receipt(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_with_items(),
        counted=True,
    )

    assert deltas[0].completed is True
    assert deltas[0].reward_xp == 50
    assert deltas[0].reward_points == 30
    assert add_xp_calls == [
        {
            "user_id": 1,
            "xp": 50,
            "kind": "challenge",
            "ref_type": "challenge",
            "ref_id": 3,
            "points_delta": 30,
        }
    ]
    assert streak_calls == [True]


async def test_on_receipt_completion_for_side_challenge_skips_streak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = make_challenge_row(
        id=4, type="frequency", is_hero=False, progress=Decimal("2"), target=Decimal("3")
    )

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime
    ) -> list[ChallengeRow]:
        return [challenge]

    async def fake_add_xp(*args: object, **kwargs: object) -> DomovoyStateRow:
        return _domovoy_state()

    async def fail_advance_streak(*args: object, **kwargs: object) -> DomovoyStateRow:
        raise AssertionError("advance_streak must not run for a side challenge")

    monkeypatch.setattr(database, "list_active_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", _echo_update_progress)
    monkeypatch.setattr(domovoy_service, "add_xp", fake_add_xp)
    monkeypatch.setattr(domovoy_service, "advance_streak", fail_advance_streak)

    deltas = await service.on_receipt(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_with_items(),
        counted=True,
    )

    assert deltas[0].completed is True
