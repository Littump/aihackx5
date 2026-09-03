import math
import random

from app.ml.schemas import PurchaseHistory, ShopVisit, UserProfile

_MAX_CATEGORIES_PER_VISIT = 3
_BASKET_NOISE = 0.25


def simulate_history(profile: UserProfile, seed: int, horizon_weeks: int) -> PurchaseHistory:
    rng = random.Random(f"{seed}:{profile.profile_id}:history")
    visits: list[ShopVisit] = []
    for week in range(horizon_weeks):
        visits.extend(_week_visits(rng, profile, week))
    return PurchaseHistory(horizon_weeks=horizon_weeks, visits=visits)


def slice_history(history: PurchaseHistory, cut_week: int) -> PurchaseHistory:
    cut_day = cut_week * 7
    past = [visit for visit in history.visits if visit.day_index < cut_day]
    return PurchaseHistory(horizon_weeks=cut_week, visits=past)


def tail_visits(history: PurchaseHistory, cut_week: int) -> list[ShopVisit]:
    cut_day = cut_week * 7
    return [visit for visit in history.visits if visit.day_index >= cut_day]


def _week_visits(rng: random.Random, profile: UserProfile, week: int) -> list[ShopVisit]:
    count = _poisson(rng, profile.visits_per_week)
    days = sorted(rng.sample(range(7), min(count, 7))) if count else []
    return [_make_visit(rng, profile, week * 7 + day) for day in days]


def _make_visit(rng: random.Random, profile: UserProfile, day_index: int) -> ShopVisit:
    categories = _pick_categories(rng, profile.category_weights)
    factor = 1.0 + rng.uniform(-_BASKET_NOISE, _BASKET_NOISE)
    basket = round(profile.avg_basket * factor, 2)
    return ShopVisit(day_index=day_index, categories=categories, basket=basket)


def _pick_categories(rng: random.Random, weights: dict[str, float]) -> list[str]:
    size = rng.randint(1, _MAX_CATEGORIES_PER_VISIT)
    categories = list(weights.keys())
    chosen: list[str] = []
    remaining = dict(weights)
    for _ in range(size):
        if not remaining:
            break
        picked = _weighted_choice(rng, remaining)
        chosen.append(picked)
        remaining.pop(picked)
    return chosen if chosen else [categories[0]]


def _weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    total = sum(weights.values())
    threshold = rng.random() * total
    cumulative = 0.0
    for category, weight in weights.items():
        cumulative += weight
        if threshold <= cumulative:
            return category
    return next(iter(weights))


def _poisson(rng: random.Random, rate: float) -> int:
    if rate <= 0:
        return 0
    limit = math.exp(-rate)
    count = 0
    product = rng.random()
    while product > limit:
        count += 1
        product *= rng.random()
        if count > 12:
            break
    return count
