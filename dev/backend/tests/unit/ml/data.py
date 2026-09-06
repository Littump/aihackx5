from app.ml import config
from app.ml.schemas import (
    BuyerClassification,
    CategoryTimeseries,
    ChallengePlan,
    ChallengeReward,
    GeneralStrategy,
    NamedInsight,
    PlannedChallenge,
    PlannerFeatures,
    PlannerGoal,
    PlannerInput,
    PlannerUser,
    SkuCatalogItem,
)


def sample_catalog() -> list[SkuCatalogItem]:
    return [
        SkuCatalogItem(
            sku_id="DAIR-0001",
            name="Молоко 3.2% 930мл",
            category="dairy",
            brand="Простоквашино",
            regular_price=89.9,
            typical_promo_depth=0.1,
            is_challenge_eligible=True,
            popularity_rank=1,
        ),
        SkuCatalogItem(
            sku_id="SNAC-0002",
            name="Чипсы Lay's 140г",
            category="snacks",
            brand="Lay's",
            regular_price=129.0,
            typical_promo_depth=0.2,
            is_challenge_eligible=True,
            popularity_rank=2,
        ),
    ]


def sample_features() -> PlannerFeatures:
    return PlannerFeatures(
        frequency_per_week=1.3,
        recency_days=6,
        avg_basket=560.0,
        promo_sensitivity=0.48,
        cadence_days=6.5,
        churn_risk="none",
        baseline_visits=1,
        visit_momentum=1.02,
        overdue_ratio=0.92,
        cadence_regularity=0.71,
        visit_headroom_ratio=0.57,
        basket_index=0.93,
        category_breadth=2,
        top_category_overdue_ratio=2.67,
    )


def sample_timeseries() -> list[CategoryTimeseries]:
    return [
        CategoryTimeseries(
            category="dairy",
            cadence_days=6.0,
            days_overdue=10.0,
            share=0.22,
            visits=12,
            contribution_margin=config.CATEGORY_CONTRIBUTION_MARGIN["dairy"],
            is_high_margin=config.is_high_margin("dairy"),
        ),
        CategoryTimeseries(
            category="bakery",
            cadence_days=3.0,
            days_overdue=0.0,
            share=0.41,
            visits=22,
            contribution_margin=config.CATEGORY_CONTRIBUTION_MARGIN["bakery"],
            is_high_margin=config.is_high_margin("bakery"),
        ),
        CategoryTimeseries(
            category="snacks",
            cadence_days=9.0,
            days_overdue=2.0,
            share=0.12,
            visits=5,
            contribution_margin=config.CATEGORY_CONTRIBUTION_MARGIN["snacks"],
            is_high_margin=config.is_high_margin("snacks"),
        ),
    ]


def sample_planner_input(high_margin_mandate: bool = True) -> PlannerInput:
    return PlannerInput(
        user=PlannerUser(segment="regular_mid", level=3, tenure_weeks=7),
        features=sample_features(),
        favorite_categories=["dairy", "bakery", "snacks"],
        category_timeseries=sample_timeseries(),
        catalog=sample_catalog(),
        previous_plans=[],
        challenge_library=list(config.CHALLENGE_LIBRARY),
        high_margin_categories=list(config.HIGH_MARGIN_CATEGORIES),
        high_margin_mandate=high_margin_mandate,
    )


def low_cadence_churning_input() -> PlannerInput:
    features = sample_features().model_copy(
        update={
            "frequency_per_week": 0.5,
            "churn_risk": "high",
            "promo_sensitivity": 0.2,
            "recency_days": 40,
            "overdue_ratio": 3.0,
            "visit_momentum": 0.3,
        }
    )
    return PlannerInput(
        user=PlannerUser(segment="dormant", level=2, tenure_weeks=9),
        features=features,
        favorite_categories=["beauty", "dairy"],
        category_timeseries=[],
        catalog=sample_catalog(),
        previous_plans=[],
        challenge_library=list(config.CHALLENGE_LIBRARY),
        high_margin_categories=list(config.HIGH_MARGIN_CATEGORIES),
        high_margin_mandate=True,
    )


def valid_plan() -> ChallengePlan:
    return ChallengePlan(
        thinking="steady regular, dairy lapsed a full cycle; add a high-margin snacks side.",
        classification=BuyerClassification(
            keywords=["steady", "has_headroom", "dairy_lapsed", "day_to_day"],
            label="Steady Everyday Regular With A Lapsed Dairy Run",
            description="On-cadence weekly regular with headroom who let dairy lapse a cycle.",
            evidence=[
                "steady: overdue_ratio=0.92",
                "has_headroom: visit_headroom_ratio=0.57",
                "dairy_lapsed: top_category_overdue_ratio=2.67",
            ],
            posture="value_selective",
            is_ambiguous=False,
        ),
        goal=PlannerGoal(
            target="visit_frequency",
            proxy="lapsed_category_rebuy",
            direction="recover",
            rationale="dairy overdue (top_category_overdue_ratio=2.67); the re-buy is the trip",
        ),
        insights=[
            NamedInsight(
                name="dairy_lapsed",
                kind="lapsed_category",
                behaviour="buys dairy every ~6d but none for 16d",
                dod="re-buys dairy within a week",
                strategy_hint="replenishment on dairy, target 1",
                evidence_metric="top_category_overdue_ratio=2.67",
            ),
            NamedInsight(
                name="visit_headroom",
                kind="visit_headroom",
                behaviour="visits ~1.3/wk with room for one more",
                dod="one extra visit this week",
                strategy_hint="frequency, target baseline+1",
                evidence_metric="visit_headroom_ratio=0.57",
            ),
            NamedInsight(
                name="snacks_high_margin",
                kind="high_margin_push",
                behaviour="snacks is a high-margin category they touch sometimes",
                dod="tries a snacks pairing to lift margin per trip",
                strategy_hint="collection on snacks, XP-led side",
                evidence_metric="contribution_margin=0.3",
            ),
        ],
        challenges=[
            PlannedChallenge(
                role="hero",
                insight_ref="dairy_lapsed",
                challenge_type="replenishment",
                category="dairy",
                target=1,
                reward=ChallengeReward(xp_level="medium", points_level="medium"),
                rationale="dairy 10d overdue on a 6d cycle - a timely re-buy trip",
            ),
            PlannedChallenge(
                role="side",
                insight_ref="snacks_high_margin",
                challenge_type="collection",
                category="snacks",
                target=1,
                reward=ChallengeReward(xp_level="low", points_level="none"),
                rationale="high-margin snacks (margin 0.3) to earn more per trip, XP-led",
            ),
        ],
        general_strategy=GeneralStrategy(
            insight_refs=["dairy_lapsed", "visit_headroom", "snacks_high_margin"],
            rationale="Recover visit_frequency via the lapsed dairy re-buy; XP-led snacks side "
            "satisfies the high-margin mandate.",
            next_week_hint="if dairy completes, switch hero to plain visit_headroom.",
        ),
    )
