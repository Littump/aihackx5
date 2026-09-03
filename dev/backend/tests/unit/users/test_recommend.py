from decimal import Decimal
from typing import Literal

import pytest

from app.features.users import recommend
from app.features.users.models import RecommendedMechanicRow

Mechanic = Literal["challenge", "league", "referral"]

CASES: list[tuple[int, bool, str, Mechanic, str]] = [
    (0, False, "0", "challenge", recommend.REASON_FIRST_CHALLENGE),
    (0, True, "1", "challenge", recommend.REASON_FIRST_CHALLENGE),
    (3, True, "0", "league", recommend.REASON_LEAGUE),
    (2, True, "0", "challenge", recommend.REASON_DEFAULT),
    (3, False, "0", "challenge", recommend.REASON_DEFAULT),
    (2, False, "0.6", "referral", recommend.REASON_REFERRAL),
    (2, False, "0.59", "challenge", recommend.REASON_DEFAULT),
    (1, False, "0.9", "challenge", recommend.REASON_DEFAULT),
    (3, True, "0.9", "league", recommend.REASON_LEAGUE),
    (2, True, "0.9", "referral", recommend.REASON_REFERRAL),
]


@pytest.mark.parametrize(
    ("completed", "has_league", "propensity", "expected_mechanic", "expected_reason"), CASES
)
def test_choose_mechanic(
    completed: int,
    has_league: bool,
    propensity: str,
    expected_mechanic: Mechanic,
    expected_reason: str,
) -> None:
    result = recommend.choose_mechanic(
        completed_challenges_count=completed,
        has_league=has_league,
        social_propensity=Decimal(propensity),
    )

    assert result == RecommendedMechanicRow(mechanic=expected_mechanic, reason=expected_reason)
