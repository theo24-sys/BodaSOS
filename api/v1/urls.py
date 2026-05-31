from django.urls import include, path

urlpatterns = [
    path("dispatch/", include("dispatch.urls")),
    path("riders/", include("riders.urls")),
    path("patients/", include("patients.urls")),
]
