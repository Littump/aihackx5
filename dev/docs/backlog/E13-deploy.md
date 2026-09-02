# E13 — Деплой на Yandex Cloud VM и CD (владелец: R)

Схема и список нужных данных — в [deploy.md](../deploy.md). Задачи INF-006 и INF-009 не требуют данных VM и делаются сразу; INF-007, INF-008, INF-010 — после того как есть VM и secrets.

## INF-006 Образы и prod-compose
**Файлы:** `deploy/Dockerfile.backend`, `deploy/Dockerfile.frontend`, `deploy/nginx.conf`, `deploy/docker-compose.prod.yml`, `deploy/.env.prod.example`.
**Описание:**
- `Dockerfile.backend`: multi-stage на `python:3.12-slim`, `uv sync --frozen --no-dev`, non-root пользователь, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`, `HEALTHCHECK` на `/api/v1/health`.
- `Dockerfile.frontend`: stage `node:22-alpine` → `npm ci && npm run build` с `VITE_API_URL=` (пустой: фронт ходит на относительный `/api`), stage `nginx:alpine` со статикой и `nginx.conf`.
- `nginx.conf`: `/` → статика с fallback на `index.html`, `/api/` → `proxy_pass http://backend:8000/api/`, gzip, `client_max_body_size 1m`.
- `docker-compose.prod.yml`: `postgres` (volume `pgdata`, healthcheck), `backend` (образ `ghcr.io/littump/aihackx5-backend:${TAG}`, `env_file: .env`, `depends_on: postgres healthy`), `migrate` (тот же образ, `command: python scripts/migrate.py`, `restart: "no"`), `frontend` (образ `ghcr.io/littump/aihackx5-frontend:${TAG}`, порты 80/443), `restart: unless-stopped` у всех.
- `shared/api/client.ts`: `BASE_URL` пустой по умолчанию в prod-сборке — проверить, что относительные пути работают.
**AC:** `docker build` обоих образов проходит локально; `docker compose -f deploy/docker-compose.prod.yml up` на локальной машине с `.env` из примера поднимает стек, `curl localhost/api/v1/health` отвечает `ok`, фронт открывается; образы не содержат `.env` и dev-зависимостей.

## INF-007 Подготовка VM
**Файлы:** `deploy/setup-vm.sh`.
**Описание:** идемпотентный скрипт для Ubuntu 24.04: docker + compose plugin из официального репозитория, пользователь деплоя в группе `docker`, `/opt/domovoy` с правами, `ufw` (22/80/443), `unattended-upgrades`, cron `pg_dump` раз в сутки в `/var/backups/domovoy` с ротацией 7 дней, `docker login ghcr.io` по токену из stdin.
**Требует:** VM создана, есть SSH-доступ.
**AC:** повторный запуск ничего не ломает; после скрипта `docker compose version` работает от пользователя деплоя; `curl http://VM` отвечает 502 от nginx-заглушки или 404 (порт открыт).

## INF-008 CD workflow
**Файлы:** `.github/workflows/deploy.yml`.
**Описание:** `on: workflow_run` после успешного `CI` на `main` (или `push` в `main` с `needs` на CI-джобы). Шаги: login в ghcr через `GITHUB_TOKEN`, `docker/build-push-action` для двух образов с тегами `sha` и `latest`, кэш `type=gha`; затем `appleboy/ssh-action` (или `ssh` с ключом из `VM_SSH_KEY`) на VM: `cd /opt/domovoy && export TAG=<sha> && docker compose -f docker-compose.prod.yml pull && docker compose run --rm migrate && docker compose up -d && curl -f localhost/api/v1/health`. `docker-compose.prod.yml`, `nginx.conf` и `.env.prod.example` копируются на VM через `scp` в том же шаге. Secrets: `VM_HOST`, `VM_USER`, `VM_SSH_KEY`. `concurrency: deploy` без отмены, чтобы два пуша не деплоились одновременно.
**Требует:** INF-006, INF-007, secrets добавлены.
**AC:** push в `main` → через ≤ 5 минут новый `sha` виден в `docker ps` на VM и `/api/v1/health` зелёный; упавший CI не запускает деплой; упавшая миграция останавливает шаг до `up -d` и workflow красный.

## INF-009 Миграции, healthcheck, откат
**Файлы:** `deploy/docker-compose.prod.yml`, `deploy/rollback.sh`, `dev/docs/deploy.md`.
**Описание:** `migrate` как отдельный одноразовый сервис перед `backend`; `backend` не стартует, пока `migrate` не завершился с 0 (`depends_on: condition: service_completed_successfully`). `rollback.sh <sha>`: выставить `TAG`, `pull`, `up -d` без миграций (миграции только вперёд, откат кода допустим только если миграция обратно совместима — правило в `deploy.md`). Логи: `docker compose logs --tail 200 backend`.
**AC:** сценарий «миграция падает» на локальном стеке оставляет старый backend работающим; `rollback.sh` на предыдущий `sha` возвращает прежнюю версию за ≤ 1 минуты.

## INF-010 Домен и TLS (если будет домен)
**Описание:** A-запись на IP VM, `certbot` в контейнере или `nginx` + `certbot --nginx` на хосте, редирект 80 → 443, `VITE_API_URL` не нужен (относительный `/api`). Без домена — пропускаем, демо по IP и HTTP.
**AC:** `https://домен/api/v1/health` зелёный, сертификат обновляется автоматически.

## INF-011 Демо-данные на VM
**Описание:** после деплоя один раз выполнить `docker compose run --rm backend python -m app.synthetic --users 300 --weeks 10 --seed 42` и eval/simulation (когда готовы AI-005/006); `DEMO_NOW` в `.env` выставить на дату генерации + 3 дня, чтобы неделя была «в разгаре».
**Требует:** INF-008, AI-003.
**AC:** `GET /users` на VM отдаёт 300 пользователей; Home первого пользователя показывает активный челлендж с ненулевым прогрессом.
