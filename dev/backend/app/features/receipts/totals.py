from decimal import Decimal

from app.features.receipts.models import ReceiptItemDraft, ReceiptTotals

CENT = Decimal("0.01")


def compute_totals(items: list[ReceiptItemDraft]) -> ReceiptTotals:
    regular = sum((item.regular_price * item.qty for item in items), Decimal("0"))
    paid = sum((item.paid_price * item.qty for item in items), Decimal("0"))
    regular = regular.quantize(CENT)
    paid = paid.quantize(CENT)
    return ReceiptTotals(regular_total=regular, paid_total=paid, discount_total=regular - paid)
