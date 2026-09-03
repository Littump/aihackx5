import pytest

from app import game_rules
from tests.unit.game_rules_data import (
    EXPECTED_CONSTANTS,
    LEVEL_FOR_XP_CASES,
    XP_TO_NEXT_LEVEL_CASES,
)


@pytest.mark.parametrize(("name", "expected"), EXPECTED_CONSTANTS)
def test_constant_matches_domain_rules(name: str, expected: object) -> None:
    assert getattr(game_rules, name) == expected


@pytest.mark.parametrize(("xp", "expected_level"), LEVEL_FOR_XP_CASES)
def test_level_for_xp(xp: int, expected_level: int) -> None:
    assert game_rules.level_for_xp(xp) == expected_level


@pytest.mark.parametrize(("xp", "expected_to_next"), XP_TO_NEXT_LEVEL_CASES)
def test_xp_to_next_level(xp: int, expected_to_next: int) -> None:
    assert game_rules.xp_to_next_level(xp) == expected_to_next


def test_receipt_strong_signals_sum_reaches_block_threshold() -> None:
    strong_weights = [
        signal["weight"] for signal in game_rules.RECEIPT_SIGNALS.values() if signal["strong"]
    ]
    assert sum(strong_weights) >= game_rules.FRAUD_BLOCK_THRESHOLD
