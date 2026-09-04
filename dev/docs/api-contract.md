# Контракт API

Источник истины — `dev/contracts/openapi.yaml`. Этот файл — навигация: какая ручка для какого экрана. Все пути с префиксом `/api/v1`. Auth в MVP нет, пользователь демо — `user_id` в пути.

| Метод и путь | Экран / потребитель | Feature | Заметки |
|---|---|---|---|
| `GET /health` | инфраструктура | health | проверяет и базу |
| `GET /users` | переключатель пользователя в демо | users | id, pseudonym, segment |
| `GET /users/{user_id}/home` | Home | users (агрегирует domovoy, savings, challenges, league, referral) | один запрос на экран |
| `GET /users/{user_id}/savings?period=week\|month` | Home, Profile | savings | сумма, дельта к прошлому периоду, топ категорий |
| `GET /users/{user_id}/challenges` | Challenge | challenges | hero + side + история |
| `GET /users/{user_id}/challenges/{challenge_id}` | Challenge | challenges | с `explanation` и `rationale_features` |
| `POST /users/{user_id}/challenges/refresh` | демо, недельный job | challenges | сгенерировать новый набор на неделю |
| `POST /receipts` | интеграция / тесты | receipts | полный чек с позициями → `ReceiptProcessingResult` |
| `GET /users/{user_id}/receipts/simulate/draft` | шаг 1 кнопки «Симулировать покупку» | receipts | черновик чека на 3–4 позиции, цель недели, категории с названиями товаров |
| `POST /users/{user_id}/receipts/simulate` | кнопка «Simulate new purchase» | receipts | сценарий `typical` / `category_boost` / `fraud_burst` либо подтверждённые `items` |
| `GET /users/{user_id}/receipts?limit=` | PM view, отладка | receipts | |
| `GET /users/{user_id}/league` | League | league | дивизион, 30 участников под псевдонимами, моё место, зоны, дельта позиции |
| `GET /users/{user_id}/referral` | Referral | referrals | код, ссылка, приглашённые со статусами, лимиты |
| `POST /referrals/redeem` | демо регистрации приглашённого | referrals | создаёт пользователя-приглашённого |
| `GET /users/{user_id}/achievements` | Home/Profile | achievements | |
| `GET /pm/users/{user_id}` | PM view | pm | features, механика, челлендж, экономика, фрод, награды |
| `GET /pm/fraud?limit=` | PM view | pm | последние решения антифрода с причинами |
| `GET /pm/simulation/latest` | PM view | pm | последняя симуляция |
| `GET /pm/eval/latest` | PM view | pm | последний relevance eval |

## Ошибки

```json
{ "error": { "code": "user_not_found", "message": "Пользователь 42 не найден" } }
```

Коды: `user_not_found`, `challenge_not_found`, `store_not_found`, `referral_code_invalid`, `referral_limit_reached`, `validation_error`. HTTP: 404, 409, 422.

## Как менять

Скилл `update-api-contract`. Коротко: YAML → `make contract-lint` → backend → `make contract-check` → `make contract-types` → frontend.
