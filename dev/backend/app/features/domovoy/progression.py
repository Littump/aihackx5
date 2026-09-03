from decimal import Decimal

from app import game_rules
from app.features.domovoy.models import Mood
from app.features.receipts.models import ReceiptWithItems

HEALTHY_CATEGORIES: frozenset[str] = frozenset({"fruits_veg", "dairy"})
COZY_CATEGORIES: frozenset[str] = frozenset({"bakery", "drinks"})


def level_for_xp(xp: int) -> int:
    return game_rules.level_for_xp(xp)


def xp_to_next_level(xp: int) -> int:
    return game_rules.xp_to_next_level(xp)


def mood_for_week(receipts: list[ReceiptWithItems]) -> tuple[Mood, str]:
    if not receipts:
        return "sleepy", f"нет чеков {game_rules.MOOD_SLEEPY_INACTIVITY_DAYS}+ дней"
    healthy_share = _category_group_share(receipts, HEALTHY_CATEGORIES)
    if healthy_share >= game_rules.MOOD_HEALTHY_SHARE_MIN:
        return "healthy", f"доля полезных покупок {healthy_share:.0%}"
    cozy_receipts = _receipts_with_all_categories(receipts, COZY_CATEGORIES)
    if cozy_receipts >= game_rules.MOOD_COZY_MIN_RECEIPTS:
        return "cozy", "выпечка и напитки в нескольких чеках"
    categories = _distinct_categories(receipts)
    if len(categories) >= game_rules.MOOD_CHEERFUL_MIN_CATEGORIES:
        return "cheerful", f"{len(categories)} разных категорий за неделю"
    return "bored", "нет выраженного паттерна покупок"


def next_streak(prev: int, completed_this_week: bool, freeze_available: bool) -> tuple[int, bool]:
    if completed_this_week:
        return prev + 1, freeze_available
    if freeze_available:
        return prev, False
    return 0, freeze_available


def _category_group_share(receipts: list[ReceiptWithItems], categories: frozenset[str]) -> Decimal:
    total = Decimal("0")
    matched = Decimal("0")
    for receipt in receipts:
        for item in receipt.items:
            line = item.regular_price * item.qty
            total += line
            if item.category in categories:
                matched += line
    return matched / total if total else Decimal("0")


def _receipts_with_all_categories(
    receipts: list[ReceiptWithItems], categories: frozenset[str]
) -> int:
    return sum(1 for r in receipts if categories.issubset({item.category for item in r.items}))


def _distinct_categories(receipts: list[ReceiptWithItems]) -> set[str]:
    result: set[str] = set()
    for r in receipts:
        result.update(item.category for item in r.items)
    return result
