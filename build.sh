#!/usr/bin/env bash
# Render build script. Runs once per deploy on the build container.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Auto-create superuser from env vars if one doesn't exist (free tier has no shell).
python manage.py ensure_superuser

# Populate demo data on first deploy (skips automatically if data already exists).
python manage.py seed_data
