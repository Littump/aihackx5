from typing import Literal

from app.core.models import AppModel
from app.features.challenges.models import ChallengeDraft
from app.features.savings.models import SavingsSummary
from app.features.user_features.models import UserFeaturesRow

CATEGORY_LABELS: dict[str, str] = {
    "dairy": "Молочное",
    "bakery": "Выпечка",
    "fruits_veg": "Овощи и фрукты",
    "meat_fish": "Мясо и рыба",
    "grocery": "Бакалея",
    "snacks": "Снеки",
    "drinks": "Напитки",
    "alcohol": "Алкоголь",
    "household": "Хозтовары",
    "beauty": "Красота и уход",
    "ready_food": "Готовая еда",
    "other": "Другое",
}
PERIOD_LABELS: dict[str, str] = {"week": "неделю", "month": "месяц"}


def _category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)


class ChallengeCopy(AppModel):
    title: str
    body: str
    explanation: str
    source: Literal["llm", "template"]


async def render_challenge(
    *, challenge: ChallengeDraft, features: UserFeaturesRow
) -> ChallengeCopy:
    if challenge.type == "category":
        return _category_copy(challenge)
    return _frequency_copy(challenge)


async def render_insight(*, features: UserFeaturesRow, savings: SavingsSummary) -> str:
    period_label = PERIOD_LABELS.get(savings.period, savings.period)
    return f"За {period_label} ты сэкономил {savings.amount:.0f} ₽ — Домовой доволен!"


def _frequency_copy(challenge: ChallengeDraft) -> ChallengeCopy:
    target = int(challenge.target)
    current = challenge.rationale_features.frequency_per_week
    assert current is not None
    explanation = (
        f"Сейчас у тебя {current:.1f} покупок в неделю — предлагаем дойти "
        f"до {target}, это по силам."
    )
    body = f"Цель недели: {target} покупок (сейчас {challenge.baseline})."
    return ChallengeCopy(
        title="Покупай почаще", body=body, explanation=explanation, source="template"
    )


def _category_copy(challenge: ChallengeDraft) -> ChallengeCopy:
    target = int(challenge.target)
    label = _category_label(challenge.category) if challenge.category else "категории"
    share = challenge.rationale_features.share
    assert share is not None
    share_percent = round(share * 100)
    explanation = (
        f"Категория «{label}» — {share_percent}% твоих покупок. Попробуй набрать "
        f"{target} раз на этой неделе."
    )
    body = f"Цель недели: {target} покупок в категории «{label}»."
    return ChallengeCopy(
        title=f"Больше «{label}»", body=body, explanation=explanation, source="template"
    )
