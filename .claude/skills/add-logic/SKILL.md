---
name: add-logic
description: Добавить или изменить бизнес-логику в слое service — расчёт, правило, обработчик события — с числами из game_rules.py и unit-тестами. Использовать на «добавь логику», «посчитай», «реализуй правило», «обработай событие», «economics engine», «fraud score», «league score», «сделай сервисную функцию», «добавь формулу».
argument-hint: <feature и что считаем>
---

# add-logic — логика в service

## Шаги

1. **Найти правило.** Открыть `dev/docs/domain-rules.md` — там формула и числовой пример. Если правила нет — сначала дописать его туда (одна формула, один пример), потом код. Числа — в `app/game_rules.py` как константы с говорящими именами.
2. **Выбрать место.** Логика живёт в `service.py` того feature, которому принадлежит результат: расчёт награды — `challenges`, фрод-скор — `antifraud`, score лиги — `league`. Чистые вычисления без базы выносить в отдельный модуль внутри feature (`economics.py`, `scoring.py`) — так их проще тестировать.
3. **Сигнатура.** Чистые функции принимают скаляры или модели из `models.py`, а не `conn`: `def max_reward_points(*, baseline: float, target: float, avg_basket: Decimal) -> int`, `def evaluate(draft: ChallengeDraft, features: UserFeatures) -> ChallengeEconomics`. Результат с несколькими полями — всегда pydantic-модель в `models.py`, не кортеж и не `dict`. Функции с базой принимают `conn` первым аргументом и вызывают `database.py`.
4. **Событийная логика.** Обработка чека (`receipts/service.process_receipt`) вызывает сервисы соседей в фиксированном порядке из `architecture.md`. Порядок менять нельзя без правки документа.
5. **Unit-тесты.** `tests/unit/<feature>/test_<module>.py`: пример из `domain-rules.md` как первый тест (входы и ожидаемое число один-в-один), границы (ноль, отрицательные, пустой список), лимиты (минимум и максимум награды).
6. **Время.** Если логика зависит от «сейчас» (неделя, дедлайн, recency) — только `app.core.clock`; в тестах `freeze_time`.
7. **Проверка.** `make check`, `uv run pytest tests/unit -q`.

## Пример: economics engine

`domain-rules.md`: baseline 2 покупки/нед, target 3, средний чек 600 ₽, contribution margin 15 % → expected incremental margin 90 ₽ → максимум награды 40 % → 36 ₽ → выдаём 30 баллов (кратно 10, не ниже минимума 30).

```python
def test_max_reward_matches_prd_example():
    assert max_reward_points(baseline=2, target=3, avg_basket=Decimal("600")) == 30
```

## Чего не делать

- Не пересчитывать «по-своему» то, что уже есть в другом feature. Нужны features пользователя — вызывать `features/service.get_user_features`.
- Не смешивать чтение из базы и вычисление в одной функции, если вычисление можно выделить.
- Не звать LLM из логики. LLM получает результат логики и пишет текст.
