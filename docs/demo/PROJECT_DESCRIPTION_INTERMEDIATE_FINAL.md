# Описание проекта — промежуточная версия
## X5 «Домовой»

## 1. Краткая аннотация

**Домовой** — персональный игровой слой поверх X5 Клуба, который использует историю покупок пользователя для персонализации следующего действия: челленджа, прогресса, лиги или referral-механики.

Рабочая гипотеза: если связать реальные покупки с постоянным игровым прогрессом и персональными целями относительно привычного поведения пользователя, можно увеличить частоту покупок без снижения маржи на участника.

Рабочий сегмент — пользователи X5 Клуба со средней частотой покупок, ориентировочно **3–7 покупок в месяц**.

## 2. Проблематика

В X5 уже есть акции, кешбэк, задания и игровые кампании, но они существуют как отдельные механики. По данным X5, в игровых проектах компании в 2025 году участвовали около 9 млн человек, а «Ам Ням» привлёк 4,2 млн игроков и более 74 млн игровых сессий — то есть аудитория уже готова к игровым форматам ([X5](https://mediahub.x5.ru/news/kazhdyj-tretij-gejmer-igraet-v-mobilnyh-prilozheniyah-x5)).

При этом задача — не просто растить engagement в приложении, а влиять на частоту покупок между визитами. Внешние benchmarks показывают, что потенциал есть: пользователи игр «Магнита» покупали в среднем на 7,4% чаще сопоставимых неиграющих пользователей ([New Retail](https://new-retail.ru/novosti/retail/auditoriya_igr_v_prilozhenii_magnita_prevysila_10_mln/)), а Tesco персонализирует челленджи по истории покупок, категориям, порогам и наградам ([Eagle Eye](https://eagleeye.com/case-studies/tesco-clubcard-challenges)).

Для X5 остаются три бизнес-задачи:
- сделать персональную выгоду и накопленный результат заметнее;
- дать пользователю причину вернуться без постоянного увеличения скидок;
- не допустить, чтобы rewards съедали incremental margin или уходили во fraud.

## 3. Актуальная постановка задачи

Собрать PoC, который на синтетических данных:

- анализирует историю чеков и рассчитывает профиль пользователя;
- выбирает персональную механику / челлендж;
- обновляет прогресс Домового после новой покупки;
- рассчитывает допустимую награду с учётом экономики;
- обновляет рейтинг и referral-status;
- объясняет выбор механики;
- проверяет чеки и referrals на fraud;
- позволяет оценить relevance, потенциальный uplift и unit economics.

Критерии, которые должны быть проверяемы в PoC:

- relevance персонализации ≥70% на 30–50 профилях;
- reward cost не превышает ожидаемый incremental effect;
- antifraud работает по explainable precision-first логике;
- simulation сравнивает control и treatment на 1–10 тыс. synthetic users.

## 4. Выбранное техническое решение

PoC реализуется как **mobile-first React web + FastAPI backend + PostgreSQL**.

Основной поток:

```text
Новый чек
→ antifraud
→ пересчёт user features
→ обновление Домового
→ challenge / reward
→ league
→ referral
→ UI
```

Персонализация строится отдельно:

```text
User Features
→ Candidate Engine
→ Personalization / Recommender
→ Economics / Reward Engine
→ LLM copy
```

- **Feature Engine** считает признаки из истории чеков.
- **Candidate Engine** определяет допустимые варианты.
- **Personalization / Recommender** ранжирует их; rule-based ranking используется как baseline.
- **Economics / Reward Engine** задаёт target и максимальный бюджет награды.
- **LLM** отвечает за текст и explanation, но не назначает финансовые параметры.
- **Eval / Simulation** используются для проверки relevance, экономики и antifraud-метрик.

## 5. Уже реализованные компоненты

> Заполняется разработчиками по фактическому состоянию проекта.

- Backend: ...
- Frontend: ...
- AI / Data: ...
- Infra / CI / API contracts: ...

## 6. Предварительные результаты

> Заполняется командой после текущего прогона PoC.

- ...
- ...
- ...

## 7. Ограничения текущей версии

> Заполняется командой по фактически реализованной версии.

- ...
- ...
- ...

## 8. Открытые вопросы

> Заполняется командой после синхронизации продукта и разработки.

- ...
- ...
- ...

## 9. План работ до финальной версии

### Product / Business — Анна

- [ ] Финализировать финансовую модель: challenge economics, referral economics, sensitivity по uplift / margin / reward.
- [ ] Сверить продуктовые assumptions с `domain-rules` и фактической реализацией.
- [ ] Финализировать критерии успеха, guardrails и план пилота.
- [ ] Собрать итоговую презентацию и логику защиты.
- [ ] Финализировать обязательные продуктовые документы.
- [ ] Подготовить бизнес-часть demo: проблема → решение → результаты → экономика → пилот.

### Общекомандные задачи

- [ ] Собрать end-to-end demo.
- [ ] Прогнать eval и simulation.
- [ ] Зафиксировать фактические результаты, ограничения и открытые вопросы.
- [ ] Провести финальный QA и репетицию demo.
- [ ] Технические задачи до финала — дополнить разработчикам.

## 10. Команда и распределение задач

| Участник | GitHub | Роль и зона ответственности | Выполнено / текущий фокус |
|---|---|---|---|
| **Анна Казанцева** | `anna-kaz` | **AI Product.** Problem framing, JTBD, UX-аудит, product scope и приоритеты, research, бизнес-логика, экономика, метрики и pilot design; продуктовые документы, demo-сценарий и презентация. Задачи `DOC-*`. | Сформированы сегмент и продуктовая гипотеза, MVP и основные сценарии, reward economics, критерии успеха, guardrails и план пилота; продуктовая постановка сверена с архитектурой. До финала: финмодель, demo narrative, финальные документы и презентация. |
| **Роман Якимов** | `Littump` | **Backend / Frontend / Infrastructure.** Backend core: receipts, user features, savings, Domovoy, challenges, economics/personalization, league, referrals, antifraud, PM view; frontend целиком; API contract, миграции и инфраструктура. Задачи `BE-*`, `FE-*`, `INF-*`. | Уже собраны foundation, API-contract и миграции; receipts/features/savings, Домовой, challenges и reward logic; receipt pipeline и simulate; Home/Challenge; League; Referral и базовый antifraud; основные consumer-экраны. До финала остаются интеграция antifraud в receipt pipeline, achievements, PM view и deploy/demo-инфраструктура. |
| **Татьяна Тельнова** | `tatiana-stlv` | **Data & AI.** `app/synthetic/` — synthetic users/receipts и fraud patterns; `app/llm/` — тексты Домового, explanation, insights и fallback; `app/eval/` — relevance evaluation; `app/simulation/` — control vs treatment и результаты для PM view. Задачи `AI-*`. | Основная зона на текущий этап — синтетика, LLM-модуль, eval и simulation. До финала нужно подготовить synthetic dataset, fraud patterns, LLM-copy/fallback, relevance eval на 30–50 профилях и simulation на 1–10 тыс. пользователей. |
