from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.features.challenges import database, service
from app.features.challenges.models import ChallengeDraft, ChallengeRow
from app.features.user_features import service as user_features_service
from app.features.user_features.models import CategoryAffinity, UserFeaturesRow
from app.features.users import service as users_service
from app.features.users.models import UserRow
from app.llm import domovoy_copy
from tests.unit.challenges.data import make_challenge_row, make_features, make_user_row

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


async def test_refresh_weekly_expires_builds_ranks_and_inserts_hero_and_side(
    monkeypatch: pytest.MonkeyPatch, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    features = make_features(
        frequency_per_week=Decimal("2"),
        recency_days=5,
        avg_basket=Decimal("600"),
        category_affinity={"dairy": CategoryAffinity(share=0.30, visits=6, cadence_days=5.0)},
    )
    expire_calls: list[int] = []
    insert_calls: list[dict[str, object]] = []
    render_calls: list[str] = []
    result_rows = [
        make_challenge_row(id=1, is_hero=True),
        make_challenge_row(id=2, is_hero=False, type="category", category="dairy"),
    ]

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return make_user_row(user_id=user_id)

    async def fake_expire(_: AsyncConnection, *, user_id: int) -> None:
        expire_calls.append(user_id)

    async def fake_features_get(_: AsyncConnection, user_id: int) -> UserFeaturesRow:
        return features

    async def fake_render(
        *, challenge: ChallengeDraft, features: UserFeaturesRow
    ) -> domovoy_copy.ChallengeCopy:
        render_calls.append(challenge.type)
        return domovoy_copy.ChallengeCopy(title="T", body="B", explanation="E", source="template")

    async def fake_insert(_: AsyncConnection, **kwargs: object) -> ChallengeRow:
        insert_calls.append(kwargs)
        return result_rows[len(insert_calls) - 1]

    async def fake_list(_: AsyncConnection, *, user_id: int) -> list[ChallengeRow]:
        return result_rows

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(database, "expire_active_challenges", fake_expire)
    monkeypatch.setattr(user_features_service, "get", fake_features_get)
    monkeypatch.setattr(domovoy_copy, "render_challenge", fake_render)
    monkeypatch.setattr(database, "insert_challenge", fake_insert)
    monkeypatch.setattr(database, "list_challenges_by_user", fake_list)

    result = await service.refresh_weekly(None, 1)  # type: ignore[arg-type]

    assert expire_calls == [1]
    assert len(insert_calls) == 2
    assert insert_calls[0]["is_hero"] is True
    assert isinstance(insert_calls[0]["draft"], ChallengeDraft)
    assert insert_calls[0]["draft"].type == "frequency"
    assert insert_calls[0]["period_start"] == week_start(NOW)
    assert insert_calls[0]["period_end"] == week_end(NOW)
    assert insert_calls[0]["reward_points"] == 30
    assert insert_calls[1]["is_hero"] is False
    assert isinstance(insert_calls[1]["draft"], ChallengeDraft)
    assert insert_calls[1]["draft"].type == "category"
    assert render_calls == ["frequency", "category"]
    assert result.hero == result_rows[0]
    assert result.side == [result_rows[1]]
