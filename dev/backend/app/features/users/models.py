from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel


class StoreRow(AppModel):
    id: int
    name: str
    chain: Literal["pyaterochka", "perekrestok"]
    district: str
    city: str


class UserRow(AppModel):
    id: int
    pseudonym: str
    segment: Literal["regular_mid", "light", "heavy", "dormant"]
    favourite_store_id: int | None
    referral_code: str
    referred_by_user_id: int | None
    device_fingerprint: str | None
    social_propensity: Decimal
    created_at: datetime


class UserBasicRow(AppModel):
    id: int
    pseudonym: str
    segment: Literal["regular_mid", "light", "heavy", "dormant"]


class UserSummary(AppModel):
    id: int
    pseudonym: str
    segment: Literal["regular_mid", "light", "heavy", "dormant"]
    level: int


class DomovoyStateSummary(AppModel):
    xp: int
    level: int
    xp_to_next_level: int
    mood: Literal["cheerful", "cozy", "healthy", "bored", "sleepy"]
    mood_reason: str
    streak_weeks: int
    items: list[str]


class ReferralTeaserRow(AppModel):
    code: str
    invited_count: int
    rewarded_count: int


class RecommendedMechanicRow(AppModel):
    mechanic: Literal["challenge", "league", "referral"]
    reason: str
