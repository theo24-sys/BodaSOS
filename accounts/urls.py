from django.urls import path

from .views import login_view, logout_view, portal_view

urlpatterns = [
    path("portal/", portal_view, name="portal"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
