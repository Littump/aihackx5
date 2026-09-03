import pytest

from app.features.achievements.models import AchievementContext
from app.features.achievements.rules import evaluate
from tests.unit.achievements.data import EVALUATE_CASES


@pytest.mark.parametrize(
    ("case_id", "ctx", "expected"),
    EVALUATE_CASES,
    ids=[case[0] for case in EVALUATE_CASES],
)
def test_evaluate_matches_expected_codes(
    case_id: str, ctx: AchievementContext, expected: list[str]
) -> None:
    assert evaluate(ctx) == expected
