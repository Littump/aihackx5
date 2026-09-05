# Langfuse (локальный self-hosted)

Локальный стек Langfuse для инспекции трейсов ML-eval (`dev/backend/app/ml`).

## Запуск

```bash
make langfuse-up      # web+worker+postgres+clickhouse+redis+minio
make langfuse-logs    # хвост логов
make langfuse-down    # остановить (данные — в docker volumes)
```

UI: http://localhost:3000 — вход `admin@domovoy.local` / `domovoy-admin`.

## Ключи и порты

Org/project/пользователь/ключи создаются автоматически при первом старте через `LANGFUSE_INIT_*`.

- public key: `pk-lf-domovoy-local`
- secret key: `sk-lf-domovoy-local`
- host: `http://localhost:3000`

Дефолты продублированы в `dev/backend/app/ml/config.py`, поэтому eval заливает трейсы без ручной настройки. Переопределяются через `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`.

Порты на хосте: `3000` (web). Остальные сервисы слушают только `127.0.0.1`; minio вынесен с занятого `9090` на `9190` (S3) и `9191` (консоль).

## Авто-заливка из прогонов

`run-eval` с `--trace-out` заливает трейсы в Langfuse автоматически по завершении прогона. Заливка best-effort: недоступный Langfuse не роняет eval (`langfuse push skipped: ...`). Отключить — `--no-langfuse`.

Значения секретов здесь — только для локальной разработки.
