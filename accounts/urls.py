from django.urls import path

from .views import jwt_obtain_pair_view, logout_view, pin_login_view, token_refresh_view, whoami_view

urlpatterns = [
    path("login/", pin_login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("jwt/login/", jwt_obtain_pair_view, name="jwt_login"),
    path("jwt/refresh/", token_refresh_view, name="token_refresh"),
    path("whoami/", whoami_view, name="whoami"),
]
