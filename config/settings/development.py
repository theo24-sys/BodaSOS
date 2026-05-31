from .base import *  # noqa: F401,F403

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True
INSTALLED_APPS += [
	"django_extensions",
	"debug_toolbar",
]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
INTERNAL_IPS = ["127.0.0.1", "localhost"]
