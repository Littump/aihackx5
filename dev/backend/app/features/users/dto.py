from typing import Literal

from app.core.models import AppModel


class UserSummary(AppModel):
    id: int
    pseudonym: str
    segment: Literal["regular_mid", "light", "heavy", "dormant"]
    level: int


class UserListResponse(AppModel):
    items: list[UserSummary]
