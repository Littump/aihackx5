# ML-rework: LLM-планировщик персональных челленджей (принято)

Материалы переработки ML-части «Домового». Статус — **принято и смёрджено** в продукт (`docs/product-analysis/`),
решения (`dev/docs/decisions.md` #15) и backlog (эпик `dev/docs/backlog/E14-ml-planner.md`) после сверки с
видением продукт-овнера (`docs/demo/`). Код внедряется по задачам E14; сами эти документы — источник дизайна.

| Документ | О чём |
|---|---|
| [ml-rework-explained.md](ml-rework-explained.md) | **Start here.** Plain-language walkthrough of the whole ML side (in English): the big picture first, then a deep dive per component; every term is explained on first use. |
| [ml-solution-architecture.md](ml-solution-architecture.md) | Целевая ML-архитектура: Insight Builder → LLM Challenge Planner (structured output, tool-use; `reward_kind` promo/ladder/none + многошаговый план `steps[]` (cap 2)) → Validator → статические Economics/Reward Ladder; фиксированный каталог SKU; синтетическая eval **продолжением истории** (обрезка в точке T, LLM-as-user дописывает хвост, деньги считает код — без LLM-судьи). С обоснованием и ссылками на research. |
| [product-and-architecture-modifications.md](product-and-architecture-modifications.md) | Карта влияния на уже принятую архитектуру/продукт: сдвиг роли LLM, новые модули и таблицы, константы, контракт, backlog, порядок внедрения, вопросы продукт-овнеру. |
| [actor-and-tracing.md](actor-and-tracing.md) | Синтетический покупатель: «пиковые» профили и снятие лояльности актёра, строгий выход (thinking+rationale+verdict), трейсы прогонов и экспорт в Langfuse, заметка про длину симуляции. |
| [metrics-explained.md](metrics-explained.md) | Метрики eval простыми словами: что такое бизнес-метрики (net_effect, incr.visits, uplift) и системные (completion, relevance hit, llm plans), и что из этого мы оптимизируем. |

## Суть в одном абзаце

Вместо hand-rolled рекоммендера (`candidate.build` + `personalization.rank`) — дешёвая LLM-аналитик,
которая читает подготовленный кодом инсайт по пользователю (агрегаты + товарный time-series + сигнал оттока)
и **планирует** следующий персональный челлендж из фиксированной библиотеки поверх фиксированного каталога SKU,
возвращая строгую схему (Anthropic tool-use forcing). Планировщик выбирает форму награды (`reward_kind`:
промо-деньги, бонус-XP reward ladder или `none` — самоценный челлендж), думает на несколько шагов вперёд (`steps[]`, cap 2, активен только `steps[0]`)
и адаптируется по своим прошлым ходам (`previous_plans`); часть челленджей самоценна
и не тратит бюджет. Деньги считает прежний статический Economics Engine по марже (LLM задаёт лишь ординальный
`reward_level`), XP — Reward Ladder. Проверяем поведенчески: LLM-as-user генерирует полную историю профиля,
обрезаем её в точке T, подставляем оффер, LLM-as-user дописывает хвост, и выручку/маржу считает код по формулам
продукт-овнера — **без LLM-судьи**, сравнивая наш оффер с baseline-оффером X5.
