#!/usr/bin/env bash
# Run as the CloudPanel SITE USER, inside the project root.
# Usage: deploy/setup.sh fms.socialflylive.com
set -euo pipefail
DOMAIN="${1:?usage: deploy/setup.sh <domain>}"
cd "$(dirname "$0")/.."

PY="$(command -v python3.12 || command -v python3.11 || command -v python3)"
[ -d "$HOME/venv" ] || "$PY" -m venv "$HOME/venv"
# shellcheck disable=SC1091
source "$HOME/venv/bin/activate"
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ ! -f .env ]; then
  KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(60))')"
  cat > .env <<ENV
FMS_DEBUG=0
FMS_SECRET_KEY=$KEY
FMS_ALLOWED_HOSTS=$DOMAIN
ENV
  chmod 600 .env
  echo "Created .env"
fi

set -a; source .env; set +a
mkdir -p media
python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo
echo "Setup done. Now create the admin login:"
echo "  source ~/venv/bin/activate && set -a && source .env && set +a && python manage.py createsuperuser"
