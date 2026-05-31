Render + Supabase deployment guide

This setup keeps the Django app on Render and the database on Supabase.

1. Supabase setup

- Create a new Supabase project.
- Open Database > Extensions and enable `postgis`.
- Copy the connection string from Project Settings > Database.
- Prefer the URI form Render expects, such as:

```text
postgresql://postgres.[your-id]:[your-password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

2. Render setup

- Push this repo to GitHub.
- In Render, create a new Web Service and connect the GitHub repo.
- Set the environment type to Python.
- Set the build command to `./build.sh`.
- Set the start command to `gunicorn salamanoda.wsgi:application --bind 0.0.0.0:$PORT`.

3. Environment variables

Add these on the Render dashboard:

- `DATABASE_URL` = Supabase connection string.
- `POSTGIS_ENABLED=true`.
- `SECRET_KEY` = a secure random production value.
- `DEBUG=false`.
- Optional: `REDIS_URL`, `AFRICASTALKING_USERNAME`, `AFRICASTALKING_API_KEY`, `AFRICASTALKING_SENDER_ID`.

4. Deploy

- Deploy the service.
- After the first build, verify migrations ran and open the site URL Render gives you.
- If the database is empty, run any seed command you want from the Render shell or locally against the same database.

Notes

- The project still falls back to SQLite locally when `DATABASE_URL` is not set.
- If you later add Channels/WebSockets, you can switch the start command to an ASGI entrypoint, but the current project runs fine with the WSGI start command above.