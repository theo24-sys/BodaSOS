from .base import *  # noqa: F401,F403

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ALLOWED_HOSTS = [host.strip() for host in config("ALLOWED_HOSTS", default="").split(",") if host.strip()]

render_host = config("RENDER_EXTERNAL_HOSTNAME", default="")
if render_host:
    ALLOWED_HOSTS.append(render_host)

for host in ["localhost", "127.0.0.1"]:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)


# Sentry configuration (optional)
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            environment=config("SENTRY_ENVIRONMENT", default="production"),
            traces_sample_rate=config("SENTRY_TRACES_SAMPLE_RATE", default=0.0, cast=float),
            send_default_pii=True,
        )
    except Exception:
        # Do not crash startup if Sentry import fails
        pass
