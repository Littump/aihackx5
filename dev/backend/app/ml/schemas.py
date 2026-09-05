from typing import Literal

from pydantic import BaseModel, Field

Segment = Literal["regular_mid", "light", "heavy", "dormant"]
ChurnRisk = Literal["none", "elevated", "high"]
ChallengeType = Literal["frequency", "category", "basket", "streak", "replenishment", "collection"]
RewardKind = Literal["promo", "ladder", "none"]
RewardLevel = Literal["none", "low", "medium", "high"]
PlanSource = Literal["llm", "rules"]
Branch = Literal["control_x5", "treatment_llm", "treatment_rules"]
PromoDecision = Literal["use_offer", "buy_as_usual", "ignore"]
DealAttitude = Literal["promo_skeptic", "selective", "deal_seeker"]


class SkuCatalogItem(BaseModel):
    sku_id: str
    name: str
    category: str
    brand: str | None
    regular_price: float
    typical_promo_depth: float
    is_challenge_eligible: bool
    popularity_rank: int


class ScrapedCatalog(BaseModel):
    source: str
    scraped_at: str
    count: int
    items: list[SkuCatalogItem]


class ShopVisit(BaseModel):
    day_index: int
    categories: list[str]
    basket: float


class PurchaseHistory(BaseModel):
    horizon_weeks: int
    visits: list[ShopVisit]


class UserProfile(BaseModel):
    profile_id: str
    segment: Segment
    persona_label: str
    archetype: str
    persona_brief: str
    deal_attitude: DealAttitude
    routine_rigidity: float
    level: int
    tenure_weeks: int
    visits_per_week: float
    avg_basket: float
    promo_sensitivity: float
    category_weights: dict[str, float]
    favorite_categories: list[str]
    offer_responsiveness: float


class CategoryTimeseries(BaseModel):
    category: str
    cadence_days: float
    days_overdue: float
    share: float
    visits: int


class PreviousPlan(BaseModel):
    week: int
    challenge_type: ChallengeType
    reward_kind: RewardKind
    reward_level: RewardLevel
    status: Literal["completed", "expired", "active"]
    used: bool


class PlannerUser(BaseModel):
    segment: Segment
    level: int
    tenure_weeks: int


class PlannerFeatures(BaseModel):
    frequency_per_week: float
    recency_days: int
    avg_basket: float
    promo_sensitivity: float
    cadence_days: float
    churn_risk: ChurnRisk
    baseline_visits: int


class PlannerInput(BaseModel):
    user: PlannerUser
    features: PlannerFeatures
    category_timeseries: list[CategoryTimeseries]
    catalog: list[SkuCatalogItem]
    previous_plans: list[PreviousPlan]
    challenge_library: list[str]


class ChallengeStep(BaseModel):
    challenge_type: ChallengeType
    target: int
    category: str | None
    sku_refs: list[str] = Field(default_factory=list, max_length=3)
    reward_kind: RewardKind
    reward_level: RewardLevel
    deadline_days: int


class ChallengePlan(BaseModel):
    steps: list[ChallengeStep] = Field(min_length=1, max_length=2)
    insight_used: list[str] = Field(default_factory=list)
    rationale: str = Field(max_length=400)


class RewardComputation(BaseModel):
    reward_kind: RewardKind
    reward_level: RewardLevel
    max_reward_rub: float
    reward_points: int
    ladder_bonus_xp: int
    reward_cost_rub: float


class ChallengeOffer(BaseModel):
    plan_step: int
    challenge_type: ChallengeType
    category: str | None
    baseline: int
    target: int
    sku_refs: list[str]
    deadline_days: int
    reward: RewardComputation
    rationale: str


class ValidatedPlan(BaseModel):
    offers: list[ChallengeOffer]
    plan_source: PlanSource
    is_valid: bool
    repair_count: int
    insight_used: list[str]


class OfferResponse(BaseModel):
    thinking: str = Field(max_length=1200)
    promo_decision: PromoDecision
    extra_visits: int = Field(ge=0, le=6)
    completed_challenge: bool
    rationale: str = Field(max_length=400)

    @property
    def engaged(self) -> bool:
        return self.promo_decision == "use_offer"


class BranchOutcome(BaseModel):
    branch: Branch
    plan_source: PlanSource
    baseline_tail_visits: int
    tail_visits: int
    incremental_visits: int
    incremental_revenue_rub: float
    incremental_margin_rub: float
    reward_cost_rub: float
    infra_cost_rub: float
    net_effect_rub: float
    purchases_in_window: int
    reached_business_metric: bool
    completed_challenge: bool
    relevance_hit: bool


class ProfileEvalResult(BaseModel):
    profile_id: str
    segment: Segment
    persona_label: str
    churn_risk: ChurnRisk
    branches: dict[str, BranchOutcome]


class BranchAggregate(BaseModel):
    branch: Branch
    profiles: int
    avg_incremental_visits: float
    avg_incremental_margin_rub: float
    avg_reward_cost_rub: float
    avg_net_effect_rub: float
    business_metric_share: float
    completion_rate: float
    relevance_hit_rate: float
    plan_source_llm_share: float


class EvalReport(BaseModel):
    seed: int
    profiles: int
    horizon_weeks: int
    cut_week: int
    planner_model: str
    actor_model: str
    null_test: bool
    business_metric_purchases: int
    business_metric_window_weeks: int
    aggregates: dict[str, BranchAggregate]
    business_metric_uplift_pp: float
    results: list[ProfileEvalResult]
