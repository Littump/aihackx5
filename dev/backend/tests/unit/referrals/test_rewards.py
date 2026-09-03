from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo

import pytest

from app.features.referrals import rewards
from app.game_rules import TIMEZONE
from tests.unit.referrals.data import make_referral_row

TZ = ZoneInfo(TIMEZONE)

RewardCase = tuple[Literal["new", "dormant", "active"], int, int, int]
REWARD_TABLE_CASES: list[RewardCase] = [
    ("new", 200, 150, 100),
    ("dormant", 150, 150, 100),
    ("active", 0, 0, 0),
]


@pytest.mark.parametrize("kind, referee_points, referrer_points, referrer_xp", REWARD_TABLE_CASES)
def test_rewards_for_matches_domain_rules_table(
    kind: Literal["new", "dormant", "active"],
    referee_points: int,
    referrer_points: int,
    referrer_xp: int,
) -> None:
    reward = rewards.rewards_for(kind)

    assert reward["referee_first_purchase_points"] == referee_points
    assert reward["referrer_reward_points"] == referrer_points
    assert reward["referrer_reward_xp"] == referrer_xp


PURCHASES_DONE_CASES: list[tuple[dict[str, object], int]] = [
    ({}, 0),
    ({"first_purchase_at": datetime(2026, 9, 1, tzinfo=UTC)}, 1),
    (
        {
            "first_purchase_at": datetime(2026, 9, 1, tzinfo=UTC),
            "second_purchase_at": datetime(2026, 9, 8, tzinfo=UTC),
        },
        2,
    ),
]


@pytest.mark.parametrize("overrides, expected", PURCHASES_DONE_CASES)
def test_purchases_done_counts_completed_milestones(
    overrides: dict[str, object], expected: int
) -> None:
    referral = make_referral_row(**overrides)

    assert rewards.purchases_done(referral) == expected


def test_to_invitee_view_hides_identity_and_numbers_label() -> None:
    referral = make_referral_row(status="rewarded", referrer_reward_points=150)

    view = rewards.to_invitee_view(referral, 3)

    assert view.label == "Сосед №3"
    assert view.reward_points == 150
    assert "id" not in view.model_dump()
    assert "pseudonym" not in view.model_dump()


def test_to_invitee_view_hides_reward_points_when_not_rewarded() -> None:
    referral = make_referral_row(status="qualified", referrer_reward_points=150)

    view = rewards.to_invitee_view(referral, 1)

    assert view.reward_points == 0


def test_referral_link_embeds_code() -> None:
    assert rewards.referral_link("ABC123") == "https://x5.club/r/ABC123"


def test_rules_text_mentions_threshold_and_min_days() -> None:
    text = " ".join(rewards.rules_text())

    assert "500" in text
    assert "7" in text


def test_month_bounds_returns_first_day_of_month_range() -> None:
    start, end = rewards.month_bounds(datetime(2026, 9, 15, 10, tzinfo=UTC))

    assert (start.year, start.month, start.day) == (2026, 9, 1)
    assert (end.year, end.month, end.day) == (2026, 10, 1)


def test_month_bounds_wraps_december_into_next_year() -> None:
    _, end = rewards.month_bounds(datetime(2026, 12, 20, tzinfo=UTC))

    assert (end.year, end.month, end.day) == (2027, 1, 1)


def test_year_bounds_returns_full_calendar_year() -> None:
    start, end = rewards.year_bounds(datetime(2026, 6, 1, tzinfo=UTC))

    assert start == datetime(2026, 1, 1, tzinfo=TZ)
    assert end == datetime(2027, 1, 1, tzinfo=TZ)
