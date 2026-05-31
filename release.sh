#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "Applying database migrations to Supabase..."
python manage.py migrate --noinput

echo "Database schema sync complete."
