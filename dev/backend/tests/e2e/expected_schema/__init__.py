from . import core, social_risk
from .types import (
    BIGINT,
    BOOLEAN,
    DATE,
    INTEGER,
    JSONB,
    NUMERIC,
    SET_BY_DB,
    TEXT,
    TIMESTAMPTZ,
    Check,
    Column,
    ForeignKey,
    Index,
    numeric,
)

COLUMNS: dict[str, dict[str, Column]] = {**core.COLUMNS, **social_risk.COLUMNS}
TABLES: tuple[str, ...] = core.TABLES + social_risk.TABLES
PRIMARY_KEYS: dict[str, tuple[str, ...]] = {**core.PRIMARY_KEYS, **social_risk.PRIMARY_KEYS}
UNIQUES: dict[str, set[tuple[str, ...]]] = {**core.UNIQUES, **social_risk.UNIQUES}
FOREIGN_KEYS: dict[str, set[ForeignKey]] = {**core.FOREIGN_KEYS, **social_risk.FOREIGN_KEYS}
INDEXES: dict[str, set[Index]] = {**core.INDEXES, **social_risk.INDEXES}
CHECKS: list[Check] = core.CHECKS
CHECK_VALUES: list[Check] = social_risk.CHECK_VALUES
DEFAULTS: dict[str, dict[str, object]] = core.DEFAULTS

__all__ = [
    "BIGINT",
    "BOOLEAN",
    "CHECKS",
    "CHECK_VALUES",
    "COLUMNS",
    "DATE",
    "DEFAULTS",
    "FOREIGN_KEYS",
    "INDEXES",
    "INTEGER",
    "JSONB",
    "NUMERIC",
    "PRIMARY_KEYS",
    "SET_BY_DB",
    "TABLES",
    "TEXT",
    "TIMESTAMPTZ",
    "UNIQUES",
    "Check",
    "Column",
    "ForeignKey",
    "Index",
    "numeric",
]
