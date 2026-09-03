import pytest

from app.core.errors import AppError
from app.features.users.pseudonyms import (
    ADJECTIVES,
    NOUNS,
    PSEUDONYM_MAX_ATTEMPTS,
    generate_unique_pseudonym,
)

PSEUDONYM_SAMPLE_SIZE = 1000


async def test_generates_1000_unique_pseudonyms() -> None:
    seen: set[str] = set()

    async def is_taken(candidate: str) -> bool:
        return candidate in seen

    for _ in range(PSEUDONYM_SAMPLE_SIZE):
        pseudonym = await generate_unique_pseudonym(is_taken)
        assert pseudonym not in seen
        seen.add(pseudonym)

    assert len(seen) == PSEUDONYM_SAMPLE_SIZE


async def test_generated_pseudonym_combines_known_words() -> None:
    async def never_taken(_: str) -> bool:
        return False

    pseudonym = await generate_unique_pseudonym(never_taken)
    adjective, noun = pseudonym.split(" ", 1)
    assert adjective in ADJECTIVES
    assert noun in NOUNS


def test_word_lists_have_forty_unique_words() -> None:
    assert len(ADJECTIVES) == len(set(ADJECTIVES)) == 40
    assert len(NOUNS) == len(set(NOUNS)) == 40


async def test_raises_after_exhausting_max_attempts() -> None:
    call_count = 0

    async def always_taken(_: str) -> bool:
        nonlocal call_count
        call_count += 1
        return True

    with pytest.raises(AppError) as exc_info:
        await generate_unique_pseudonym(always_taken)

    assert call_count == PSEUDONYM_MAX_ATTEMPTS
    assert exc_info.value.code == "pseudonym_generation_failed"
    assert exc_info.value.status == 500
