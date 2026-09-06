from statistics import mean, pstdev

from app.ml import config
from app.ml.schemas import (
    CadenceClass,
    CategoryTimeseries,
    ChurnRisk,
    PlannerFeatures,
    PlannerInput,
    PlannerUser,
    PreviousPlan,
    PurchaseHistory,
    ShoppingHabit,
    ShopVisit,
    SkuCatalogItem,
    UserProfile,
)

_DEFAULT_CADENCE_DAYS = 7.0
_NO_HISTORY_RECENCY_DAYS = 60


def shopping_habits(
    timeseries: list[CategoryTimeseries], favorites: list[str]
) -> list[ShoppingHabit]:
    by_category = {series.category: series for series in timeseries}
    habits: list[ShoppingHabit] = []
    for category in favorites:
        series = by_category.get(category)
        if series is None:
            habits.append(
                ShoppingHabit(
                    category=category,
                    cadence_class="occasional",
                    share=0.0,
                    days_overdue=0.0,
                    cadence_days=0.0,
                )
            )
            continue
        habits.append(
            ShoppingHabit(
                category=category,
                cadence_class=_cadence_class(series),
                share=series.share,
                days_overdue=series.days_overdue,
                cadence_days=series.cadence_days,
            )
        )
    return habits


def _cadence_class(series: CategoryTimeseries) -> CadenceClass:
    if series.share >= config.STAPLE_SHARE_MIN and series.visits >= config.STAPLE_MIN_VISITS:
        return "lapsed" if series.days_overdue > 0 else "staple"
    if _is_lapse_candidate(series) and series.days_overdue > 0:
        return "lapsed"
    if series.share >= config.CATEGORY_MIN_SHARE:
        return "regular"
    return "occasional"


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
    timeseries = _category_timeseries(visits, now_day, len(visits), churn_risk)
    baseline_visits = max(1, round(frequency_per_week))
    features = PlannerFeatures(
        frequency_per_week=frequency_per_week,
        recency_days=recency_days,
        avg_basket=avg_basket,
        promo_sensitivity=profile.promo_sensitivity,
        cadence_days=round(cadence_days, 2),
        churn_risk=churn_risk,
        baseline_visits=baseline_visits,
        visit_momentum=_visit_momentum(visits, now_day),
        overdue_ratio=round(recency_days / max(cadence_days, 1.0), 2),
        cadence_regularity=_cadence_regularity(visits),
        visit_headroom_ratio=_visit_headroom_ratio(frequency_per_week, recency_days),
        basket_index=round(avg_basket / config.BASKET_REFERENCE, 2),
        category_breadth=_category_breadth(timeseries),
        top_category_overdue_ratio=_top_category_overdue_ratio(timeseries),
    )
    return PlannerInput(
        user=PlannerUser(
            segment=profile.segment, level=profile.level, tenure_weeks=profile.tenure_weeks
        ),
        features=features,
        favorite_categories=list(profile.favorite_categories),
        category_timeseries=timeseries,
        catalog=eligible_catalog,
        previous_plans=previous_plans[: config.PLANNER_PREV_PLANS_MAX],
        challenge_library=list(config.CHALLENGE_LIBRARY),
        high_margin_categories=list(config.HIGH_MARGIN_CATEGORIES),
        high_margin_mandate=config.HIGH_MARGIN_MANDATE_ENABLED,
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


def _visit_momentum(visits: list[ShopVisit], now_day: int) -> float:
    window = config.DERIVED_WINDOW_DAYS
    recent_start = now_day - window
    prior_start = now_day - 2 * window
    weeks = window / 7
    recent = sum(1 for visit in visits if visit.day_index >= recent_start) / weeks
    prior = sum(1 for visit in visits if prior_start <= visit.day_index < recent_start) / weeks
    return round(recent / max(prior, 0.25), 2)


def _cadence_regularity(visits: list[ShopVisit]) -> float:
    if len(visits) < 3:
        return 0.0
    gaps = [visits[i].day_index - visits[i - 1].day_index for i in range(1, len(visits))]
    mean_gap = mean(gaps)
    if mean_gap <= 0:
        return 0.0
    return round(1 - min(1.0, pstdev(gaps) / mean_gap), 2)


def _visit_headroom_ratio(frequency_per_week: float, recency_days: int) -> float:
    if recency_days > config.HEADROOM_ACTIVE_RECENCY_DAYS:
        return 0.0
    ceiling = config.VISIT_CEILING
    ratio = (ceiling - frequency_per_week) / ceiling
    return round(max(0.0, min(1.0, ratio)), 2)


def _category_breadth(timeseries: list[CategoryTimeseries]) -> int:
    return sum(1 for series in timeseries if series.share >= config.CATEGORY_MIN_SHARE)


def _top_category_overdue_ratio(timeseries: list[CategoryTimeseries]) -> float:
    ratios = [
        round((series.days_overdue + series.cadence_days) / max(series.cadence_days, 1.0), 2)
        for series in timeseries
        if _is_lapse_candidate(series) or _is_lapsed_staple(series)
    ]
    return max(ratios) if ratios else 1.0


def _is_lapse_candidate(series: CategoryTimeseries) -> bool:
    return (
        series.category not in config.EXCLUDED_CATEGORIES
        and series.share >= config.CATEGORY_MIN_SHARE
        and series.share < config.STAPLE_SHARE_MIN
        and series.visits >= config.CATEGORY_MIN_VISITS
    )


def _is_lapsed_staple(series: CategoryTimeseries) -> bool:
    return (
        series.category not in config.EXCLUDED_CATEGORIES
        and series.share >= config.STAPLE_SHARE_MIN
        and series.visits >= config.STAPLE_MIN_VISITS
        and series.days_overdue > 0
    )


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
    visits: list[ShopVisit], now_day: int, total_visits: int, churn_risk: ChurnRisk
) -> list[CategoryTimeseries]:
    days_by_category: dict[str, list[int]] = {}
    for visit in visits:
        for category in visit.categories:
            days_by_category.setdefault(category, []).append(visit.day_index)
    series: list[CategoryTimeseries] = []
    for category, days in days_by_category.items():
        cadence = _category_cadence(days)
        last_day = max(days)
        share = round(len(days) / total_visits, 3) if total_visits else 0.0
        overdue = round(max(0.0, (now_day - last_day) - cadence), 2) if len(days) >= 2 else 0.0
        if share >= config.STAPLE_SHARE_MIN and churn_risk == "none":
            overdue = 0.0
        series.append(
            CategoryTimeseries(
                category=category,
                cadence_days=round(cadence, 2),
                days_overdue=overdue,
                share=share,
                visits=len(days),
                contribution_margin=config.CATEGORY_CONTRIBUTION_MARGIN.get(
                    category, config.CONTRIBUTION_MARGIN
                ),
                is_high_margin=config.is_high_margin(category),
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
