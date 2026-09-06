from app.ml import config, insight
from app.ml.schemas import CategoryTimeseries, PlannerInput, ShopVisit


def _series(category: str, share: float, days_overdue: float, visits: int) -> CategoryTimeseries:
    return CategoryTimeseries(
        category=category,
        cadence_days=7.0,
        days_overdue=days_overdue,
        share=share,
        visits=visits,
        contribution_margin=config.CONTRIBUTION_MARGIN,
        is_high_margin=config.is_high_margin(category),
    )


def test_fresh_staple_reads_as_staple() -> None:
    series = [_series("dairy", share=0.5, days_overdue=0.0, visits=9)]
    habits = insight.shopping_habits(series, ["dairy"])
    assert habits[0].cadence_class == "staple"


def test_overdue_staple_reads_as_lapsed() -> None:
    series = [_series("dairy", share=0.5, days_overdue=30.0, visits=9)]
    habits = insight.shopping_habits(series, ["dairy"])
    assert habits[0].cadence_class == "lapsed"


def test_lapsed_requires_gap_and_enough_visits() -> None:
    series = [_series("bakery", share=0.25, days_overdue=14.0, visits=3)]
    habits = insight.shopping_habits(series, ["bakery"])
    assert habits[0].cadence_class == "lapsed"


def test_regular_when_present_but_not_overdue() -> None:
    series = [_series("bakery", share=0.25, days_overdue=0.0, visits=3)]
    habits = insight.shopping_habits(series, ["bakery"])
    assert habits[0].cadence_class == "regular"


def test_thin_history_is_not_lapsed() -> None:
    series = [_series("meat_fish", share=0.2, days_overdue=20.0, visits=2)]
    habits = insight.shopping_habits(series, ["meat_fish"])
    assert habits[0].cadence_class == "regular"


def test_missing_favourite_is_occasional() -> None:
    habits = insight.shopping_habits([], ["fruits_veg"])
    assert habits[0].cadence_class == "occasional"
    assert habits[0].share == 0.0


def test_habits_follow_favourite_order() -> None:
    series = [
        _series("dairy", share=0.5, days_overdue=0.0, visits=9),
        _series("bakery", share=0.25, days_overdue=14.0, visits=3),
    ]
    habits = insight.shopping_habits(series, ["bakery", "dairy", "snacks"])
    assert [habit.category for habit in habits] == ["bakery", "dairy", "snacks"]
    assert habits[0].cadence_class == "lapsed"
    assert habits[1].cadence_class == "staple"
    assert habits[2].cadence_class == "occasional"


def test_single_visit_high_share_is_not_staple() -> None:
    series = [_series("fruits_veg", share=1.0, days_overdue=0.0, visits=1)]
    habits = insight.shopping_habits(series, ["fruits_veg"])
    assert habits[0].cadence_class == "regular"


def _build(visits: list[ShopVisit], favs: list[str]) -> PlannerInput:
    from app.ml.schemas import PurchaseHistory, UserProfile

    profile = UserProfile(
        profile_id="PTEST",
        segment="regular_mid",
        persona_label="test",
        persona_brief="test",
        archetype="test",
        deal_attitude="selective",
        routine_rigidity=0.5,
        level=1,
        tenure_weeks=10,
        visits_per_week=2.0,
        avg_basket=500.0,
        promo_sensitivity=0.5,
        favorite_categories=favs,
        category_weights={c: 1.0 for c in favs},
        offer_responsiveness=0.5,
    )
    return insight.build_insight(profile, PurchaseHistory(horizon_weeks=6, visits=visits), [], [])


def test_active_staple_overdue_is_zeroed() -> None:
    visits = [ShopVisit(day_index=d, categories=["dairy"], basket=500.0) for d in (20, 23, 26, 29)]
    visits += [ShopVisit(day_index=d, categories=["snacks"], basket=500.0) for d in (35, 38, 41)]
    planner_input = _build(visits, ["dairy"])
    dairy = next(s for s in planner_input.category_timeseries if s.category == "dairy")
    assert dairy.share >= config.STAPLE_SHARE_MIN
    assert planner_input.features.churn_risk == "none"
    assert dairy.days_overdue == 0.0


def test_lapsed_staple_overdue_is_preserved() -> None:
    visits = [
        ShopVisit(day_index=d, categories=["dairy"], basket=500.0)
        for d in (0, 3, 6, 9, 12, 15, 18, 21)
    ]
    visits.append(ShopVisit(day_index=1, categories=["snacks"], basket=500.0))
    planner_input = _build(visits, ["dairy"])
    dairy = next(s for s in planner_input.category_timeseries if s.category == "dairy")
    habits = insight.shopping_habits(planner_input.category_timeseries, ["dairy"])
    assert dairy.share >= config.STAPLE_SHARE_MIN
    assert planner_input.features.churn_risk != "none"
    assert dairy.days_overdue > 0.0
    assert habits[0].cadence_class == "lapsed"
