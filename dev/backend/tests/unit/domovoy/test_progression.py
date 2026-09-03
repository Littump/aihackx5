import pytest

from app.features.domovoy import progression
from app.features.domovoy.models import Mood
from app.features.receipts.models import ReceiptWithItems
from tests.unit.domovoy.data import MOOD_CASES, STREAK_CASES


@pytest.mark.parametrize(("xp", "expected_level"), [(0, 1), (150, 2)])
def test_level_for_xp_reuses_game_rules(xp: int, expected_level: int) -> None:
    assert progression.level_for_xp(xp) == expected_level


@pytest.mark.parametrize(("xp", "expected_to_next"), [(0, 100), (150, 150)])
def test_xp_to_next_level_reuses_game_rules(xp: int, expected_to_next: int) -> None:
    assert progression.xp_to_next_level(xp) == expected_to_next


@pytest.mark.parametrize(("name", "receipts", "expected_mood"), MOOD_CASES)
def test_mood_for_week(name: str, receipts: list[ReceiptWithItems], expected_mood: Mood) -> None:
    mood, reason = progression.mood_for_week(receipts)
    assert mood == expected_mood
    assert reason != ""


@pytest.mark.parametrize(
    ("name", "prev", "completed", "freeze_available", "expected_streak", "expected_freeze"),
    STREAK_CASES,
)
def test_next_streak(
    name: str,
    prev: int,
    completed: bool,
    freeze_available: bool,
    expected_streak: int,
    expected_freeze: bool,
) -> None:
    streak, freeze_left = progression.next_streak(prev, completed, freeze_available)
    assert streak == expected_streak
    assert freeze_left == expected_freeze
