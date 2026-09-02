# E6 — Receipt pipeline и frontend core

## BE-013 process_receipt
**Файлы:** `app/features/receipts/service.py`, тесты `tests/e2e/receipts/test_pipeline.py`.
**Описание:** оркестратор строго по порядку из `architecture.md`. До BE-018/BE-020 шаг антифрода — `approve` с пустыми сигналами; до BE-016 лига — null; до BE-019 referral — null; до BE-021 achievements — []. Всё в одной транзакции. Возвращает полный `ReceiptProcessingResult`.
**AC:**
- один вызов → строка в `receipts`, `user_features` пересчитаны, `domovoy_states.xp` +10, прогресс hero +1, `savings_delta` = savings чека;
- ошибка в любом шаге → ничего не записано (тест с monkeypatch, бросающим в шаге 5);
- ответ по контракту.

## BE-014 simulate
**Файлы:** `app/features/receipts/simulate.py`, router, тесты.
**Описание:** генерирует чек из features: магазин — любимый (или `store_id`), позиции — 3–6 из категорий по affinity, промо по promo_sensitivity, сумма около `avg_basket` ± 30 %. Сценарии: `typical`; `category_boost` — добавляет 2 позиции категории hero-челленджа; `fraud_burst` — 4 чека по 100 ₽ с интервалом 3 минуты (для демо антифрода). Затем `process_receipt`.
**AC:** `typical` даёт counted-чек с суммой в диапазоне; `category_boost` двигает category-челлендж; `fraud_burst` создаёт 4 чека, из них counted ≤ 1 (дедуп), и после BE-020 — decision hold/block.

## BE-015 home
**Файлы:** `app/features/users/home.py`, router, тесты.
**Описание:** `GET /users/{id}/home` собирает `HomeResponse` из сервисов domovoy, savings(month), challenges (hero, refresh если активных нет), league teaser (null до BE-016), referral teaser, `recommended_mechanic` по правилам: нет выполненных челленджей → `challenge`; ≥ 3 выполненных и есть лига → `league`; `social_propensity ≥ 0.6` и есть 2 выполненных → `referral`; иначе `challenge`. Причина — одна фраза. `insight` — из `llm.render_insight` (шаблон до AI-004). Решение пишется в `mechanic_decisions`.
**AC:** ответ по контракту; правило выбора механики покрыто unit на все ветки; `mechanic_decisions` получает строку на каждый вызов.

## FE-001 оболочка
**Файлы:** `src/app/*`, `src/shared/ui/{PhoneShell,BottomNav,Card,ProgressBar,Button}.tsx`, `src/shared/api/client.ts`, `src/test/{setup,handlers}.ts`, `src/features/users/`.
**Описание:** роуты `/`, `/challenge`, `/league`, `/referral`, `/pm`; `?user=<id>` в URL и `UserContext`; переключатель пользователя (select из `GET /users`); нижняя навигация; MSW-хендлеры для всех ручек контракта с правдоподобными данными.
**AC:** `npm run build` без ошибок; тест: смена пользователя меняет `?user=`; все 5 роутов рендерятся с моками.

## FE-002 Home
**Описание:** по PRD §4 Screen 1: Домовой (иллюстрация по mood — 5 SVG/эмодзи-плейсхолдеров), уровень и XP-бар, настроение с причиной, savings за месяц с дельтой, insight, hero challenge с прогрессом и наградой, раскрывающийся «Почему это мне?», кнопка «Simulate new purchase» (мутация → инвалидация home/challenges/league → анимация дельт из `ReceiptProcessingResult`), переходы в Лигу и Referral.
**AC:** тесты: рендер данных, клик Simulate вызывает `POST .../simulate` и обновляет прогресс, explanation раскрывается; ширина 390 без горизонтального скролла.

## FE-003 Challenge
**Описание:** PRD §4 Screen 2: hero + side карточки (тип, условие, baseline → target, прогресс, дедлайн, награда), explanation, история выполненных.
**AC:** тесты рендера и раскрытия explanation; пустое состояние «Домовой думает…» с кнопкой refresh.
