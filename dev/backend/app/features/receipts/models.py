from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel


class ReceiptRow(AppModel):
    id: int
    user_id: int
    store_id: int
    purchased_at: datetime
    regular_total: Decimal
    paid_total: Decimal
    discount_total: Decimal
    points_earned: int
    points_spent: int
    counted: bool
    is_returned: bool
    returned_at: datetime | None
    source: Literal["synthetic", "simulated", "api"]
    pos_id: str | None
    created_at: datetime


class ReceiptItemRow(AppModel):
    id: int
    receipt_id: int
    product_name: str
    category: str
    qty: Decimal
    regular_price: Decimal
    paid_price: Decimal
    is_promo: bool
