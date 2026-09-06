from app.ml import validator
from tests.unit.ml import data


def test_valid_plan_passes() -> None:
    result = validator.validate_plan(data.valid_plan(), data.sample_planner_input())
    assert result.ok, result.errors


def test_lifecycle_keyword_must_be_first() -> None:
    plan = data.valid_plan()
    plan.classification.keywords = ["has_headroom", "steady"]
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_unknown_keyword_flagged() -> None:
    plan = data.valid_plan()
    plan.classification.keywords = ["steady", "whale"]
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_extra_lifecycle_keyword_is_normalized() -> None:
    plan = data.valid_plan()
    plan.classification.keywords = ["dormant", "rising", "has_headroom"]
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert result.ok, result.errors
    assert result.normalized.classification.keywords == ["dormant", "has_headroom"]


def test_goal_direction_must_match_target() -> None:
    plan = data.valid_plan()
    plan.goal.target = "basket_value"
    plan.goal.direction = "recover"
    plan.goal.proxy = "none"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_proxy_must_serve_target() -> None:
    plan = data.valid_plan()
    plan.goal.proxy = "add_category"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_repeated_insight_kind_flagged() -> None:
    plan = data.valid_plan()
    plan.insights[1].kind = "lapsed_category"
    plan.insights[1].name = "snacks_lapsed"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_hero_mechanic_must_match_target() -> None:
    plan = data.valid_plan()
    plan.challenges[0].challenge_type = "basket"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_insight_ref_integrity_flagged() -> None:
    plan = data.valid_plan()
    plan.challenges[0].insight_ref = "ghost_insight"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_strategy_refs_must_cover_all_insights() -> None:
    plan = data.valid_plan()
    plan.general_strategy.insight_refs = ["dairy_lapsed"]
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok


def test_target_outside_corridor_flagged_and_clamped() -> None:
    plan = data.valid_plan()
    plan.challenges[0].target = 9
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok
    assert result.normalized.challenges[0].target <= 2


def test_excluded_category_flagged_and_dropped() -> None:
    plan = data.valid_plan()
    plan.challenges[0].category = "alcohol"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok
    assert result.normalized.challenges[0].category is None


def test_points_capped_to_posture() -> None:
    plan = data.valid_plan()
    plan.classification.posture = "promo_immune"
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert result.normalized.challenges[0].reward.points_level == "none"


def test_high_margin_mandate_enforced_when_on() -> None:
    plan = data.valid_plan()
    plan.challenges[1].category = "bakery"
    result = validator.validate_plan(plan, data.sample_planner_input(high_margin_mandate=True))
    assert not result.ok
    assert any("high-margin" in error for error in result.errors)


def test_high_margin_mandate_off_allows_no_high_margin() -> None:
    plan = data.valid_plan()
    plan.challenges[1].category = "bakery"
    result = validator.validate_plan(plan, data.sample_planner_input(high_margin_mandate=False))
    assert result.ok, result.errors


def test_finalize_sorts_hero_first_and_computes_reward() -> None:
    planner_input = data.sample_planner_input()
    result = validator.validate_plan(data.valid_plan(), planner_input)
    finalized = validator.finalize_plan(result.normalized, planner_input, "llm", 0)
    assert finalized.plan_source == "llm"
    assert finalized.offers[0].role == "hero"
    assert finalized.offers[0].reward.xp_amount > 0
    assert any(offer.category in data.config.HIGH_MARGIN_CATEGORIES for offer in finalized.offers)


def test_frequency_hero_rejected_for_low_cadence() -> None:
    plan = data.valid_plan()
    plan.goal.proxy = "none"
    plan.goal.direction = "increase"
    plan.challenges[0].challenge_type = "frequency"
    plan.challenges[0].category = None
    plan.challenges[0].target = 3
    result = validator.validate_plan(plan, data.sample_planner_input())
    assert not result.ok
    assert any("frequency hero invalid" in error for error in result.errors)


def test_churning_promo_immune_gets_material_points() -> None:
    planner_input = data.low_cadence_churning_input()
    plan = data.valid_plan()
    plan.classification.posture = "promo_immune"
    plan.challenges[0].reward.points_level = "high"
    result = validator.validate_plan(plan, planner_input)
    hero = next(challenge for challenge in result.normalized.challenges if challenge.role == "hero")
    assert hero.reward.points_level == "low"
