from decimal import Decimal

from app.ml import economics


def test_reward_points_scale_with_level() -> None:
    budget = economics.max_reward_rub(baseline=2, target=3, avg_basket=600.0)
    assert budget == Decimal("36.00")
    assert economics.reward_points_for_level(budget, "high") == 30
    assert economics.reward_points_for_level(budget, "medium") == 20
    assert economics.reward_points_for_level(budget, "low") == 10
    assert economics.reward_points_for_level(budget, "none") == 0


def test_reward_never_exceeds_margin_cap() -> None:
    budget = economics.max_reward_rub(baseline=2, target=4, avg_basket=1200.0)
    points = economics.reward_points_for_level(budget, "high")
    assert points <= float(budget)
    assert points <= 150


def test_two_currency_reward_pays_points_and_xp() -> None:
    reward = economics.compute_reward(
        baseline=2,
        target=3,
        avg_basket=600.0,
        xp_level="high",
        points_level="high",
        level=3,
        tenure_weeks=7,
    )
    assert reward.reward_points == 30
    assert reward.xp_amount > 0
    assert reward.reward_cost_rub > 0
    assert reward.points_level == "high"


def test_points_below_minimum_drop_to_none() -> None:
    reward = economics.compute_reward(
        baseline=1,
        target=2,
        avg_basket=300.0,
        xp_level="low",
        points_level="high",
        level=3,
        tenure_weeks=7,
    )
    assert reward.reward_points == 0
    assert reward.points_level == "none"
    assert reward.reward_cost_rub == 0.0
    assert reward.xp_amount > 0


def test_xp_is_always_on_even_with_no_points() -> None:
    reward = economics.compute_reward(
        baseline=1,
        target=2,
        avg_basket=500.0,
        xp_level="medium",
        points_level="none",
        level=2,
        tenure_weeks=3,
    )
    assert reward.reward_points == 0
    assert reward.reward_cost_rub == 0.0
    assert reward.xp_amount > 0


def test_xp_rewards_newbies_more_than_veterans() -> None:
    newbie = economics.xp_amount("high", level=1, tenure_weeks=1)
    veteran = economics.xp_amount("high", level=9, tenure_weeks=40)
    assert newbie > veteran
