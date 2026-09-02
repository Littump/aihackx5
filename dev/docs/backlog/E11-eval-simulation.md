# E11 — Eval & Simulation (владелец: T)

## AI-005 relevance eval
**Файлы:** `app/eval/__main__.py`, `relevance.py`, тесты.
**Описание:** берёт 30–50 пользователей (`--profiles`, стратифицировано по сегментам), для каждого `challenges.service.refresh_weekly`, проверяет 4 условия §14, считает hit rate, invalid rate (валидатор отверг), fallback rate (`copy_source=template`), economics pass rate. Пишет `eval_runs` с `details` по профилям. Печатает таблицу.
**AC:** на seed-данных hit rate ≥ 0.70 (если ниже — это дефект candidate/economics, заводится задача); unit на каждое из 4 условий.

## AI-006 simulation
**Файлы:** `app/simulation/__main__.py`, `model.py`, `report.py`, тесты.
**Описание:** агентная модель по §13: популяция из синтетики (или генерируется на лету через `synthetic.profiles` без записи в базу), control/treatment, участие, uplift с затуханием, награды по economics, реферальная реактивация `dormant` через `social_propensity`, фрод-агенты и скоринг из BE-018 → precision/recall. Параметры CLI с дефолтами из `game_rules.SIMULATION_DEFAULTS`. Пишет `simulation_runs`.
**AC:** 5 000 пользователей × 8 недель < 60 с; при uplift 0 net_effect ≤ 0 и share_above_n равны; при дефолтах net_effect > 0; все параметры в `params` с ключом `assumptions=true`.

## AI-007 промпт-тюнинг
**Описание:** прогнать AI-005 с реальным ключом на 50 профилях, добиться fallback rate < 20 % и наличия чисел из features в explanation в 100 % случаев; зафиксировать финальный промпт и примеры в `app/llm/prompts.py`.
**AC:** отчёт eval с ключом приложен в `dev/docs/eval-report.md`.
