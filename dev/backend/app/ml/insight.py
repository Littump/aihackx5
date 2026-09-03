from statistics import mean

from app.ml import config
from app.ml.schemas import (
    CategoryTimeseries,
    ChurnRisk,
    PlannerFeatures,
    PlannerInput,
    PlannerUser,
    PreviousPlan,
    PurchaseHistory,
    ShopVisit,
    SkuCatalogItem,
    UserProfile,
)

_DEFAULT_CADENCE_DAYS = 7.0
_NO_HISTORY_RECENCY_DAYS = 60


def build_insight(
    profile: UserProfile,
    past: PurchaseHistory,
    eligible_catalog: list[SkuCatalogItem],
    previous_plans: list[PreviousPlan],
) -> PlannerInput:
    now_day = past.horizon_weeks * 7
    weeks = max(past.horizon_weeks, 1)
    visits = sorted(past.visits, key=lambda visit: visit.day_index)
    frequency_per_week = round(len(visits) / weeks, 3)
    recency_days = _recency_days(visits, now_day)
    cadence_days = _overall_cadence(visits)
    avg_basket = round(mean(visit.basket for visit in visits), 2) if visits else profile.avg_basket
    churn_risk = _churn_risk(recency_days, cadence_days)
    timeseries = _category_timeseries(visits, now_day, len(visits))
    baseline_visits = max(1, round(frequency_per_week))
    features = PlannerFeatures(
        frequency_per_week=frequency_per_week,
        recency_days=recency_days,
        avg_basket=avg_basket,
        promo_sensitivity=profile.promo_sensitivity,
        cadence_days=round(cadence_days, 2),
        churn_risk=churn_risk,
        baseline_visits=baseline_visits,
    )
    return PlannerInput(
        user=PlannerUser(
            segment=profile.segment, level=profile.level, tenure_weeks=profile.tenure_weeks
        ),
        features=features,
        category_timeseries=timeseries,
        catalog=eligible_catalog,
        previous_plans=previous_plans[: config.PLANNER_PREV_PLANS_MAX],
        challenge_library=list(config.CHALLENGE_LIBRARY),
    )


def _recency_days(visits: list[ShopVisit], now_day: int) -> int:
    if not visits:
        return _NO_HISTORY_RECENCY_DAYS
    return now_day - visits[-1].day_index


def _overall_cadence(visits: list[ShopVisit]) -> float:
    if len(visits) < 2:
        return _DEFAULT_CADENCE_DAYS
    gaps = [visits[i].day_index - visits[i - 1].day_index for i in range(1, len(visits))]
    return mean(gaps)


def _churn_risk(recency_days: int, cadence_days: float) -> ChurnRisk:
    if cadence_days <= 0:
        return "none"
    ratio = recency_days / cadence_days
    if ratio > config.CHURN_RISK_HIGH_FACTOR:
        return "high"
    if ratio > config.CHURN_RISK_CADENCE_FACTOR:
        return "elevated"
    return "none"


def _category_timeseries(
    visits: list[ShopVisit], now_day: int, total_visits: int
) -> list[CategoryTimeseries]:
    days_by_category: dict[str, list[int]] = {}
    for visit in visits:
        for category in visit.categories:
            days_by_category.setdefault(category, []).append(visit.day_index)
    series: list[CategoryTimeseries] = []
    for category, days in days_by_category.items():
        cadence = _category_cadence(days)
        last_day = max(days)
        series.append(
            CategoryTimeseries(
                category=category,
                cadence_days=round(cadence, 2),
                days_overdue=round(max(0.0, (now_day - last_day) - cadence), 2),
                share=round(len(days) / total_visits, 3) if total_visits else 0.0,
                visits=len(days),
            )
        )
    series.sort(key=lambda item: item.visits, reverse=True)
    return series[: config.PLANNER_TIMESERIES_TOP_K]


def _category_cadence(days: list[int]) -> float:
    if len(days) < 2:
        return _DEFAULT_CADENCE_DAYS
    ordered = sorted(days)
    gaps = [ordered[i] - ordered[i - 1] for i in range(1, len(ordered))]
    return mean(gaps)
