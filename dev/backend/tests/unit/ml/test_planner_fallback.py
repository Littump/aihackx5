from app.ml import config, planner
from tests.unit.ml import data


async def test_no_client_uses_rule_fallback() -> None:
    result = await planner.plan_challenge(None, data.sample_planner_input())
    assert result.plan_source == "rules"
    assert result.is_valid is False
    assert len(result.offers) >= 1
    assert result.offers[0].role == "hero"
    for offer in result.offers:
        assert offer.challenge_type in (
            "frequency",
            "category",
            "basket",
            "replenishment",
            "collection",
        )
        assert offer.reward.reward_cost_rub >= 0
    assert any(config.is_high_margin(offer.category) for offer in result.offers)


def test_frequency_mechanic_gate_by_cadence() -> None:
    from app.ml import rules

    low = data.sample_features().model_copy(update={"frequency_per_week": 1.3})
    high = data.sample_features().model_copy(update={"frequency_per_week": 2.5})
    assert rules.frequency_mechanic_ok(low) is False
    assert rules.frequency_mechanic_ok(high) is True


def test_churn_aware_reward_ceiling() -> None:
    from app.ml import rules

    assert rules.reward_for("recover", "promo_immune", "high").points_level == "low"
    assert rules.reward_for("recover", "promo_immune", "none").points_level == "none"
    assert rules.reward_for("recover", "value_selective", "high").points_level == "medium"


async def test_low_cadence_dormant_fallback_avoids_raw_frequency() -> None:
    planner_input = data.low_cadence_churning_input()
    result = await planner.plan_challenge(None, planner_input)
    hero = next(offer for offer in result.offers if offer.role == "hero")
    assert hero.challenge_type != "frequency"
    assert hero.target == 1


def test_high_margin_pick_avoids_staple() -> None:
    from app.ml import config, rules
    from app.ml.schemas import CategoryTimeseries

    high_margin = next(iter(config.HIGH_MARGIN_CATEGORIES))
    other_high_margin = next(
        category for category in config.HIGH_MARGIN_CATEGORIES if category != high_margin
    )
    planner_input = data.sample_planner_input().model_copy(
        update={
            "category_timeseries": [
                CategoryTimeseries(
                    category=high_margin,
                    cadence_days=4.0,
                    days_overdue=0.0,
                    share=0.6,
                    visits=30,
                    contribution_margin=config.CATEGORY_CONTRIBUTION_MARGIN.get(
                        high_margin, config.CONTRIBUTION_MARGIN
                    ),
                    is_high_margin=True,
                ),
                CategoryTimeseries(
                    category=other_high_margin,
                    cadence_days=12.0,
                    days_overdue=1.0,
                    share=0.15,
                    visits=6,
                    contribution_margin=config.CATEGORY_CONTRIBUTION_MARGIN.get(
                        other_high_margin, config.CONTRIBUTION_MARGIN
                    ),
                    is_high_margin=True,
                ),
            ]
        }
    )
    assert rules.high_margin_pick(planner_input) == other_high_margin
