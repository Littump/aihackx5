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
