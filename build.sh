#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files safely
python manage.py collectstatic --no-input

# Generate and apply database migrations automatically
# Run makemigrations but don't fail the build if it errors —
# this prevents deployment from blocking if migrations cannot be created in CI
if python manage.py makemigrations --no-input; then
	echo "makemigrations completed"
else
	echo "makemigrations failed or no model changes; continuing"
fi

python manage.py migrate --no-input