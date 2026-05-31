from .base import *  # noqa: F401,F403

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ALLOWED_HOSTS = config("ALLOWED_HOSTS").split(",")

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
