# ML-rework: LLM-планировщик персональных челленджей (принято)

Материалы переработки ML-части «Домового». Статус — **принято и смёрджено** в продукт (`docs/product-analysis/`),
решения (`dev/docs/decisions.md` #15) и backlog (эпик `dev/docs/backlog/E14-ml-planner.md`) после сверки с
видением продукт-овнера (`docs/demo/`). Код внедряется по задачам E14; сами эти документы — источник дизайна.

| Документ | О чём |
|---|---|
| [ml-rework-explained.md](ml-rework-explained.md) | **Start here.** Plain-language walkthrough of the whole ML side (in English): the big picture first, then a deep dive per component; every term is explained on first use. |
| [ml-solution-architecture.md](ml-solution-architecture.md) | Целевая ML-архитектура: Insight Builder → LLM Challenge Planner (structured output, tool-use; `reward_kind` promo/ladder/none + многошаговый план `steps[]` (cap 2)) → Validator → статические Economics/Reward Ladder; фиксированный каталог SKU; синтетическая eval **продолжением истории** (обрезка в точке T, LLM-as-user дописывает хвост, деньги считает код — без LLM-судьи). С обоснованием и ссылками на research. |
| [product-and-architecture-modifications.md](product-and-architecture-modifications.md) | Карта влияния на уже принятую архитектуру/продукт: сдвиг роли LLM, новые модули и таблицы, константы, контракт, backlog, порядок внедрения, вопросы продукт-овнеру. |
| [actor-and-tracing.md](actor-and-tracing.md) | Синтетический покупатель: «пиковые» профили и снятие лояльности актёра, строгий выход (thinking+rationale+verdict), **многонедельный чат по неделям** (KV-cache, прогрессия по T, fast-forward), трейсы прогонов и экспорт в Langfuse (понедельные метрики и графики). |
| [planner-v2-explained.md](planner-v2-explained.md) | **Planner v2, start here (English).** Plain-language proposal for the next planner: staged sections in one AI call (think → name the buyer → goal → insights → challenges → strategy), glossary-first. Classification **names the buyer** from a closed keyword palette (one lifecycle + modifiers); the goal picks one of **two** targets (visit_frequency / basket_value) plus a proxy lever; reward is two currencies (XP always + X5 points when the budget allows, never none). |
| [planner-v2-classification-insights.md](planner-v2-classification-insights.md) | Planner v2 — точный дизайн (RU, proposal, код не меняется): **устаревшее оформление** (Family A `engagement` как ранжированный массив + 4 target’а) — ещё не синхронизировано с v2-фреймворком «name the buyer» + 2 target + proxy + reward XP/X5-points из EN-доков; переписывается отдельно. Пока источник v2-дизайна — `planner-v2-taxonomy-and-examples.md`. |
| [planner-v2-taxonomy-and-examples.md](planner-v2-taxonomy-and-examples.md) | Planner v2 — таксономия (English, **источник истины по v2**): research-обоснование (2026 RFM/CDP), «name the buyer» из закрытой палитры ключевых слов (один lifecycle + модификаторы), стадия goal с **двумя** target’ами (`visit_frequency`/`basket_value`) + `proxy`-рычаги + `direction`, двухвалютная награда (`xp_level` всегда + `points_level`, никогда не пусто), derived-фичи и карта «метрика → keyword», правила выбора goal, библиотека видов инсайтов и few-shot примеры (анти-галлюцинация, 5 канонических типов челленджа без `streak`). |
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
