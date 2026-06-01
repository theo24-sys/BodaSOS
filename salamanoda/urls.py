from django.contrib import admin
from django.urls import include, path
from decouple import config

ADMIN_URL_GATEKEEPER = config("DJANGO_ADMIN_URL", default="internal-ops-gate-x937f")

urlpatterns = [
    path(f"{ADMIN_URL_GATEKEEPER.strip('/')}/", admin.site.urls),
    path("", include("dispatch.urls")),
]
