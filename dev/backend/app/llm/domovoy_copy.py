from typing import Literal

from app.core.models import AppModel
from app.features.challenges.models import ChallengeDraft
from app.features.savings.models import SavingsSummary
from app.features.user_features.models import UserFeaturesRow


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
    return f"За {savings.period} ты сэкономил {savings.amount:.0f} ₽ — Домовой доволен!"


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
    category = challenge.category or "категории"
    share = challenge.rationale_features.share
    assert share is not None
    share_percent = round(share * 100)
    explanation = (
        f"Ты берёшь {category} в {share_percent}% покупок — попробуй набрать "
        f"{target} раз на этой неделе."
    )
    body = f"Цель недели: {target} покупок категории {category}."
    return ChallengeCopy(
        title=f"Больше {category}", body=body, explanation=explanation, source="template"
    )
