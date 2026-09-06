# Планировщик v2: классификация → инсайты → портфель челленджей

> Статус: **черновик архитектуры (proposal), код не меняется**. Это переработка
> ML-планировщика из [ml-solution-architecture.md](ml-solution-architecture.md).
> Числа — `simulation assumptions`, игровые константы живут в `dev/backend/app/game_rules.py`.
> Цель документа: зафиксировать целевую архитектуру до кода, дать конкретные схемы,
> критику и план проверки. Реализация — отдельной задачей после ревью.

## 0. TL;DR

Сегодня планировщик — один констрейнед-вызов без рассуждения (`enable_thinking: False`),
который сразу отдаёт `steps[]` + одну строку `rationale`. Он не проговаривает, **кем** он
считает пользователя, а «инсайт» — это входные фичи, а не вывод модели.

Предлагается развернуть вывод в **явные стадии рассуждения, зашитые в порядок полей схемы**:

1. **thinking** — настоящее свободное рассуждение (reasoning trace), не констрейнится.
2. **classification** — описание поведения: `engagement` — **один плоский ранжированный список**
   поведенческих сигналов (сильный первым, каждый со `score` и derived-метрикой) + `posture`
   (ценовая позиция, одна). Никаких под-групп — просто сигналы, отсортированные по силе; «несколько
   типов» = несколько высоких score.
3. **goal** — статистический пред-анализ *между* классификацией и инсайтами: одна фича, которую
   оптимизируем на этой неделе (`visit_frequency`/`basket_value`/`basket_breadth`/
   `category_reengagement`) + направление (`increase`/`recover`/`sustain`). Отделяет «что видим»
   (classification) от «что делаем» (goal), напр.: «частота падает → recover visit_frequency» либо
   «частота у потолка, но корзина крупная → increase basket_value».
4. **insights[]** — массив именованных инсайтов строгой формы `name / behaviour / dod /
   strategy_hint`, обосновывающих достижение goal.
5. **challenges[]** — несколько челленджей за один шаг; каждый ссылается на `insight` по имени
   (проверяемо кодом); механика hero совпадает с `goal.target`.
6. **general_strategy** — общий rationale, ссылающийся на **все** имена инсайтов и на goal.

Порядок полей = порядок генерации при constrained decoding, поэтому схема сама ведёт модель
по стадиям. Ссылки «челлендж → инсайт» и «стратегия → инсайты» делаем **структурными**
(списки имён), а не регуляркой по числам в тексте — и валидируем детерминированно.

Проверка — маленький **классификационный eval** по срезу пользователей разных сегментов:
planner-only, без симуляции покупателя, сверяем топ-сигнал `engagement[0]` с наблюдаемым
поведением и целостность ссылок инсайтов.

---

## 1. Что не так сегодня (с привязкой к коду)

- **Рассуждение выключено.** `dev/backend/app/ml/llm_client.py` в `emit_json` шлёт
  `chat_template_kwargs={"enable_thinking": False}`. Планировщик не думает — он сразу
  эмитит JSON. Единственная «мысль» — поле `rationale` (<=200 символов).
- **Нет стадии классификации.** `dev/backend/app/ml/planner.py` → `plan_challenge` отдаёт
  `ChallengePlan` (`schemas.py`): `steps[]`, `insight_used: list[str]`, `rationale`. Модель
  нигде не фиксирует свой «портрет» пользователя. Сегмент (`regular_mid/light/heavy/dormant`)
  приходит на вход (`PlannerInput.user.segment`), то есть классификация подменена входной
  меткой.
- **«Инсайт» — это фичи, а не вывод.** `dev/backend/app/ml/insight.py` `build_insight`
  собирает `PlannerFeatures` + `category_timeseries`. Это вход планировщика. Поле
  `insight_used` в выводе — просто список строк-ключей, ни к чему не привязанный.
- **Связь «челлендж → инсайт» не проверяема.** Валидатор
  (`dev/backend/app/ml/validator.py` `_rationale_has_insight_number`) проверяет лишь, что в
  `rationale` есть **какое-то** число из инсайта (`_insight_numbers`). Это не доказывает, что
  челлендж следует из конкретного наблюдения — модель может вписать любое совпавшее число.
- **Один челлендж на выход.** `MAX_PLAN_STEPS = 2` (`config.py`), при этом `steps[1]` —
  внутренняя заметка на следующую неделю, пользователю показывается только `steps[0]`
  (см. `planner_system.md` и `langfuse_export.py` `planner_strategy_view`, который читает
  `steps[0]`). Отдать пользователю набор челленджей за шаг сейчас нельзя.
- **Хорошая новость (не ломать).** Стратегия уже описана прозой в
  `dev/backend/app/ml/prompts/planner_system.md` пятью шагами (mechanic → category → target →
  reward → continuity). По трейсам таргетинг сильный: relevance_hit 98% против 26% у
  rule-fallback (`docs/ml-rework/eval-findings.md`). Слабое место — не релевантность, а
  экономика награды и доказуемость. Переработку строим как **надстройку над этой логикой**, а
  не замену.

---

## 2. Целевой конвейер: schema-guided reasoning по стадиям

Один вызов планировщика, но его выход — не «ответ», а **протокол рассуждения**, где каждая
секция обязана появиться до следующей. Порядок объявления свойств в JSON-схеме = порядок их
генерации при constrained decoding (xgrammar/outlines/guidance генерируют ключи объекта строго
в порядке `properties`). Поэтому сама схема заставляет модель:

```
thinking ─▶ classification ─▶ goal ─▶ insights[] ─▶ challenges[] ─▶ general_strategy
(свободно)  (плоский ранж.    (что     (что вижу и    (что делаю,      (почему всё это
            список сигналов   опти-    почему это     ссылка на        вместе, все
            + posture)        мизи-    важно для      инсайт; hero =   инсайты + goal)
                              руем)    goal)          goal.target)
```

Стадии:

1. **thinking** — свободный reasoning (см. §3). Не констрейнится грамматикой, здесь живёт
   «настоящее мышление»: перебор гипотез о пользователе, взвешивание сигналов, отбраковка.
2. **classification** — описание поведения (§5): один **плоский** ранжированный список сигналов
   `engagement` + одна `posture`. Никаких под-групп; «несколько типов» = несколько высоких score.
3. **goal** — статистический пред-анализ (§5а): одна `target`-фича + `direction`. Что именно
   двигаем, выбранное детерминированно из сигналов, до построения факт-инсайтов.
4. **insights** — массив именованных инсайтов (§6), обосновывающих достижение goal. Каждый —
   гипотеза «наблюдение → цель → как двигать».
5. **challenges** — один или несколько челленджей (§7); каждый структурно ссылается на инсайт
   по `name`, механика hero = `goal.target`.
6. **general_strategy** — сводный rationale (§7), ссылающийся на все имена инсайтов и на goal,
   плюс план на следующую неделю.

Это соответствует «schema guided reasoning through rigorous stages», при этом «real thinking»
остаётся живым в стадии 1.

---

## 3. Реальное мышление рядом со строгим JSON

Исследование транспорта (vLLM structured outputs + reasoning):

- Текущий код уже использует правильный современный путь — `response_format` типа
  `json_schema` со `strict: true` (см. `llm_client.emit_json`). Устаревшие `guided_json` в
  vLLM 0.12 удалены; менять транспорт не нужно, только параметры.
- **Нативное совмещение reasoning + structured output.** Если vLLM запущен с
  `--reasoning-parser qwen3` (для Qwen3) или `deepseek_r1` (для DeepSeek-R1-подобных), сервер
  оставляет `<think>…</think>` **без** грамматической маски и включает JSON-грамматику только
  после конца рассуждения (`reasoning_ended`). Свободная мысль уезжает в отдельное поле
  `message.reasoning` (раньше `reasoning_content`), а `message.content` остаётся валидным JSON.
  Один вызов — и живое рассуждение, и валидная схема.
  - Источник: `vllm/v1/structured_output/__init__.py` (gate `reasoning_ended`), vLLM
    Reasoning Outputs docs. Для Qwen3-Coder есть флаг-нюанс
    `--structured-outputs-config.enable_in_reasoning=True`.
- **Defense-in-depth (модель/парсер без нативной поддержки).** Дополнительно держим `thinking`
  **первым строковым полем** схемы. Даже без reasoning-парсера модель «думает» в этом поле до
  того, как грамматика заставит её зафиксировать классификацию. CoT-поле эмпирически заметно
  поднимает качество (Instructor: reasoning-first схема даёт большой прирост на reasoning-задачах).
- **Крайний fallback** — два вызова (свободно рассудить → отформатировать), но это ×2 латентность
  и разрыв связности; берём только если конкретная пара модель+парсер не поддерживает нативный
  gate.

**Решение для нашего стека:** на планировщике (Qwen) убрать `enable_thinking: False`, включить
`--reasoning-parser qwen3` на сервере, писать `message.reasoning` в трейс как аудит честности
рассуждения, и одновременно оставить `thinking` первым полем схемы как страховку. Температуру
держим детерминированной для воспроизводимости eval; `max_tokens` поднять (see §12), т.к. вывод
стал больше (рассуждение + инсайты + несколько челленджей).

Замечание по инфраструктуре: reasoning-парсер и флаги — это изменение запуска vLLM на
инференс-узле. Любые действия на узле — строго по правилам `.codex/skills/inference-node/SKILL.md`
и только с явного разрешения (адрес/пароль узла — там). В самом планировщике reasoning-first-поле
работает и без серверного флага, поэтому редизайн не блокируется доступом к узлу.

---

## 4. Новая схема вывода (pydantic v2, набросок)

Имена полей — английские (правило репозитория), доктстрингов нет (правило NO-COMMENTS).
Это целевой контракт `dev/backend/app/ml/schemas.py`; JSON-схема для vLLM зеркалится в
`tool_schemas.py`.

```python
EngagementSignal = Literal[        # Family A: ранжируемые поведенческие сигналы (не метка)
    "rising",                      # чаще ходит в последнее время (visit_momentum)
    "steady_core",                 # рутина как часы, в цикле (cadence_regularity + overdue_ratio)
    "cooling",                     # выпадает из цикла, ещё достижим (overdue_ratio 1.2..2.6)
    "lapsing",                     # долгий разрыв, почти потерян (overdue_ratio > 2.6)
    "visit_headroom",              # активен, есть место для +1 визита (visit_headroom_ratio)
    "basket_depth",                # крупная широкая корзина, есть куда углублять (basket_index)
    "category_gap",                # выпала конкретная нужная категория (top_category_overdue_ratio)
]

PricePosture = Literal[           # Family B: движок награды (форма + уровень)
    "promo_immune",               # к промо равнодушен, рутина > скидки
    "value_selective",            # реагирует только на реальную своевременную нужду
    "deal_driven",                # гонится за выгодой
]


class EngagementTag(BaseModel):
    signal: EngagementSignal
    score: float = Field(ge=0.0, le=1.0)         # сила сигнала из derived-метрики (Part 1b таксономии)
    evidence_metric: str = Field(max_length=80)  # метрика-источник, напр. overdue_ratio=2.83


class Classification(BaseModel):
    engagement: list[EngagementTag] = Field(min_length=1, max_length=4)  # ранжирован по score, сильный первым
    posture: PricePosture                            # Family B, ведёт награду (обязателен)
    is_ambiguous: bool                      # top-2 score в пределах ~0.15
    summary: str = Field(max_length=240)


class Insight(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{2,39}$")   # snake_case, стабильный якорь
    behaviour: str = Field(max_length=240)   # что видим сейчас (наблюдение)
    dod: str = Field(max_length=240)         # каким хотим видеть поведение (definition of done)
    strategy_hint: str = Field(max_length=240)  # что теоретически можно сделать
    evidence_metric: str = Field(max_length=80)  # ключ/число из инсайта-входа


class ChallengeDraft(BaseModel):
    insight_ref: str                          # == Insight.name (валидируется)
    challenge_type: ChallengeType
    target: int
    category: str | None
    sku_refs: list[str] = Field(default_factory=list, max_length=3)
    reward_kind: RewardKind
    reward_level: RewardLevel
    deadline_days: int
    role: Literal["hero", "side"]             # ровно один hero, остальные side
    rationale: str = Field(max_length=240)    # почему этот шаг закрывает insight_ref


class GeneralStrategy(BaseModel):
    insight_refs: list[str] = Field(min_length=1)  # обязано покрыть ВСЕ Insight.name
    rationale: str = Field(max_length=600)
    next_week_hint: str = Field(max_length=240)


class PlannerReasoning(BaseModel):
    thinking: str = Field(max_length=2000)    # первое поле = «думаем» до фиксации
    classification: Classification
    insights: list[Insight] = Field(min_length=2, max_length=4)
    challenges: list[ChallengeDraft] = Field(min_length=1, max_length=MAX_CHALLENGES)
    general_strategy: GeneralStrategy
```

Ключевые отличия от текущего `ChallengePlan`:

- Добавлены `thinking`, `classification`, `insights` — стадии рассуждения в самой схеме.
- Классификация **двухосевая**, и ось вовлечённости — **ранжированный массив сигналов, а не одна
  метка**: `engagement` — Family A, список `{signal, score 0..1, evidence_metric}`,
  отсортированный по score (сильный первым); `engagement[0]` ведёт механику, `posture` — Family B
  (ценовая позиция, ведёт награду). Это прямой ответ на «варианты пересекаются / слишком мелкие
  или крупные»: пересечение выражается двумя высокими score, а не борьбой ярлыков; слабый сигнал
  просто оказывается внизу списка. Закрытые множества сигналов/позиций, derived-фичи, правила
  скоринга, библиотека инсайтов и few-shot — в
  [planner-v2-taxonomy-and-examples.md](planner-v2-taxonomy-and-examples.md) (источник истины по
  «что модели можно сказать» и «какая метрика на какой сигнал указывает»).
- **Вход обогащается derived-фичами.** `insight.build_insight` считает по истории визитов
  recency-взвешенные сигналы (`visit_momentum`, `overdue_ratio`, `cadence_regularity`,
  `visit_headroom_ratio`, `basket_index`, `category_breadth`, `top_category_overdue_ratio`) и
  кладёт их в `PlannerFeatures`. Числа считает код (LLM не считает), модель по ним ранжирует
  сигналы; тот же расчёт использует rule-fallback — см. Part 1b таксономии.
- `challenges[]` вместо `steps[]`; у каждого — `insight_ref` (проверяемая ссылка) и `role`.
- `general_strategy.insight_refs` обязан покрыть все `insights[].name` (см. §8).
- `insight_used: list[str]` из старой схемы уходит — его заменяют `insights[]` +
  `challenge.insight_ref` (структурно, а не свободные ключи).

---

## 5. Классификация: ранжированные сигналы + ценовая позиция

Требование пользователя (уточнённое): не одна перекрывающаяся метка, а **тип поведения, который
пользователь показывает в последнее время**, и **массив таких сигналов от сильного к слабому**;
плюс derived-фичи, которыми это измеримо, и явное соответствие «метрика → тип поведения».

- **Ось вовлечённости — ранжированный массив, а не метка (Family A).** `engagement` — список
  `EngagementTag{signal, score 0..1, evidence_metric}`, отсортированный по score (сильный первым);
  `engagement[0]` — де-факто primary и ведёт hero-механику, нижние — side-квесты. Закрытый набор
  из 7 сигналов делится на *траекторию* (`rising`/`steady_core`/`cooling`/`lapsing` — куда идёт
  недавнее поведение) и *возможности-рычаги* (`visit_headroom`/`basket_depth`/`category_gap` —
  что просить). Это чинит критику «варианты пересекаются / слишком мелкие/крупные»: старые 8
  плоских типов схлопываются в эти сигналы (`heavy_loyalist`≈`steady_core`+`basket_depth`,
  `winback_at_risk`≈`cooling`, `dormant_reactivation`≈`lapsing`, `frequency_headroom`≈
  `visit_headroom` и т.д.), а пересечение выражается двумя высокими score, а не борьбой ярлыков.
- **Recency-взвешенно.** «Что показывает *в последнее время*» задаётся окнами: recent = 28 дней,
  prior = предыдущие 28 (`visit_momentum`), и derived-метриками (`overdue_ratio` и др.). Так
  сигнал ловит недавний сдвиг, а не усреднение за всю историю (Part 1b таксономии).
- **Каждый сигнал измерим конкретной derived-метрикой.** У каждого `signal` в таксономии (Part
  2.1) есть колонка «measured by»: `rising`←`visit_momentum`, `cooling`/`lapsing`←`overdue_ratio`,
  `steady_core`←`cadence_regularity`, `visit_headroom`←`visit_headroom_ratio`,
  `basket_depth`←`basket_index`+`category_breadth`, `category_gap`←`top_category_overdue_ratio`.
  `evidence_metric` обязан указывать реальное значение этой метрики. Это и есть «явно сказать
  LLM, какая метрика — хороший источник для того или иного типа поведения».
- **Ценовая позиция — одна (Family B).** `posture` (`promo_immune`/`value_selective`/
  `deal_driven`) из `promo_sensitivity`, задаёт форму/уровень награды; в ранжирование не входит.
- **Отдельно от входного сегмента.** Входной `segment` (`regular_mid/light/heavy/dormant`) —
  грубая корзина на входе; `engagement` — поведенческий вывод по derived-сигналам. Классификация
  не должна просто переписывать `segment`: в eval (§14) у сегмента есть лишь ожидаемое множество
  правдоподобных `engagement[0]`, а не равенство.
- **Зачем downstream.** `engagement[0]` + `posture` — читаемый «руль» механики и награды, который
  сейчас спрятан в прозе промпта; score и `evidence_metric` дают судье/человеку критерий
  «правильно ли ранжировал и на чём».

---

## 6. Инсайты строгой формы

Каждый инсайт — маленькая проверяемая гипотеза. Строгая структура (запрос пользователя):

| поле | смысл | пример |
|---|---|---|
| `name` | стабильный snake_case якорь для ссылок | `dairy_lapsed_2w` |
| `behaviour` | что видим сейчас | «молочка не бралась 16 дней при цикле 6» |
| `dod` | каким хотим видеть поведение | «вернуть в молочку в ближайшую неделю» |
| `strategy_hint` | что теоретически можно | «replenishment на dairy, target=1, награда medium» |
| `evidence_metric` | конкретное число-якорь | `days_overdue=10` |

Правила:

- 2..4 инсайта: меньше — стадия вырождается, больше — модель «размазывает» и хуже
  конвертирует внимание.
- `dod` — это то, что делает инсайт **измеримым**: он же становится критерием релевантности и
  для eval, и для антидедвейт-логики (награждаем только за инкремент, а не за то, что купили бы
  и так — см. `eval-findings.md`).
- `evidence_metric` обязателен и проверяется кодом на «это реально число/ключ из входа», что
  надёжнее текущей регулярки по всему `rationale`.

---

## 7. Портфель челленджей и проверяемые ссылки

- **Несколько челленджей за шаг.** `challenges[]` = один `hero` (главный, показывается крупно)
  + 0..N `side` (побочные квесты). Это меняет `MAX_PLAN_STEPS`-модель: вместо «steps[0]
  пользователю, steps[1] на потом» — портфель на неделю с явной ролью каждого.
- **Каждый челлендж ссылается на инсайт.** `challenge.insight_ref` обязан совпадать с одним из
  `insights[].name`. Так «rationale references the named insight (verifiable)» — не проза, а
  структурная ссылка, которую валидатор проверяет множественно.
- **Общая стратегия ссылается на все инсайты.** `general_strategy.insight_refs` обязан быть
  **равен множеству** всех `insights[].name`. Если инсайт назван, но не использован ни в
  челлендже, ни в общей стратегии — это дефект плана (валидатор отметит), а не «свободный
  текст».
- **Бюджетный guardrail портфеля.** Несколько наград опасны для маржи. Держим:
  ровно один денежный (`promo`) челлендж — hero; `side`-квесты по умолчанию `ladder`/`none`
  (XP/самоценные, промо-бюджет не тратят); суммарная награда за неделю по-прежнему упирается в
  недельный потолок баллов (`game_rules`, сейчас 150) и в правило «денежная награда ≤ 40% от
  ожидаемой инкрементальной маржи» (decision из `ml-solution-architecture.md`). Это считает
  детерминированный код (`economics.py`), не LLM.

---

## 8. Валидатор: что проверяем детерминированно

Расширение `dev/backend/app/ml/validator.py` (форма проверок, не код):

- `challenge.insight_ref ∈ {insight.name}` для каждого челленджа; иначе — repair-фидбек модели.
- `set(general_strategy.insight_refs) == {insight.name}` (покрытие всех инсайтов).
- ровно один `role == "hero"`; не более одного `reward_kind == "promo"`.
- `classification.engagement`: 1..4 элементов, отсортирован по `score` desc, каждый `signal` из
  закрытого набора `EngagementSignal`, `score ∈ [0,1]`; ровно один `posture`; `is_ambiguous`
  согласован с зазором top-2 score (~0.15).
- `EngagementTag.evidence_metric` и `insight.evidence_metric` резолвятся в реальную derived/сырую
  метрику из `PlannerInput` в направлении, заданном таксономией (Part 2.1) — замена
  `_rationale_has_insight_number`, более строгая и адресная.
- существующие проверки сохраняются: `target` в коридоре (`rules.target_in_corridor`),
  `sku_refs` из каталога, категория из разрешённых, парность `reward_kind`/`reward_level`,
  `deadline_days` в [1;14].
- при провале — те же repair-итерации (`PLANNER_REPAIR_MAX`), при исчерпании — детерминированный
  fallback (§10).

Ссылочная целостность (insight_ref, покрытие) — это то, что делает связи «verifiable» в терминах
запроса: не совпадение числа в тексте, а граф «инсайт → челлендж/стратегия», который либо
согласован, либо нет.

---

## 9. Экономика и антидедвейт (без изменений по сути)

Экономику наград не трогаем принципиально: LLM выбирает только `reward_kind` + `reward_level`,
рубли/XP считает `economics.py`; инкремент и `net_effect` считает eval, кредит за «купил бы и
так» не даётся (`eval.py`, `eval-findings.md`). Новое — только портфельный guardrail из §7
(один promo, потолок недели, 40% маржи), т.к. челленджей теперь несколько.

---

## 10. Детерминированный fallback под новую форму

`dev/backend/app/ml/rules.py` (`fallback_plan`) должен собирать **ту же богатую форму**
`PlannerReasoning`, чтобы eval и демо работали без сети/ключа (жёсткое правило репозитория):

- `thinking` — короткая детерминированная строка («rule fallback: <причина>»).
- `classification.engagement` — тем же скорингом, что eval (Part 3 таксономии): код считает
  derived-метрики, мапит каждую в `score` монотонно, берёт топ-1..4 сигналов, сортирует по score.
  Траектория: `overdue_ratio>2.6`→`lapsing`; `1.2..2.6`→`cooling`; иначе `visit_momentum>1.15`→
  `rising`, else `steady_core`. Рычаги, что прошли порог: `category_gap`/`visit_headroom`/
  `basket_depth`. `posture` — из `promo_sensitivity` (`<0.35`→`promo_immune`,
  `0.35..0.62`→`value_selective`, `>=0.62`→`deal_driven`). `is_ambiguous` — по зазору top-2.
- `insights[]` — 2 инсайта из детерминированных сигналов (например `overdue_category`,
  `frequency_gap`), с честными `behaviour/dod/strategy_hint` из чисел.
- `challenges[]` — текущая rule-логика как один `hero`.
- `general_strategy.insight_refs` = имена этих инсайтов.

Так `plan_source == "rules"` остаётся полноценной веткой, а не деградацией схемы.

---

## 11. Трейсинг, Langfuse, judge

- **Трейс.** `tracing.py`/`langfuse_export.py`: `planner_strategy_view` должен читать
  `challenges[0]` (hero) + прикладывать `classification` и `insights[]` на корень трейса, а
  `message.reasoning` — как отдельное observation (сырое мышление рядом с распарсенным JSON,
  для проверки, что модель не читерит).
- **how_to_judge.** В `JUDGE_QUESTIONS` (`langfuse_export.py`) добавить вопросы новой
  архитектуры: (a) верен ли `engagement[0]` (и ранжирование) для наблюдаемого поведения; (b) обоснованы ли
  инсайты числами; (c) закрывает ли каждый челлендж свой `insight_ref`; (d) покрывает ли общая
  стратегия все инсайты.
- **LLM-as-judge.** `judge.py` получает новые дименшены: `judge_classification_fit`,
  `judge_insight_grounding`, `judge_reference_integrity` в дополнение к существующим. Судья —
  по-прежнему отдельная сильная модель (без self-grading).

---

## 12. Карта изменений в коде (для будущей задачи, не сейчас)

| Файл | Что меняется |
|---|---|
| `app/ml/insight.py` | новые derived-фичи в `PlannerFeatures` (`visit_momentum`, `overdue_ratio`, `cadence_regularity`, `visit_headroom_ratio`, `basket_index`, `category_breadth`, `top_category_overdue_ratio`) по окнам recent/prior 28д |
| `app/ml/schemas.py` | `PlannerFeatures` += derived-поля; новые модели `Classification` (ранж. `engagement`), `EngagementTag`, `Insight`, `ChallengeDraft`, `GeneralStrategy`, `PlannerReasoning`; enum'ы `EngagementSignal` (Family A) и `PricePosture` (Family B) |
| `app/ml/tool_schemas.py` | JSON-схема с порядком полей thinking→classification→insights→challenges→general_strategy |
| `app/ml/llm_client.py` | убрать `enable_thinking: False` для планировщика; читать `message.reasoning`; поднять `max_tokens` |
| `app/ml/planner.py` | парсить `PlannerReasoning`; передавать reasoning в трейс; repair-цикл под новые проверки |
| `app/ml/validator.py` | форма ранж. `engagement` (1..4, sort by score, закрытый enum, один posture); ссылочная целостность insight_ref/покрытие; один hero/один promo; evidence_metric резолвится |
| `app/ml/rules.py` | fallback собирает полную форму `PlannerReasoning` |
| `app/ml/prompts/planner_system.md` | переписать под стадии; текущие 5 шагов стратегии остаются как guidance внутри стадий |
| `app/ml/economics.py` | портфельный guardrail (один promo, потолок недели) при нескольких челленджах |
| `app/ml/config.py` | `MAX_CHALLENGES` вместо/вместе с `MAX_PLAN_STEPS`; константы derived-фич (`VISIT_CEILING`, `BASKET_REFERENCE`, окна recent/prior, пороги сигналов, зазор ambiguity) |
| `app/ml/tracing.py`, `langfuse_export.py`, `judge.py` | classification/insights в трейс; новые judge-дименшены |
| `dev/contracts/openapi.yaml` | если hero+side уходит в продуктовый API — контракт первым |

Продуктовые последствия (hero + side-квесты на главном экране) — синхронизировать с
`product-and-architecture-modifications.md` и эпиком E14 до реализации.

---

## 13. Критика предложенной архитектуры и что улучшить

Что в идее сильное:
- Явная классификация и именованные инсайты делают решение **читаемым и оцениваемым** — это
  прямой ответ на «непонятно, кем планировщик считает пользователя».
- Структурные ссылки (`insight_ref`, покрытие) надёжнее текущей регулярки по числу в тексте и
  дают настоящую верифицируемость.
- `dod` в инсайте — сильный ход: инсайт становится измеримой целью, стыкуется с антидедвейт-
  метрикой (награда за инкремент, а не за обычную покупку).
- Reasoning-first поле + reasoning-парсер — дёшево, воспроизводимо, оставляет «живое» мышление.

Риски и как их закрыть:
- **Гейминг ранжирования.** Модель может лепить длинный `engagement` со всеми сигналами низкого
  score, снимая с себя ответственность. → Жёсткий предел 1..4, включать сигнал только если его
  derived-метрика прошла порог (не «шум с низким score»), не более одной траектории без близкого
  второго; `is_ambiguous` только по зазору top-2 ~0.15; в eval штрафовать за раздутый массив.
- **Раздувание инсайтов.** Соблазн выдать 4 водянистых инсайта. → Жёсткий предел 2..4 +
  обязательный `evidence_metric` + judge-дименшен «grounding».
- **Бюджет на нескольких челленджах.** Несколько наград = риск слить маржу. → Ровно один promo,
  side-квесты `ladder`/`none`, недельный потолок и правило 40% маржи считает код (§7, §9).
- **Латентность/токены.** Рассуждение + инсайты + портфель — это в разы больше токенов;
  планировщик Qwen дешёвый, но `max_tokens` и таймаут надо пересчитать; иначе рост
  `fallback` (см. заметки про concurrency/таймауты в корневом AGENTS.md).
- **Стадии могут «зажать» мысль.** Если гейт reasoning не сработает на конкретной модели,
  constrained JSON начнётся слишком рано и рассуждение выродится. → reasoning-first поле как
  страховка; в eval мониторим долю пустого `thinking`.
- **Классификация ≠ переписывание сегмента.** Если модель просто копирует входной `segment`,
  стадия бесполезна. → В eval сегмент даёт лишь допустимое подмножество значений `engagement[0]`,
  а не равенство; поощряем поведенческий вывод.

**Решение (принято): один вызов LLM, не несколько.** Классификация, инсайты и челленджи
генерируются в одном structured-ответе, стадии задаёт порядок полей. Отдельные вызовы на
классификацию/инсайты — не делаем: одна модель, одна схема — дешевле, ниже латентность и
связнее (челленджи выбираются в том же ответе, что и обосновывающие их инсайты).

Что бы я добавил сверх запроса (по желанию, не обязательно для MVP):
- **`insight.name` как долгоживущий якорь между неделями.** Если хранить имена инсайтов в
  `previous_plans`, планировщик сможет отслеживать «закрыл ли я dod прошлой недели» — это
  усиливает continuity-шаг, который сейчас работает по типу челленджа.

---

## 14. Верификационный eval по типам пользователей

Запрос: «очень маленький eval на срезе пользователей разных типов — проверить, что планировщик
реально классифицирует и делает это корректно». Ключевая идея — **planner-only**, без дорогой
симуляции покупателя (actor), поэтому он быстрый и не требует сильной модели/долгих прогонов.

Дизайн:
- **Выборка по сегментам.** Берём фиксированный маленький срез: по 2–3 профиля на каждый из
  4 сегментов (`profiles.build_profiles`), детерминированно по `--seed`. ~8–12 профилей.
- **Только планировщик.** Для каждого профиля: `insight.build_insight` → `planner.plan_challenge`
  (без 3 веток, без actor). Дёшево: 1 вызов Qwen на профиль.
- **Что проверяем (детерминированно, без LLM-судьи):**
  1. **Классификация непустая и валидная:** непустой ранж. `engagement` (1..4, sort by score) и
     `posture`; каждый `signal` из закрытого enum, каждый со `score` и `evidence_metric`.
  2. **Согласованность с наблюдаемым поведением:** у каждого сегмента — ожидаемое подмножество
     правдоподобных `engagement[0]` (`dormant` → {`lapsing`, `cooling`}; `heavy` →
     {`steady_core`, `basket_depth`, `visit_headroom`, `category_gap`} — см. Part 3 таксономии).
     Метрика — доля профилей, чей `engagement[0]` попал в допустимое множество сегмента.
  2a. **Метрика подтверждает сигнал:** для `engagement[0]` derived-метрика из `evidence_metric`
     реально лежит в диапазоне сигнала (Part 2.1): напр. `lapsing` ⇒ `overdue_ratio>2.6`. Доля
     профилей, где сигнал согласован со своим числом.
  3. **Не копирует сегмент вслепую:** доля профилей, где `engagement[0]` опирается на derived-
     сигнал (momentum/overdue/headroom), а не просто повторяет входную метку.
  3a. **Posture из чувствительности:** доля профилей, где `posture` совпадает с корзиной по
     `promo_sensitivity` (cuts из Part 2.2 таксономии) — санити ценовой оси.
  4. **Целостность ссылок:** 100% челленджей с валидным `insight_ref`; `general_strategy`
     покрывает все инсайты (это уже гарантирует валидатор, eval лишь фиксирует долю).
  5. **Разнообразие:** на разных сегментах — разные механики/типы (санити против «всем одно и
     то же»).
- **Опционально — LLM-judge classification_fit** на этом же срезе для качественной оценки, но
  основной сигнал — детерминированные проверки 1–5.
- **Как гонять.** Новая CLI-подкоманда (например `verify-classification`) или флаг
  `run-eval --classification-only`, пишущая маленький md/json-отчёт (доля по каждому критерию,
  разбивка по сегментам). Прогон — секунды-минуты, а не ~час, т.к. нет actor-веток.

Это ровно «мало eval, только проверить классификацию», и оно ортогонально дорогому
контрфактическому eval (`run-eval` с actor), который остаётся для экономики.

---

## 15. Открытые вопросы

- Таксономия зафиксирована в
  [planner-v2-taxonomy-and-examples.md](planner-v2-taxonomy-and-examples.md): Family A — **7
  ранжируемых сигналов** (траектория `rising`/`steady_core`/`cooling`/`lapsing` + рычаги
  `visit_headroom`/`basket_depth`/`category_gap`), Family B — 3 позиции `posture`, семь derived-
  фич (Part 1b) и правила скоринга/ранжирования (Part 3). Открытые калибровки (не блокеры):
  константы `VISIT_CEILING`, `BASKET_REFERENCE`, ширина окон recent/prior (28д), зазор
  `is_ambiguous` (~0.15) и точные пороги сигналов — подобрать по первому же verify-прогону.
- Держать ли `score` непрерывным (0..1) или квантизовать в тиры (напр. 1–5, как в RFM) для
  устойчивости LLM — предложение: непрерывный, но валидатор допускает грубые значения.
- Сколько `side`-квестов максимум (`MAX_CHALLENGES`)? Предложение: hero + до 2 side.
- Reasoning-парсер на узле (`qwen3`) — согласовать запуск vLLM по правилам inference-node;
  до этого работает reasoning-first-поле.
- Показывать ли `classification`/инсайты пользователю (объяснимость) или только в трейсе/judge?
- Число вызовов LLM — решено: один вызов (§13). Вопрос закрыт.

---

## Куда дальше
- Базовая архитектура и контракты — `ml-solution-architecture.md`.
- Метрики и инварианты eval — `metrics-explained.md`.
- Актёр и трейсинг — `actor-and-tracing.md`.
- Последний прогон — `eval-report.md`, разбор — `eval-findings.md`.
