from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from app.core import clock


def test_now_uses_override(freeze_time: Callable[[datetime], None]) -> None:
    freeze_time(datetime(2026, 9, 2, 12, 0, tzinfo=UTC))
    assert clock.now().isoformat() == "2026-09-02T15:00:00+03:00"


def test_week_start_is_monday_midnight_moscow(freeze_time: Callable[[datetime], None]) -> None:
    freeze_time(datetime(2026, 9, 2, 21, 30, tzinfo=UTC))
    assert clock.week_start().isoformat() == "2026-08-31T00:00:00+03:00"
    assert clock.week_end().isoformat() == "2026-09-06T23:59:59.999999+03:00"


def test_week_start_before_moscow_midnight_belongs_to_previous_week(
    freeze_time: Callable[[datetime], None],
) -> None:
    freeze_time(datetime(2026, 8, 30, 22, 0, tzinfo=UTC))
    assert clock.week_start().date().isoformat() == "2026-08-31"


def test_day_start_is_local_midnight_moscow(freeze_time: Callable[[datetime], None]) -> None:
    freeze_time(datetime(2026, 9, 2, 21, 30, tzinfo=UTC))
    assert clock.day_start().isoformat() == "2026-09-03T00:00:00+03:00"
    assert clock.day_end().isoformat() == "2026-09-03T23:59:59.999999+03:00"


def test_day_start_before_moscow_midnight_belongs_to_previous_day(
    freeze_time: Callable[[datetime], None],
) -> None:
    freeze_time(datetime(2026, 9, 2, 20, 59, tzinfo=UTC))
    assert clock.day_start().date().isoformat() == "2026-09-02"
    freeze_time(datetime(2026, 9, 2, 21, 0, tzinfo=UTC))
    assert clock.day_start().date().isoformat() == "2026-09-03"


def test_override_requires_timezone() -> None:
    with pytest.raises(ValueError):
        clock.set_override(datetime(2026, 9, 2, 12, 0))  # noqa: DTZ001


def test_real_now_is_aware() -> None:
    assert clock.now().tzinfo is not None
