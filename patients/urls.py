from django.urls import path

from dispatch import views

urlpatterns = [
    path("", views.home, name="home"),
    path("requests/new/", views.emergency_request_create, name="emergency_request_create"),
]
