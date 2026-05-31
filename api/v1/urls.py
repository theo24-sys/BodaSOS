from django.urls import include, path

urlpatterns = [
    path("", include("patients.api_urls")),
    path("riders/", include("riders.api_urls")),
    path("saccos/", include("saccos.api_urls")),
    path("dispatch/", include("dispatch.api_urls")),
    path("reports/", include("reports.api_urls")),
    path("accounts/", include("accounts.api_urls")),
]
