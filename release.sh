#!/usr/bin/env bash
set -e

echo "Running migrations against Supabase..."
python manage.py migrate --noinput

echo "Migrations complete."
