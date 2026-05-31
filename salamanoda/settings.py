import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = "django-insecure-change-me-in-production"
DEBUG = True
ALLOWED_HOSTS: list[str] = [".onrender.com", "localhost", "127.0.0.1"]

POSTGIS_ENABLED = os.getenv("POSTGIS_ENABLED", "false").lower() == "true"
AFRICASTALKING_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "")
AFRICASTALKING_API_KEY = os.getenv("AFRICASTALKING_API_KEY", "")
AFRICASTALKING_SENDER_ID = os.getenv("AFRICASTALKING_SENDER_ID", "")
AFRICASTALKING_SANDBOX = os.getenv("AFRICASTALKING_SANDBOX", "true").lower() != "false"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "dispatch",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "salamanoda.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "salamanoda.wsgi.application"
ASGI_APPLICATION = "salamanoda.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

database_url = os.getenv("DATABASE_URL")
if database_url:
    database_engine = (
        "django.contrib.gis.db.backends.postgis"
        if POSTGIS_ENABLED
        else "django.db.backends.postgresql"
    )
    DATABASES["default"] = dj_database_url.config(
        default=database_url,
        engine=database_engine,
        conn_max_age=600,
    )

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "bodasos-local-cache",
    }
}

redis_url = os.getenv("REDIS_URL")
if redis_url:
    CACHES["default"] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/portal/"
LOGOUT_REDIRECT_URL = "/"
