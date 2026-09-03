from decimal import Decimal

import pytest

from app.features.receipts.models import ReceiptItemDraft
from app.features.receipts.totals import compute_totals
from tests.unit.receipts.data import TOTALS_CASES


@pytest.mark.parametrize(("items", "regular_total", "paid_total", "discount_total"), TOTALS_CASES)
def test_compute_totals_rounds_to_kopeck(
    items: list[ReceiptItemDraft],
    regular_total: Decimal,
    paid_total: Decimal,
    discount_total: Decimal,
) -> None:
    totals = compute_totals(items)
    assert totals.regular_total == regular_total
    assert totals.paid_total == paid_total
    assert totals.discount_total == discount_total
