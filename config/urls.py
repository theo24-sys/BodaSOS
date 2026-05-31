from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("health/", include("core.health_urls")),
    path("accounts/", include("accounts.urls")),
    path("api/v1/", include("api.v1.urls")),
    path("admin/", admin.site.urls),
    path("", include("patients.urls")),
    path("riders/", include("riders.urls")),
    path("saccos/", include("saccos.urls")),
    path("dispatch/", include("dispatch.urls")),
    path("reports/", include("reports.urls")),
]
