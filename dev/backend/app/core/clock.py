from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.game_rules import TIMEZONE

TZ = ZoneInfo(TIMEZONE)
_override: datetime | None = None


def now() -> datetime:
    if _override is not None:
        return _override.astimezone(TZ)
    if settings.demo_now:
        return datetime.fromisoformat(settings.demo_now).astimezone(TZ)
    return datetime.now(tz=TZ)  # noqa: TID251


def today() -> date:
    return now().date()


def week_start(moment: datetime | None = None) -> datetime:
    local = (moment or now()).astimezone(TZ)
    monday = local.date() - timedelta(days=local.weekday())
    return datetime.combine(monday, datetime.min.time(), tzinfo=TZ)


def week_end(moment: datetime | None = None) -> datetime:
    return week_start(moment) + timedelta(days=7) - timedelta(microseconds=1)


def month_start(moment: datetime | None = None) -> datetime:
    local = (moment or now()).astimezone(TZ)
    return datetime(local.year, local.month, 1, tzinfo=TZ)


def month_end(moment: datetime | None = None) -> datetime:
    start = month_start(moment)
    year = start.year + 1 if start.month == 12 else start.year
    month = 1 if start.month == 12 else start.month + 1
    return datetime(year, month, 1, tzinfo=TZ) - timedelta(microseconds=1)


def day_start(moment: datetime | None = None) -> datetime:
    local = (moment or now()).astimezone(TZ)
    return datetime.combine(local.date(), datetime.min.time(), tzinfo=TZ)


def day_end(moment: datetime | None = None) -> datetime:
    return day_start(moment) + timedelta(days=1) - timedelta(microseconds=1)


def set_override(moment: datetime | None) -> None:
    global _override
    if moment is not None and moment.tzinfo is None:
        raise ValueError("время должно быть с таймзоной")
    _override = moment
