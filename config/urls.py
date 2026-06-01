from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.health import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("api/v1/", include(("api.v1.urls", "api"), namespace="v1")),
    path("auth/", include("django.contrib.auth.urls")),

    # HTML/PWA Web views at root
    path("accounts/", include("accounts.urls")),
    path("patients/", include("patients.urls")),
    path("riders/", include("riders.urls")),
    path("saccos/", include("saccos.urls")),
    path("reports/", include("reports.urls")),
    path("", include("dispatch.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
