from app.ml.schemas import (
    CategoryTimeseries,
    ChallengePlan,
    ChallengeStep,
    PlannerFeatures,
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
            sku_id="BAKE-0002",
            name="Хлеб бородинский",
            category="bakery",
            brand="Коломенское",
            regular_price=54.0,
            typical_promo_depth=0.15,
            is_challenge_eligible=True,
            popularity_rank=1,
        ),
    ]


def sample_planner_input() -> PlannerInput:
    return PlannerInput(
        user=PlannerUser(segment="regular_mid", level=3, tenure_weeks=7),
        features=PlannerFeatures(
            frequency_per_week=1.8,
            recency_days=11,
            avg_basket=590.0,
            promo_sensitivity=0.32,
            cadence_days=5.5,
            churn_risk="elevated",
            baseline_visits=2,
        ),
        category_timeseries=[
            CategoryTimeseries(
                category="dairy", cadence_days=5.5, days_overdue=5.0, share=0.22, visits=9
            ),
        ],
        catalog=sample_catalog(),
        previous_plans=[],
        challenge_library=[
            "frequency",
            "category",
            "basket",
            "streak",
            "replenishment",
            "collection",
        ],
    )


def valid_step() -> ChallengeStep:
    return ChallengeStep(
        challenge_type="replenishment",
        target=1,
        category="dairy",
        sku_refs=["DAIR-0001"],
        reward_kind="promo",
        reward_level="medium",
        deadline_days=7,
    )


def valid_plan() -> ChallengePlan:
    return ChallengePlan(
        steps=[valid_step()],
        insight_used=["days_overdue", "churn_risk"],
        rationale="Молочка просрочена на 5 дней при кадэнсе 5.5, нужен возврат к рутине.",
    )
