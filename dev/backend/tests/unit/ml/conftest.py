from collections.abc import AsyncIterator

import pytest


@pytest.fixture(scope="session", autouse=True)
async def migrated_db() -> None:
    return None


@pytest.fixture(autouse=True)
async def clean_tables() -> AsyncIterator[None]:
    yield
