from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.core.errors import AppError
from app.features.pm import database, service
from app.features.pm.models import (
    EvalRunRow,
    JsonValue,
    SimulationRunResults,
    SimulationRunRow,
)

CREATED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)

SIMULATION_RESULTS = SimulationRunResults(
    purchases_per_user_control=1.2,
    purchases_per_user_treatment=1.5,
    share_above_n_control=0.3,
    share_above_n_treatment=0.4,
    frequency_uplift=0.25,
    incremental_revenue=1000.0,
    incremental_margin=150.0,
    reward_cost=50.0,
    net_effect=100.0,
    referral_conversion=0.1,
    fraud_precision=0.9,
    fraud_recall=0.8,
)


async def test_get_latest_simulation_raises_404_when_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_latest(_: AsyncConnection) -> None:
        return None

    monkeypatch.setattr(database, "get_latest_simulation_run", fake_latest)

    with pytest.raises(AppError) as exc_info:
        await service.get_latest_simulation(None)  # type: ignore[arg-type]

    assert exc_info.value.code == "simulation_not_found"
    assert exc_info.value.status == 404


async def test_get_latest_simulation_returns_row_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = SimulationRunRow(
        id=1, created_at=CREATED_AT, params={"users": 100}, results=SIMULATION_RESULTS
    )

    async def fake_latest(_: AsyncConnection) -> SimulationRunRow:
        return row

    monkeypatch.setattr(database, "get_latest_simulation_run", fake_latest)

    result = await service.get_latest_simulation(None)  # type: ignore[arg-type]

    assert result == row


def test_simulation_run_row_accepts_nested_json_value_in_params() -> None:
    row = SimulationRunRow(
        id=1,
        created_at=CREATED_AT,
        params={"assumptions": {"uplift": 0.2, "weeks": [1, 2, 3]}},
        results=SIMULATION_RESULTS,
    )

    assumptions = row.params["assumptions"]
    assert isinstance(assumptions, dict)
    assert assumptions["uplift"] == 0.2


async def test_get_latest_eval_raises_404_when_none(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_latest(_: AsyncConnection) -> None:
        return None

    monkeypatch.setattr(database, "get_latest_eval_run", fake_latest)

    with pytest.raises(AppError) as exc_info:
        await service.get_latest_eval(None)  # type: ignore[arg-type]

    assert exc_info.value.code == "eval_not_found"
    assert exc_info.value.status == 404


async def test_record_simulation_run_delegates_to_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    async def fake_insert(
        _: AsyncConnection,
        *,
        params: dict[str, JsonValue],
        results: SimulationRunResults,
    ) -> SimulationRunRow:
        calls.append({"params": params, "results": results})
        return SimulationRunRow(id=2, created_at=CREATED_AT, params=params, results=results)

    monkeypatch.setattr(database, "insert_simulation_run", fake_insert)

    result = await service.record_simulation_run(
        None,  # type: ignore[arg-type]
        params={"users": 500},
        results=SIMULATION_RESULTS,
    )

    assert len(calls) == 1
    assert calls[0]["params"] == {"users": 500}
    assert result.id == 2


async def test_record_eval_run_delegates_to_database(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    async def fake_insert(
        _: AsyncConnection,
        *,
        profiles: int,
        hit_rate: Decimal,
        invalid_rate: Decimal,
        fallback_rate: Decimal,
        economics_pass_rate: Decimal,
        details: list[dict[str, JsonValue]],
    ) -> EvalRunRow:
        calls.append({"profiles": profiles, "details": details})
        return EvalRunRow(
            id=3,
            created_at=CREATED_AT,
            profiles=profiles,
            hit_rate=hit_rate,
            invalid_rate=invalid_rate,
            fallback_rate=fallback_rate,
            economics_pass_rate=economics_pass_rate,
            details=details,
        )

    monkeypatch.setattr(database, "insert_eval_run", fake_insert)

    result = await service.record_eval_run(
        None,  # type: ignore[arg-type]
        profiles=30,
        hit_rate=Decimal("0.800"),
        invalid_rate=Decimal("0.050"),
        fallback_rate=Decimal("0.100"),
        economics_pass_rate=Decimal("0.900"),
        details=[{"challenge": "frequency", "verdict": "hit"}],
    )

    assert len(calls) == 1
    assert calls[0]["profiles"] == 30
    assert result.id == 3
