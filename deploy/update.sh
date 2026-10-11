#!/usr/bin/env bash
# Run as the SITE USER to deploy new code. Then (as root): systemctl restart factoryos
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --ff-only
source "$HOME/venv/bin/activate"
pip install -r requirements.txt -q
set -a; source .env; set +a
python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo "Done. Restart as root:  systemctl restart factoryos"
