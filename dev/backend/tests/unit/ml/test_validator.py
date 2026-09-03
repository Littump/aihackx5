from app.ml import validator
from tests.unit.ml import data


def test_valid_plan_passes() -> None:
    result = validator.validate_plan(data.valid_plan(), data.sample_planner_input())
    assert result.ok


def test_unknown_sku_flagged() -> None:
    plan = data.valid_plan()
    plan.steps[0].sku_refs = ["DOES-NOT-EXIST"]
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok
    assert result.normalized.steps[0].sku_refs == []


def test_target_outside_corridor_flagged_and_clamped() -> None:
    plan = data.valid_plan()
    plan.steps[0].target = 9
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok
    assert result.normalized.steps[0].target <= 2


def test_excluded_category_flagged() -> None:
    plan = data.valid_plan()
    plan.steps[0].category = "alcohol"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok
    assert result.normalized.steps[0].category is None


def test_reward_kind_none_requires_level_none() -> None:
    plan = data.valid_plan()
    plan.steps[0].reward_kind = "none"
    plan.steps[0].reward_level = "high"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok
    assert result.normalized.steps[0].reward_level == "none"


def test_rationale_without_number_flagged() -> None:
    plan = data.valid_plan()
    plan.rationale = "Хороший челлендж без единой цифры из инсайта."
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_finalize_builds_offer_with_reward() -> None:
    planner_input = data.sample_planner_input()
    result = validator.validate_plan(data.valid_plan(), planner_input)
    finalized = validator.finalize_plan(result.normalized, planner_input, "llm", 0)
    assert finalized.plan_source == "llm"
    assert finalized.offers[0].reward.reward_points >= 0
