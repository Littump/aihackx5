from decimal import Decimal

from app.ml import economics


def test_po_example_reward_levels() -> None:
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


def test_promo_reward_computation() -> None:
    reward = economics.compute_reward(
        baseline=2,
        target=3,
        avg_basket=600.0,
        reward_kind="promo",
        reward_level="high",
        level=3,
        tenure_weeks=7,
    )
    assert reward.reward_points == 30
    assert reward.ladder_bonus_xp == 0
    assert reward.reward_cost_rub > 0


def test_ladder_spends_no_promo_money() -> None:
    reward = economics.compute_reward(
        baseline=2,
        target=3,
        avg_basket=600.0,
        reward_kind="ladder",
        reward_level="high",
        level=1,
        tenure_weeks=1,
    )
    assert reward.reward_points == 0
    assert reward.reward_cost_rub == 0.0
    assert reward.ladder_bonus_xp > 0


def test_ladder_rewards_newbies_more_than_veterans() -> None:
    newbie = economics.ladder_bonus_xp("high", level=1, tenure_weeks=1)
    veteran = economics.ladder_bonus_xp("high", level=9, tenure_weeks=40)
    assert newbie > veteran


def test_none_kind_pays_nothing() -> None:
    reward = economics.compute_reward(
        baseline=1,
        target=2,
        avg_basket=500.0,
        reward_kind="none",
        reward_level="none",
        level=2,
        tenure_weeks=3,
    )
    assert reward.reward_points == 0
    assert reward.ladder_bonus_xp == 0
    assert reward.reward_cost_rub == 0.0
