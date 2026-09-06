import asyncio
import re
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
from pydantic import BaseModel

from app.ml import config

_GAUGE_LINE = re.compile(r"^(?P<name>sglang:[a-z0-9_]+)\{(?P<labels>[^}]*)\}\s+(?P<value>\S+)\s*$")


class CapacityError(RuntimeError):
    pass


class NodeOccupancy(BaseModel):
    running_reqs: float
    queue_reqs: float
    token_usage: float
    occupancy: float

    def describe(self) -> str:
        return (
            f"occupancy={self.occupancy:.0%} "
            f"(kv={self.token_usage:.0%}, running={self.running_reqs:.0f}, "
            f"queue={self.queue_reqs:.0f})"
        )


def metrics_url_from_base(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/v1"):
        trimmed = trimmed[: -len("/v1")]
    return f"{trimmed}/metrics"


def _scalar(values: dict[str, float], name: str, default: float = 0.0) -> float:
    return values.get(name, default)


def _read_gauges(metrics_text: str) -> dict[str, float]:
    preferred: dict[str, float] = {}
    fallback: dict[str, float] = {}
    for line in metrics_text.splitlines():
        match = _GAUGE_LINE.match(line.strip())
        if match is None:
            continue
        name = match.group("name")
        try:
            value = float(match.group("value"))
        except ValueError:
            continue
        if value != value:
            continue
        labels = match.group("labels")
        if 'tp_rank="0"' in labels:
            preferred.setdefault(name, value)
        else:
            fallback.setdefault(name, value)
    return {**fallback, **preferred}


def parse_occupancy(metrics_text: str) -> NodeOccupancy:
    gauges = _read_gauges(metrics_text)
    running = _scalar(gauges, "sglang:num_running_reqs")
    queue = _scalar(gauges, "sglang:num_queue_reqs")
    kv = max(
        _scalar(gauges, "sglang:token_usage"),
        _scalar(gauges, "sglang:full_token_usage"),
    )
    running_pressure = (running + queue) / max(1.0, float(config.NODE_RUNNING_CAPACITY))
    occupancy = min(1.0, max(kv, running_pressure))
    return NodeOccupancy(
        running_reqs=running,
        queue_reqs=queue,
        token_usage=kv,
        occupancy=occupancy,
    )


async def read_occupancy(
    client: httpx.AsyncClient,
    metrics_url: str,
    timeout_s: float = config.CAPACITY_METRICS_TIMEOUT_S,
) -> NodeOccupancy | None:
    try:
        response = await client.get(metrics_url, timeout=timeout_s)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    return parse_occupancy(response.text)


async def ensure_precheck(
    client: httpx.AsyncClient,
    metrics_url: str,
    max_occupancy: float = config.NODE_PRECHECK_MAX_OCCUPANCY,
    poll_interval_s: float = config.CAPACITY_POLL_INTERVAL_S,
    wait_timeout_s: float = config.CAPACITY_WAIT_TIMEOUT_S,
    on_status: Callable[[str], None] | None = None,
) -> NodeOccupancy | None:
    deadline = asyncio.get_event_loop().time() + wait_timeout_s
    while True:
        occupancy = await read_occupancy(client, metrics_url)
        if occupancy is None:
            if on_status is not None:
                on_status(f"capacity precheck: metrics unreachable at {metrics_url}, proceeding")
            return None
        if occupancy.occupancy < max_occupancy:
            if on_status is not None:
                on_status(f"capacity precheck OK: {occupancy.describe()} < {max_occupancy:.0%}")
            return occupancy
        if asyncio.get_event_loop().time() >= deadline:
            raise CapacityError(
                f"node still busy: {occupancy.describe()} >= {max_occupancy:.0%} "
                f"after {wait_timeout_s:.0f}s"
            )
        if on_status is not None:
            on_status(f"capacity precheck waiting: {occupancy.describe()} >= {max_occupancy:.0%}")
        await asyncio.sleep(poll_interval_s)


class CapacityLimiter:
    def __init__(
        self,
        client: httpx.AsyncClient,
        metrics_url: str,
        ceiling: float = config.NODE_OCCUPANCY_CEILING,
        concurrency: int = config.ACTOR_MAX_CONCURRENCY,
        poll_interval_s: float = config.CAPACITY_POLL_INTERVAL_S,
        wait_timeout_s: float = config.CAPACITY_WAIT_TIMEOUT_S,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        self._client = client
        self._metrics_url = metrics_url
        self._ceiling = ceiling
        self._semaphore = asyncio.Semaphore(max(1, concurrency))
        self._poll_interval_s = poll_interval_s
        self._wait_timeout_s = wait_timeout_s
        self._on_status = on_status

    async def _await_headroom(self) -> None:
        deadline = asyncio.get_event_loop().time() + self._wait_timeout_s
        while True:
            occupancy = await read_occupancy(self._client, self._metrics_url)
            if occupancy is None or occupancy.occupancy < self._ceiling:
                return
            if asyncio.get_event_loop().time() >= deadline:
                if self._on_status is not None:
                    self._on_status(
                        f"capacity gate timeout: {occupancy.describe()} still >= "
                        f"{self._ceiling:.0%}, proceeding"
                    )
                return
            if self._on_status is not None:
                self._on_status(
                    f"capacity gate holding: {occupancy.describe()} >= {self._ceiling:.0%}"
                )
            await asyncio.sleep(self._poll_interval_s)

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        async with self._semaphore:
            await self._await_headroom()
            yield
