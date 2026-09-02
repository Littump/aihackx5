# Деплой: Yandex Cloud VM + docker compose + CD

Целевая схема для демо. Реализуется задачами эпика [E13](backlog/E13-deploy.md), владелец — Роман.

## Схема

```
GitHub Actions (push в main, после зелёного CI)
   │ build образов backend и frontend → ghcr.io/littump/aihackx5-{backend,frontend}:sha
   │ ssh на VM → docker compose pull → migrate → up -d → healthcheck
   ▼
Yandex Cloud VM (Ubuntu 24.04, 2 vCPU / 4 GB, публичный IP)
   ├─ nginx (:80, при наличии домена :443 через certbot)
   │    ├─ /            → frontend (статика из образа)
   │    └─ /api/        → backend:8000
   ├─ backend  (uvicorn, образ из ghcr)
   ├─ postgres:16 (volume, pg_dump по cron в /var/backups/domovoy)
   └─ .env (секреты, только на VM)
```

Файлы в репозитории: `deploy/docker-compose.prod.yml`, `deploy/nginx.conf`, `deploy/Dockerfile.backend`, `deploy/Dockerfile.frontend`, `deploy/setup-vm.sh`, `deploy/.env.prod.example`, `.github/workflows/deploy.yml`.

## Что нужно от владельца VM

| Данные | Куда | Кто вносит |
|---|---|---|
| Публичный IP или домен | GitHub secret `VM_HOST` | Роман |
| SSH-пользователь | GitHub secret `VM_USER` | Роман |
| Приватный SSH-ключ деплоя (отдельный, только для этой VM) | GitHub secret `VM_SSH_KEY` | Роман |
| `ANTHROPIC_API_KEY`, пароль Postgres, `DEMO_NOW` | `/opt/domovoy/.env` на VM | Роман, руками по SSH |
| Токен ghcr с `read:packages` для VM (или публичные образы) | `docker login ghcr.io` на VM один раз | Роман |

Секреты в репозиторий и в чат не попадают. Агент готовит файлы и workflow с плейсхолдерами, значения вносит человек.

## Порядок первого развёртывания

1. Создать VM в Yandex Cloud: Ubuntu 24.04, 2 vCPU, 4 GB RAM, 30 GB диск, публичный IPv4, security group: 22 (только свой IP), 80, 443.
2. `ssh user@VM 'bash -s' < deploy/setup-vm.sh` — ставит docker, compose, создаёт `/opt/domovoy`, включает ufw.
3. Скопировать `deploy/.env.prod.example` → `/opt/domovoy/.env`, заполнить.
4. Добавить secrets в GitHub, запушить в `main` — workflow `deploy.yml` соберёт образы и развернёт.
5. Проверить `http://VM/api/v1/health` и открыть `http://VM/`.

## Что считается рабочим деплоем

- `GET /api/v1/health` отдаёт `{"status":"ok","database":"ok"}`.
- Frontend открывается по корню, ходит в `/api` без CORS-ошибок.
- Повторный push в `main` обновляет приложение без ручных действий за ≤ 5 минут.
- Миграции применяются автоматически до перезапуска backend; при падении миграции старый backend продолжает работать.
- Данные Postgres переживают `docker compose down && up`.
