from app.ml import app_view, marketing
from app.ml import product_knowledge as pk
from app.ml.schemas import ChallengeOffer, ChallengeType, GoalDirection, RewardComputation

_ACCUSATIVE_CASES = {
    "dairy": "молочку",
    "meat_fish": "мясо и рыбу",
    "grocery": "бакалею",
    "household": "бытовую химию",
    "beauty": "косметику и уход",
    "ready_food": "готовую еду",
    "bakery": "выпечку и хлеб",
}


def _offer(challenge_type: ChallengeType, category: str | None) -> ChallengeOffer:
    return ChallengeOffer(
        role="side",
        insight_ref="x",
        challenge_type=challenge_type,
        category=category,
        baseline=0,
        target=1,
        deadline_days=7,
        reward=RewardComputation(
            xp_level="low",
            points_level="none",
            xp_amount=10,
            max_reward_rub=0.0,
            reward_points=0,
            reward_cost_rub=0.0,
        ),
        rationale="r",
    )


def test_category_ru_acc_declension() -> None:
    for category, expected in _ACCUSATIVE_CASES.items():
        assert pk.category_ru_acc(category) == expected


def test_condition_uses_accusative_not_nominative() -> None:
    for category in _ACCUSATIVE_CASES:
        for challenge_type in ("collection", "replenishment", "category"):
            text = app_view._condition(_offer(challenge_type, category))
            assert pk.category_ru_acc(category) in text
            nominative = pk.category_ru(category)
            if nominative != pk.category_ru_acc(category):
                assert f"покупке {nominative} " not in text
                assert f"пополнить {nominative} " not in text
                assert f"взять {nominative} " not in text


def test_marketing_pitch_is_clean_for_every_category_and_direction() -> None:
    directions: tuple[GoalDirection, ...] = ("increase", "recover", "sustain")
    types: tuple[ChallengeType, ...] = ("category", "replenishment", "collection")
    for category in pk.CATEGORY_LABEL_RU:
        for challenge_type in types:
            for direction in directions:
                text = marketing.public_pitch(_offer(challenge_type, category), direction)
                assert text
                assert not any(char.isdigit() for char in text)


def test_collection_pitch_uses_accusative() -> None:
    text = marketing.public_pitch(_offer("collection", "ready_food"), "increase")
    assert "готовую еду" in text
    assert "готовая еда" not in text
