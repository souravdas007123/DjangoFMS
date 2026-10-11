#!/usr/bin/env bash
# Run as ROOT. Usage: deploy/install_service.sh <site-user> <domain> [port]
set -euo pipefail
SITE_USER="${1:?usage: install_service.sh <site-user> <domain> [port]}"
DOMAIN="${2:?domain required}"
PORT="${3:-8010}"
APP_DIR="/home/$SITE_USER/htdocs/$DOMAIN"
[ -f "$APP_DIR/.env" ] || { echo "Missing $APP_DIR/.env - run deploy/setup.sh first"; exit 1; }

cat > /etc/systemd/system/factoryos.service <<UNIT
[Unit]
Description=FactoryOS (gunicorn)
After=network.target

[Service]
User=$SITE_USER
Group=$SITE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=/home/$SITE_USER/venv/bin/gunicorn fms.wsgi:application --bind 127.0.0.1:$PORT --workers 3 --timeout 60
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now factoryos
sleep 1
systemctl --no-pager status factoryos | head -n 8
echo
echo "Gunicorn is on 127.0.0.1:$PORT. In CloudPanel set the site's App Port to $PORT."
