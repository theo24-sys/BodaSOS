from django.urls import path

from .views import patient_shell_view

urlpatterns = [
    path("", patient_shell_view, name="home"),
]
