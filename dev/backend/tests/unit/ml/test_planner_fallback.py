from app.ml import planner
from tests.unit.ml import data


async def test_no_client_uses_rule_fallback() -> None:
    result = await planner.plan_challenge(None, data.sample_planner_input())
    assert result.plan_source == "rules"
    assert result.is_valid is False
    assert len(result.offers) == 1
    offer = result.offers[0]
    assert offer.challenge_type in (
        "frequency",
        "category",
        "basket",
        "streak",
        "replenishment",
        "collection",
    )
    assert offer.reward.reward_cost_rub >= 0
