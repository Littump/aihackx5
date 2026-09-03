import pytest

from app.core.errors import AppError
from app.features.challenges import personalization
from tests.unit.challenges.data import make_draft


def test_rank_picks_highest_priority_as_hero() -> None:
    low = make_draft(type="frequency", priority=1.0)
    high = make_draft(type="category", category="dairy", priority=1.4)
    mid = make_draft(type="category", category="bakery", priority=1.2)

    hero, side = personalization.rank([low, mid, high])

    assert hero is high
    assert side == [mid, low]


def test_rank_limits_side_to_two() -> None:
    hero = make_draft(type="frequency", priority=2.0)
    candidates = [
        make_draft(type="category", category=f"cat{i}", priority=1.0 + i / 10) for i in range(4)
    ]

    _, side = personalization.rank([hero, *candidates])

    assert len(side) == 2
    assert [d.priority for d in side] == sorted((d.priority for d in candidates), reverse=True)[:2]


def test_rank_excludes_side_candidate_matching_hero_slot() -> None:
    hero = make_draft(type="category", category="dairy", priority=2.0)
    same_as_hero = make_draft(type="category", category="dairy", priority=1.8)
    other = make_draft(type="category", category="bakery", priority=1.5)

    _, side = personalization.rank([hero, same_as_hero, other])

    assert same_as_hero not in side
    assert side == [other]


def test_rank_defensive_dedup_drops_duplicate_side_slots() -> None:
    hero = make_draft(type="frequency", priority=3.0)
    first = make_draft(type="category", category="dairy", priority=2.0)
    duplicate = make_draft(type="category", category="dairy", priority=1.9)
    third = make_draft(type="category", category="bakery", priority=1.5)

    _, side = personalization.rank([hero, first, duplicate, third])

    assert side == [first, third]


def test_rank_raises_app_error_on_empty_drafts() -> None:
    with pytest.raises(AppError) as excinfo:
        personalization.rank([])

    assert excinfo.value.code == "no_challenge_candidates"
    assert excinfo.value.status == 500
