#!/usr/bin/env bash
# Идемпотентная подготовка Ubuntu 24.04 VM под деплой «Домового». Запуск: ssh user@VM 'bash -s' < deploy/setup-vm.sh
set -euo pipefail

DEPLOY_USER="${DEPLOY_USER:-$(whoami)}"
APP_DIR="${APP_DIR:-/opt/domovoy}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/domovoy}"
BACKUP_RETENTION_DAYS=7

log() { echo "==> $*"; }

log "Docker + compose plugin (официальный репозиторий)"
if ! command -v docker &>/dev/null; then
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  # shellcheck disable=SC1091
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
  log "docker уже установлен, пропускаю"
fi

log "Пользователь деплоя ($DEPLOY_USER) в группе docker"
if ! id -nG "$DEPLOY_USER" | grep -qw docker; then
  sudo usermod -aG docker "$DEPLOY_USER"
  log "добавлен в группу docker, для применения нужен новый SSH-логин"
else
  log "уже в группе docker"
fi

log "Каталог приложения $APP_DIR"
sudo mkdir -p "$APP_DIR"
sudo chown "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"

log "ufw: 22/80/443"
sudo apt-get install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw reload

log "unattended-upgrades"
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure -f noninteractive unattended-upgrades

log "Каталог бэкапов $BACKUP_DIR"
sudo mkdir -p "$BACKUP_DIR"
sudo chown "$DEPLOY_USER":"$DEPLOY_USER" "$BACKUP_DIR"

log "backup.sh + cron pg_dump раз в сутки, ротация $BACKUP_RETENTION_DAYS дней"
sudo tee "$APP_DIR/backup.sh" >/dev/null <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$APP_DIR"
set -a; source "$APP_DIR/.env"; set +a
STAMP=\$(date +%Y%m%d-%H%M%S)
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U "\$POSTGRES_USER" -d "\$POSTGRES_DB" \\
  | gzip > "$BACKUP_DIR/domovoy-\$STAMP.sql.gz"
find "$BACKUP_DIR" -name '*.sql.gz' -mtime +$BACKUP_RETENTION_DAYS -delete
EOF
sudo chown "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR/backup.sh"
sudo chmod +x "$APP_DIR/backup.sh"

CRON_LINE="0 3 * * * $APP_DIR/backup.sh >> $BACKUP_DIR/backup.log 2>&1"
EXISTING_CRON="$(sudo crontab -u "$DEPLOY_USER" -l 2>/dev/null || true)"
FILTERED_CRON="$(printf '%s\n' "$EXISTING_CRON" | grep -v "$APP_DIR/backup.sh" || true)"
printf '%s\n%s\n' "$FILTERED_CRON" "$CRON_LINE" | sudo crontab -u "$DEPLOY_USER" -

log "docker login ghcr.io"
if [[ -n "${GHCR_TOKEN:-}" ]]; then
  echo "$GHCR_TOKEN" | sudo -u "$DEPLOY_USER" docker login ghcr.io -u "${GHCR_USER:-$DEPLOY_USER}" --password-stdin
else
  log "GHCR_TOKEN не задан в окружении — пропускаю docker login, выполнить вручную позже: docker login ghcr.io"
fi

log "Готово. docker compose version от $DEPLOY_USER:"
sudo -u "$DEPLOY_USER" docker compose version
