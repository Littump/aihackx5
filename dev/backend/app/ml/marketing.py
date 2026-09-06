from app.ml import product_knowledge as pk
from app.ml.schemas import ChallengeOffer, ChallengeType, GoalDirection

_FREQUENCY_PITCH: dict[GoalDirection, str] = {
    "increase": (
        "Тебе у нас явно по душе — загляни ещё разок на этой неделе, "
        "Домовой уже приготовил награду за визит."
    ),
    "recover": (
        "Домовой соскучился: давно тебя не видно. Заскочи на неделе — "
        "он встретит тебя тёплым подарком."
    ),
    "sustain": (
        "Ты ходишь к нам как по часам — держи ритм, и Домовой копит для тебя баллы за верность."
    ),
}

_CATEGORY_PITCH: dict[GoalDirection, str] = {
    "increase": (
        "Домовой присмотрел для тебя {cat_acc} ({examples}) — забери с наградой на этой неделе."
    ),
    "recover": (
        "Давно не берёшь {cat_acc} ({examples})? Домовой вернёт это в корзину — "
        "с тёплым подарком на неделе."
    ),
    "sustain": "Бери {cat_acc} как обычно ({examples}) — Домовой добавит за это баллов к покупке.",
}

_REPLENISHMENT_PITCH = (
    "Кажется, {cat} ({examples}) уже на исходе — пополни запас на неделе, "
    "и Домовой отблагодарит наградой."
)

_BASKET_PITCH = (
    "Собери корзину чуть щедрее обычного — Домовой порадуется, подрастёт и подкинет тебе баллов."
)

_COLLECTION_PITCH = (
    "Добавь к покупке {cat_acc} ({examples}) — новая пара откроет тебе награду от Домового."
)

_FORBIDDEN_TOKENS: tuple[str, ...] = (
    "rationale",
    "margin",
    "overdue",
    "baseline",
    "insight",
    "high_margin",
    "visit_frequency",
    "basket_value",
    "cadence",
    "momentum",
    "headroom",
    "frequency",
    "replenishment",
    "collection",
    "category",
    "posture",
    "promo_immune",
    "value_selective",
    "deal_driven",
    "xp",
    "reward",
)


def public_pitch(offer: ChallengeOffer, direction: GoalDirection) -> str:
    cat = pk.category_ru(offer.category)
    cat_acc = pk.category_ru_acc(offer.category)
    examples = pk.category_examples(offer.category)
    text = _pitch_body(offer.challenge_type, direction).format(
        cat=cat, cat_acc=cat_acc, examples=examples
    )
    assert_marketing_clean(text)
    return text


def _pitch_body(challenge_type: ChallengeType, direction: GoalDirection) -> str:
    if challenge_type == "frequency":
        return _FREQUENCY_PITCH[direction]
    if challenge_type == "category":
        return _CATEGORY_PITCH[direction]
    if challenge_type == "replenishment":
        return _REPLENISHMENT_PITCH
    if challenge_type == "basket":
        return _BASKET_PITCH
    return _COLLECTION_PITCH


def assert_marketing_clean(text: str) -> None:
    if any(char.isdigit() for char in text):
        raise ValueError(f"marketing pitch leaks a raw number: {text!r}")
    lowered = text.lower()
    for token in _FORBIDDEN_TOKENS:
        if token in lowered:
            raise ValueError(f"marketing pitch leaks technical token {token!r}: {text!r}")
