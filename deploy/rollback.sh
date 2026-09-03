#!/usr/bin/env bash
set -euo pipefail

# Миграции идут только вперёд: откат поднимает старый код без прогона migrate.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <sha>" >&2
  exit 1
fi

TAG="$1"
export TAG

echo "==> Откат на образ TAG=${TAG}"

echo "==> docker compose pull"
docker compose -f "$COMPOSE_FILE" pull postgres backend frontend

echo "==> docker compose up -d (без migrate)"
# --no-deps: без него compose всё равно прогонит migrate из-за depends_on у backend
docker compose -f "$COMPOSE_FILE" up -d --no-deps postgres backend frontend

echo "==> Логи backend (последние 200 строк)"
docker compose -f "$COMPOSE_FILE" logs --tail 200 backend

echo "==> Откат на TAG=${TAG} завершён"
