#!/usr/bin/env bash
# Comando de build do serviço backend no Render.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Seeds idempotentes (só criam o que ainda não existe).
python manage.py seed_data
python manage.py seed_menu
