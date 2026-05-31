# Make Celery app available on import
from .celery import app as celery_app  # noqa: F401

