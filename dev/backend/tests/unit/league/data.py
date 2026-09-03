from decimal import Decimal

WEEK_SCORE_CASES: list[tuple[Decimal, Decimal, int, int, int, int]] = [
    (Decimal("120"), Decimal("1000"), 1, 3, 4, 124),
    (Decimal("900"), Decimal("1000"), 0, 0, 0, 100),
    (Decimal("0"), Decimal("1000"), 0, 10, 0, 50),
    (Decimal("0"), Decimal("1000"), 0, 0, 20, 35),
    (Decimal("0"), Decimal("0"), 0, 0, 0, 0),
    (Decimal("-50"), Decimal("1000"), 0, 0, 0, 0),
]

CUTOFF_CASES: list[tuple[int, int, int]] = [
    (30, 7, 26),
    (12, 7, 8),
    (1, 1, 2),
]

ZONE_CASES: list[tuple[int, int, int, str]] = [
    (1, 30, 3, "promotion"),
    (7, 30, 3, "promotion"),
    (8, 30, 3, "safe"),
    (25, 30, 3, "safe"),
    (26, 30, 3, "demotion"),
    (30, 30, 3, "demotion"),
    (30, 30, 1, "safe"),
    (1, 30, 5, "safe"),
    (7, 12, 3, "promotion"),
    (8, 12, 3, "demotion"),
    (12, 12, 3, "demotion"),
]
