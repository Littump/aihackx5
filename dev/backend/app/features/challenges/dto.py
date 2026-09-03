from datetime import datetime
from typing import Literal

from pydantic import Field

from app.core.models import AppModel
from app.features.challenges.models import ChallengeEconomics, ChallengeListResult, RewardKind


class Challenge(AppModel):
    id: int
    type: Literal["frequency", "category"]
    category: str | None
    status: Literal["active", "completed", "failed", "expired"]
    is_hero: bool
    baseline: float
    target: float
    progress: float
    period_start: datetime
    period_end: datetime
    reward_xp: int
    reward_points: int
    title: str = Field(validation_alias="copy_title")
    body: str = Field(validation_alias="copy_body")


class ChallengeDetail(Challenge):
    explanation: str = Field(validation_alias="copy_explanation")
    rationale_features: dict[str, float]
    economics: ChallengeEconomics
    copy_source: Literal["llm", "template"]


class RewardLedgerEntry(AppModel):
    kind: RewardKind
    xp_delta: int
    points_delta: int
    ref_type: str | None
    ref_id: int | None
    created_at: datetime


class ChallengeListResponse(AppModel):
    hero: ChallengeDetail | None
    side: list[ChallengeDetail]
    history: list[Challenge]

    @classmethod
    def from_result(cls, result: ChallengeListResult) -> "ChallengeListResponse":
        return cls(
            hero=ChallengeDetail.model_validate(result.hero) if result.hero else None,
            side=[ChallengeDetail.model_validate(row) for row in result.side],
            history=[Challenge.model_validate(row) for row in result.history],
        )
