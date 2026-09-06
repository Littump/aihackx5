import asyncio

import httpx
import pytest

from app.ml import capacity, config


def _metrics(running: float, queue: float, token_usage: float) -> str:
    labels = 'engine_type="unified",model_name="m",moe_ep_rank="0",pp_rank="0",tp_rank="0"'
    return "\n".join(
        [
            "# HELP sglang:num_running_reqs x",
            "# TYPE sglang:num_running_reqs gauge",
            f"sglang:num_running_reqs{{{labels}}} {running}",
            "# TYPE sglang:num_queue_reqs gauge",
            f"sglang:num_queue_reqs{{{labels}}} {queue}",
            "# TYPE sglang:token_usage gauge",
            f"sglang:token_usage{{{labels}}} {token_usage}",
            "# TYPE sglang:full_token_usage gauge",
            f"sglang:full_token_usage{{{labels}}} {token_usage}",
            "",
        ]
    )


def test_metrics_url_from_base_strips_v1() -> None:
    assert (
        capacity.metrics_url_from_base("http://localhost:8080/v1")
        == "http://localhost:8080/metrics"
    )
    assert (
        capacity.metrics_url_from_base("http://localhost:8080/v1/")
        == "http://localhost:8080/metrics"
    )


def test_parse_occupancy_uses_kv_and_running_pressure() -> None:
    occ = capacity.parse_occupancy(_metrics(running=2.0, queue=0.0, token_usage=0.03))
    assert occ.running_reqs == 2.0
    assert occ.queue_reqs == 0.0
    assert occ.token_usage == pytest.approx(0.03)
    expected = max(0.03, 2.0 / config.NODE_RUNNING_CAPACITY)
    assert occ.occupancy == pytest.approx(expected)


def test_parse_occupancy_high_kv_dominates() -> None:
    occ = capacity.parse_occupancy(_metrics(running=1.0, queue=0.0, token_usage=0.72))
    assert occ.occupancy == pytest.approx(0.72)


def test_parse_occupancy_clamps_to_one() -> None:
    occ = capacity.parse_occupancy(
        _metrics(running=float(config.NODE_RUNNING_CAPACITY) * 4, queue=0.0, token_usage=0.0)
    )
    assert occ.occupancy == pytest.approx(1.0)


def _mock_client(sequence: list[str], counter: dict[str, int]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        index = min(counter["n"], len(sequence) - 1)
        counter["n"] += 1
        return httpx.Response(200, text=sequence[index])

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_limiter_admits_immediately_when_below_ceiling() -> None:
    counter = {"n": 0}

    async def run() -> None:
        async with _mock_client([_metrics(1.0, 0.0, 0.05)], counter) as client:
            limiter = capacity.CapacityLimiter(
                client,
                "http://x/metrics",
                ceiling=0.30,
                concurrency=2,
                poll_interval_s=0.01,
                wait_timeout_s=1.0,
            )
            async with limiter.slot():
                pass

    asyncio.run(run())
    assert counter["n"] == 1


def test_limiter_waits_until_occupancy_drops() -> None:
    counter = {"n": 0}
    seq = [_metrics(30.0, 5.0, 0.9), _metrics(30.0, 5.0, 0.9), _metrics(1.0, 0.0, 0.02)]

    async def run() -> None:
        async with _mock_client(seq, counter) as client:
            limiter = capacity.CapacityLimiter(
                client,
                "http://x/metrics",
                ceiling=0.30,
                concurrency=1,
                poll_interval_s=0.01,
                wait_timeout_s=5.0,
            )
            async with limiter.slot():
                pass

    asyncio.run(run())
    assert counter["n"] == 3


def test_limiter_proceeds_when_metrics_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            limiter = capacity.CapacityLimiter(
                client,
                "http://x/metrics",
                ceiling=0.30,
                concurrency=1,
                poll_interval_s=0.01,
                wait_timeout_s=0.2,
            )
            async with limiter.slot():
                pass

    asyncio.run(run())


def test_ensure_precheck_passes_when_headroom_available() -> None:
    counter = {"n": 0}

    async def run() -> capacity.NodeOccupancy | None:
        async with _mock_client([_metrics(1.0, 0.0, 0.05)], counter) as client:
            return await capacity.ensure_precheck(
                client,
                "http://x/metrics",
                max_occupancy=0.50,
                poll_interval_s=0.01,
                wait_timeout_s=1.0,
            )

    occ = asyncio.run(run())
    assert occ is not None
    assert occ.occupancy < 0.50


def test_ensure_precheck_raises_when_node_stays_busy() -> None:
    counter = {"n": 0}

    async def run() -> None:
        async with _mock_client([_metrics(1.0, 0.0, 0.85)], counter) as client:
            await capacity.ensure_precheck(
                client,
                "http://x/metrics",
                max_occupancy=0.50,
                poll_interval_s=0.01,
                wait_timeout_s=0.2,
            )

    with pytest.raises(capacity.CapacityError):
        asyncio.run(run())
