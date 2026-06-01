# Make Celery app available on import
try:
    from .celery import app as celery_app  # noqa: F401
except ImportError:
    celery_app = None

