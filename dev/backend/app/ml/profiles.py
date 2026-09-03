import random

from app.ml import config
from app.ml.schemas import Segment, UserProfile

_SEGMENT_SHARE: tuple[tuple[Segment, float], ...] = (
    ("regular_mid", 0.60),
    ("light", 0.20),
    ("heavy", 0.12),
    ("dormant", 0.08),
)
_VISITS_PER_WEEK: dict[Segment, tuple[float, float]] = {
    "regular_mid": (0.9, 1.8),
    "light": (0.3, 0.8),
    "heavy": (2.2, 3.5),
    "dormant": (0.15, 0.5),
}
_AVG_BASKET: dict[Segment, tuple[float, float]] = {
    "regular_mid": (450.0, 760.0),
    "light": (300.0, 560.0),
    "heavy": (700.0, 1400.0),
    "dormant": (350.0, 620.0),
}
_PROMO_SENSITIVITY: dict[Segment, tuple[float, float]] = {
    "regular_mid": (0.15, 0.55),
    "light": (0.20, 0.60),
    "heavy": (0.10, 0.40),
    "dormant": (0.30, 0.80),
}
_RESPONSIVENESS: dict[Segment, tuple[float, float]] = {
    "regular_mid": (0.25, 0.65),
    "light": (0.15, 0.45),
    "heavy": (0.20, 0.50),
    "dormant": (0.30, 0.75),
}
_PERSONAS: dict[Segment, tuple[str, ...]] = {
    "regular_mid": (
        "семейный закупщик недели",
        "офисный сотрудник за обедом",
        "родитель с двумя детьми",
    ),
    "light": (
        "студент за снеками перед парой",
        "заходит по пути домой за мелочью",
    ),
    "heavy": (
        "ЗОЖ за конкретным продуктом",
        "большая семья, крупные закупки",
    ),
    "dormant": (
        "вечерний покупатель после спорта",
        "давно не заходил, дрейфует к конкуренту",
    ),
}
_FAVORITE_CATEGORIES = 3


def build_profiles(seed: int, count: int) -> list[UserProfile]:
    rng = random.Random(seed)
    return [_build_profile(rng, index) for index in range(count)]


def _build_profile(rng: random.Random, index: int) -> UserProfile:
    segment = _pick_segment(rng)
    visits_per_week = round(rng.uniform(*_VISITS_PER_WEEK[segment]), 3)
    avg_basket = round(rng.uniform(*_AVG_BASKET[segment]), 2)
    promo_sensitivity = round(rng.uniform(*_PROMO_SENSITIVITY[segment]), 3)
    responsiveness = round(rng.uniform(*_RESPONSIVENESS[segment]), 3)
    tenure_weeks = rng.randint(2, 40)
    level = _level_for(segment, tenure_weeks, rng)
    persona = rng.choice(_PERSONAS[segment])
    weights = _category_weights(rng)
    return UserProfile(
        profile_id=f"P{index:04d}",
        segment=segment,
        persona_label=persona,
        level=level,
        tenure_weeks=tenure_weeks,
        visits_per_week=visits_per_week,
        avg_basket=avg_basket,
        promo_sensitivity=promo_sensitivity,
        category_weights=weights,
        offer_responsiveness=responsiveness,
    )


def _pick_segment(rng: random.Random) -> Segment:
    roll = rng.random()
    cumulative = 0.0
    for segment, share in _SEGMENT_SHARE:
        cumulative += share
        if roll <= cumulative:
            return segment
    return _SEGMENT_SHARE[-1][0]


def _level_for(segment: Segment, tenure_weeks: int, rng: random.Random) -> int:
    base = 1 + tenure_weeks // 5
    if segment == "heavy":
        base += 2
    if segment == "dormant":
        base = max(1, base - 1)
    return max(1, min(10, base + rng.randint(-1, 1)))


def _category_weights(rng: random.Random) -> dict[str, float]:
    eligible = [category for category in config.CATEGORIES if category != "alcohol"]
    favorites = rng.sample(eligible, _FAVORITE_CATEGORIES)
    raw: dict[str, float] = {}
    for category in config.CATEGORIES:
        concentration = 6.0 if category in favorites else 0.6
        raw[category] = rng.gammavariate(concentration, 1.0)
    total = sum(raw.values())
    return {category: round(value / total, 4) for category, value in raw.items()}
