import os

from .base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", ".onrender.com").split(",") if host.strip()]
