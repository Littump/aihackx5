from typing import NamedTuple

BIGINT = "bigint"
INTEGER = "integer"
TEXT = "text"
NUMERIC = "numeric"
BOOLEAN = "boolean"
TIMESTAMPTZ = "timestamp with time zone"
DATE = "date"
JSONB = "jsonb"

SET_BY_DB = object()


class Column(NamedTuple):
    type: str
    nullable: bool = False
    precision: int | None = None
    scale: int | None = None


class ForeignKey(NamedTuple):
    column: str
    ref_table: str
    ref_column: str
    on_delete: str


class Index(NamedTuple):
    name: str
    columns: str
    unique: bool = False
    where: str | None = None

    def definition(self, table: str) -> str:
        kind = "UNIQUE INDEX" if self.unique else "INDEX"
        where = f" WHERE {self.where}" if self.where else ""
        return f"CREATE {kind} {self.name} ON {table} USING btree {self.columns}{where}"


class Check(NamedTuple):
    table: str
    column: str
    accepted: tuple[str, ...]
    rejected: str = "unknown"


def numeric(precision: int, scale: int, nullable: bool = False) -> Column:
    return Column(NUMERIC, nullable, precision, scale)
