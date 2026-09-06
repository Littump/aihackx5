import random

from app.ml import config
from app.ml.schemas import DealAttitude, Segment, UserProfile

_SEGMENT_SHARE: tuple[tuple[Segment, float], ...] = (
    ("regular_mid", 0.58),
    ("light", 0.24),
    ("heavy", 0.13),
    ("dormant", 0.05),
)
_ATTITUDE_SHARE: tuple[tuple[DealAttitude, float], ...] = (
    ("deal_seeker", 0.30),
    ("selective", 0.48),
    ("promo_skeptic", 0.22),
)
_ATTITUDE_PROMO_BAND: dict[DealAttitude, tuple[float, float]] = {
    "promo_skeptic": (0.10, 0.33),
    "selective": (0.37, 0.60),
    "deal_seeker": (0.64, 0.92),
}
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
_RESPONSIVENESS: dict[Segment, tuple[float, float]] = {
    "regular_mid": (0.25, 0.65),
    "light": (0.15, 0.45),
    "heavy": (0.20, 0.50),
    "dormant": (0.30, 0.75),
}
_ROUTINE_RIGIDITY: dict[Segment, tuple[float, float]] = {
    "regular_mid": (0.45, 0.85),
    "light": (0.35, 0.75),
    "heavy": (0.55, 0.9),
    "dormant": (0.2, 0.6),
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
_ARCHETYPES: dict[Segment, tuple[str, ...]] = {
    "regular_mid": (
        "человек привычки: один и тот же маршрут по магазину",
        "занятой прагматик, считает минуты, а не рубли",
    ),
    "light": (
        "импульсивный минималист, заходит редко и коротко",
        "экономный студент, ловит только реально выгодное",
    ),
    "heavy": (
        "закупщик-оптимизатор, планирует корзину заранее",
        "требовательный гурман, лоялен своим брендам",
    ),
    "dormant": (
        "разочарованный уходящий клиент, легко уводится конкурентом",
        "редкий гость без привязки к магазину",
    ),
}
_ATTITUDE_BLURB: dict[DealAttitude, str] = {
    "promo_skeptic": (
        "Занят и ценит время: берёт привычное на автомате, но точечную выгоду не упустит."
    ),
    "selective": "Считает деньги с умом: включается, когда выгода попадает в его корзину.",
    "deal_seeker": (
        "Осознанно ловит выгоду: держит приложение под рукой, копит баллы и кэшбэк на нужное."
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
    deal_attitude = _pick_attitude(rng)
    promo_sensitivity = round(rng.uniform(*_ATTITUDE_PROMO_BAND[deal_attitude]), 3)
    responsiveness = round(rng.uniform(*_RESPONSIVENESS[segment]), 3)
    routine_rigidity = round(rng.uniform(*_ROUTINE_RIGIDITY[segment]), 3)
    tenure_weeks = rng.randint(2, 40)
    level = _level_for(segment, tenure_weeks, rng)
    persona = rng.choice(_PERSONAS[segment])
    archetype = rng.choice(_ARCHETYPES[segment])
    weights = _category_weights(rng)
    favorites = _top_categories(weights)
    persona_brief = _ATTITUDE_BLURB[deal_attitude]
    return UserProfile(
        profile_id=f"P{index:04d}",
        segment=segment,
        persona_label=persona,
        archetype=archetype,
        persona_brief=persona_brief,
        deal_attitude=deal_attitude,
        routine_rigidity=routine_rigidity,
        level=level,
        tenure_weeks=tenure_weeks,
        visits_per_week=visits_per_week,
        avg_basket=avg_basket,
        promo_sensitivity=promo_sensitivity,
        category_weights=weights,
        favorite_categories=favorites,
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


def _pick_attitude(rng: random.Random) -> DealAttitude:
    roll = rng.random()
    cumulative = 0.0
    for attitude, share in _ATTITUDE_SHARE:
        cumulative += share
        if roll <= cumulative:
            return attitude
    return _ATTITUDE_SHARE[-1][0]


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


def _top_categories(weights: dict[str, float]) -> list[str]:
    ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)
    return [category for category, _ in ranked[:_FAVORITE_CATEGORIES]]
