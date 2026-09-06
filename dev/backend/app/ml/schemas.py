from typing import Literal

from pydantic import BaseModel, Field

from app.ml import config

Segment = Literal["regular_mid", "light", "heavy", "dormant"]
ChurnRisk = Literal["none", "elevated", "high"]
ChallengeType = Literal["frequency", "category", "basket", "replenishment", "collection"]
Lifecycle = Literal["rising", "steady", "cooling", "dormant"]
Posture = Literal["promo_immune", "value_selective", "deal_driven"]
CadenceClass = Literal["staple", "lapsed", "regular", "occasional"]
GoalTarget = Literal["visit_frequency", "basket_value"]
GoalProxy = Literal["lapsed_category_rebuy", "add_category", "high_margin_category", "none"]
GoalDirection = Literal["increase", "recover", "sustain"]
XpLevel = Literal["low", "medium", "high"]
PointsLevel = Literal["none", "low", "medium", "high"]
InsightKind = Literal[
    "lapsed_category",
    "momentum_ride",
    "visit_headroom",
    "churn_drift",
    "dormant_gap",
    "basket_depth",
    "high_margin_push",
    "streak_continuity",
    "reward_posture",
    "staple_avoid",
]
ChallengeRole = Literal["hero", "side"]
PlanSource = Literal["llm", "rules"]
Branch = Literal["control_x5", "treatment_llm", "treatment_rules"]
PromoDecision = Literal["use_offer", "buy_as_usual", "ignore"]
DealAttitude = Literal["promo_skeptic", "selective", "deal_seeker"]
JudgeVerdictLabel = Literal["good", "mixed", "bad"]
JudgeCooperationFlag = Literal["too_cooperative", "consistent", "too_resistant"]


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
    contribution_margin: float
    is_high_margin: bool


class ShoppingHabit(BaseModel):
    category: str
    cadence_class: CadenceClass
    share: float
    days_overdue: float
    cadence_days: float


class PreviousPlan(BaseModel):
    week: int
    challenge_type: ChallengeType
    xp_level: XpLevel
    points_level: PointsLevel
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
    visit_momentum: float
    overdue_ratio: float
    cadence_regularity: float
    visit_headroom_ratio: float
    basket_index: float
    category_breadth: int
    top_category_overdue_ratio: float


class PlannerInput(BaseModel):
    user: PlannerUser
    features: PlannerFeatures
    favorite_categories: list[str]
    category_timeseries: list[CategoryTimeseries]
    catalog: list[SkuCatalogItem]
    previous_plans: list[PreviousPlan]
    challenge_library: list[str]
    high_margin_categories: list[str]
    high_margin_mandate: bool


class BuyerClassification(BaseModel):
    keywords: list[str] = Field(min_length=2, max_length=5)
    label: str = Field(max_length=140)
    description: str = Field(max_length=280)
    evidence: list[str] = Field(default_factory=list)
    posture: Posture
    is_ambiguous: bool = False


class PlannerGoal(BaseModel):
    target: GoalTarget
    proxy: GoalProxy
    direction: GoalDirection
    rationale: str = Field(max_length=300)


class NamedInsight(BaseModel):
    name: str = Field(max_length=60)
    kind: InsightKind
    behaviour: str = Field(max_length=220)
    dod: str = Field(max_length=200)
    strategy_hint: str = Field(max_length=200)
    evidence_metric: str = Field(max_length=90)


class ChallengeReward(BaseModel):
    xp_level: XpLevel
    points_level: PointsLevel


class PlannedChallenge(BaseModel):
    role: ChallengeRole
    insight_ref: str = Field(max_length=60)
    challenge_type: ChallengeType
    category: str | None
    target: int = Field(ge=1)
    reward: ChallengeReward
    rationale: str = Field(max_length=240)


class GeneralStrategy(BaseModel):
    insight_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(max_length=400)
    next_week_hint: str = Field(default="", max_length=240)


class ChallengePlan(BaseModel):
    thinking: str = Field(default="", max_length=1500)
    classification: BuyerClassification
    goal: PlannerGoal
    insights: list[NamedInsight] = Field(min_length=1, max_length=config.MAX_INSIGHTS)
    challenges: list[PlannedChallenge] = Field(min_length=1, max_length=config.MAX_CHALLENGES)
    general_strategy: GeneralStrategy


class RewardComputation(BaseModel):
    xp_level: XpLevel
    points_level: PointsLevel
    xp_amount: int
    max_reward_rub: float
    reward_points: int
    reward_cost_rub: float


class ChallengeOffer(BaseModel):
    role: ChallengeRole
    insight_ref: str
    challenge_type: ChallengeType
    category: str | None
    baseline: int
    target: int
    deadline_days: int
    reward: RewardComputation
    rationale: str


class ValidatedPlan(BaseModel):
    offers: list[ChallengeOffer]
    classification: BuyerClassification
    goal: PlannerGoal
    insights: list[NamedInsight]
    general_strategy: GeneralStrategy
    plan_source: PlanSource
    is_valid: bool
    repair_count: int


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
    high_margin_hit: bool


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
    high_margin_share: float


class EvalReport(BaseModel):
    seed: int
    profiles: int
    horizon_weeks: int
    cut_week: int
    planner_model: str
    actor_model: str
    null_test: bool
    high_margin_mandate: bool
    business_metric_purchases: int
    business_metric_window_weeks: int
    aggregates: dict[str, BranchAggregate]
    business_metric_uplift_pp: float
    results: list[ProfileEvalResult]


JudgeInsightSeverity = Literal["good", "concern", "critical"]


class JudgeInsight(BaseModel):
    aspect: str = Field(max_length=48)
    observation: str = Field(max_length=240)
    severity: JudgeInsightSeverity


class JudgeVerdict(BaseModel):
    planner_insights: list[JudgeInsight] = Field(min_length=1, max_length=6)
    persona_insights: list[JudgeInsight] = Field(min_length=1, max_length=6)
    strategy_fit: int = Field(ge=1, le=5)
    mechanic_choice: int = Field(ge=1, le=5)
    reward_fit: int = Field(ge=1, le=5)
    rationale_honesty: int = Field(ge=1, le=5)
    persona_consistency: int = Field(ge=1, le=5)
    actor_cooperation: JudgeCooperationFlag
    verdict: JudgeVerdictLabel
    summary: str = Field(max_length=400)


class ProfileJudgement(BaseModel):
    profile_id: str
    segment: str
    verdict: JudgeVerdict


JudgeSeverity = Literal["high", "medium", "low"]
JudgeProposalDimension = Literal[
    "strategy_fit",
    "mechanic_choice",
    "reward_fit",
    "rationale_honesty",
    "persona_consistency",
    "actor_cooperation",
]


class ProposalEvidence(BaseModel):
    profile_id: str
    observation: str = Field(max_length=280)


class JudgeProposal(BaseModel):
    title: str = Field(max_length=120)
    dimension: JudgeProposalDimension
    severity: JudgeSeverity
    problem: str = Field(max_length=600)
    proposal: str = Field(max_length=600)
    evidence: list[ProposalEvidence] = Field(min_length=2, max_length=6)


class JudgeProposals(BaseModel):
    analysis: str = Field(max_length=1600)
    proposals: list[JudgeProposal] = Field(max_length=8)
