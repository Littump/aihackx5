from decimal import Decimal

import pytest

from app.features.league import scoring
from app.features.league.models import LeagueZone
from tests.unit.league.data import CUTOFF_CASES, NEXT_DIVISION_CASES, WEEK_SCORE_CASES, ZONE_CASES


@pytest.mark.parametrize(
    ("week_savings", "week_regular_total", "completed", "streak", "receipts", "expected"),
    WEEK_SCORE_CASES,
)
def test_week_score_matches_domain_rules_cases(
    week_savings: Decimal,
    week_regular_total: Decimal,
    completed: int,
    streak: int,
    receipts: int,
    expected: int,
) -> None:
    score = scoring.week_score(
        week_savings=week_savings,
        week_regular_total=week_regular_total,
        completed_challenges=completed,
        streak_weeks=streak,
        counted_receipts=receipts,
    )
    assert score == expected


def test_week_score_ac_example_equals_124() -> None:
    score = scoring.week_score(
        week_savings=Decimal("120"),
        week_regular_total=Decimal("1000"),
        completed_challenges=1,
        streak_weeks=3,
        counted_receipts=4,
    )
    assert score == 124


@pytest.mark.parametrize(("size", "expected_promotion", "expected_demotion"), CUTOFF_CASES)
def test_cutoffs_match_domain_rules(
    size: int, expected_promotion: int, expected_demotion: int
) -> None:
    assert scoring.promotion_cutoff(size) == expected_promotion
    assert scoring.demotion_cutoff(size) == expected_demotion


@pytest.mark.parametrize(("rank", "size", "division", "expected_zone"), ZONE_CASES)
def test_zone_for_rank_matches_domain_rules(
    rank: int, size: int, division: int, expected_zone: str
) -> None:
    assert scoring.zone_for_rank(rank=rank, size=size, division=division) == expected_zone


@pytest.mark.parametrize(("division", "zone", "expected"), NEXT_DIVISION_CASES)
def test_next_division_clamps_to_1_and_5(division: int, zone: LeagueZone, expected: int) -> None:
    assert scoring.next_division(division=division, zone=zone) == expected
