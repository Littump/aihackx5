from app.features.rewards import catalog
from app.game_rules import (
    REFERRAL_REWARDS,
    REWARD_POINTS_MAX_WEEKLY,
    REWARD_POINTS_MIN,
    XP_CHALLENGE,
    XP_RECEIPT,
    XP_REFERRAL,
)

EXPECTED_CODES = [
    "receipt",
    "challenge",
    "streak",
    "league_promotion",
    "league_top3",
    "referral",
    "achievement",
]


def test_earning_rules_cover_every_reward_source() -> None:
    assert [rule.code for rule in catalog.earning_rules()] == EXPECTED_CODES


def test_earning_rules_mirror_game_rules_numbers() -> None:
    by_code = {rule.code: rule for rule in catalog.earning_rules()}
    assert by_code["receipt"].xp == XP_RECEIPT
    assert by_code["receipt"].points_max == 0
    assert by_code["challenge"].xp == XP_CHALLENGE
    assert by_code["challenge"].points_min == REWARD_POINTS_MIN
    assert by_code["challenge"].points_max == REWARD_POINTS_MAX_WEEKLY


def test_referral_rule_takes_points_from_paid_referral_kinds() -> None:
    by_code = {rule.code: rule for rule in catalog.earning_rules()}
    paid = REFERRAL_REWARDS["new"]["referrer_reward_points"]
    assert by_code["referral"].xp == XP_REFERRAL
    assert by_code["referral"].points_min == paid
    assert by_code["referral"].points_max == paid


def test_event_titles_exist_for_every_ledger_kind() -> None:
    assert set(catalog.EVENT_TITLES) == {
        "receipt_xp",
        "challenge",
        "streak",
        "league",
        "referral",
        "achievement",
    }
