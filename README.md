# BodaSOS MVP

A free-tier prototype for emergency dispatch coordination in Kenya built with Django, Django REST Framework, browser geolocation, Leaflet + OpenStreetMap, Redis-backed OTPs, and optional PostGIS routing.

## What it does

- Registers boda boda riders with Sacco, status, and location data.
- Supports rider onboarding with National ID and NTSA validation plus document uploads.
- Stores phone verification codes in cache and can send them through Africa's Talking sandbox.
- Lets sacco chairpersons approve riders from a simple dashboard.
- Accepts an emergency request with caller details and coordinates.
- Assigns the nearest active rider using a Haversine distance calculation.
- Renders a mobile-friendly dispatch console with a live map.
- Exposes DRF endpoints for riders, emergencies, and nearest-rider dispatch.
- Accepts SMS and USSD fallback requests for low-connectivity scenarios.

## Local setup

```bash
cd salamanoda
python3 -m venv ../.venv
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_demo_data
../.venv/bin/python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the dispatch console and `http://127.0.0.1:8000/admin/` for management.

## Deploy on Render + Supabase

Render hosts the Django app, and Supabase provides the Postgres database with PostGIS enabled.

1. Create a Supabase project and enable the `postgis` extension in Database > Extensions.
2. Copy the Supabase `DATABASE_URL` connection string from Project Settings > Database.
3. Create a Render Web Service from your GitHub repo.
4. Set these environment variables on Render:
	- `DATABASE_URL` to the Supabase connection string.
	- `POSTGIS_ENABLED=true` to use the PostGIS backend.
	- `SECRET_KEY` to a strong production secret.
	- `DEBUG=false`.
	- Optional: `AFRICASTALKING_USERNAME`, `AFRICASTALKING_API_KEY`, `AFRICASTALKING_SENDER_ID`, `REDIS_URL`.
5. Use the build command `./build.sh`.
6. Use the start command `gunicorn salamanoda.wsgi:application --bind 0.0.0.0:$PORT`.

For a copy-paste Render setup guide, see [RENDER_SUPABASE.md](RENDER_SUPABASE.md).

## API endpoints

- `GET /api/riders/`
- `POST /api/riders/`
- `GET /api/emergencies/`
- `POST /api/emergencies/`
- `POST /api/dispatch/nearest-json/`
- `POST /api/africastalking/sms/`
- `POST /api/africastalking/ussd/`

## Demo flow

1. Register a rider from the homepage or the onboarding route.
2. Verify the phone number with the SMS OTP.
3. Approve the rider from the sacco dashboard or Django admin.
4. Seed demo riders and emergencies with `seed_demo_data` for a live walkthrough.

## Notes

This MVP deliberately stays on SQLite and pure Python matching by default so it remains zero-budget and fast to iterate. When `POSTGIS_ENABLED=true` and `DATABASE_URL` points at PostgreSQL with PostGIS available, the nearest-rider lookup switches to database-side geospatial routing. When `REDIS_URL` is set, OTPs use Redis instead of local memory.
# BodaSOS
