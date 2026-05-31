from django.contrib.auth import views as auth_views
from django.views.decorators.cache import never_cache
from dispatch.views import portal


@never_cache
def login_view(request):
    return auth_views.LoginView.as_view(template_name="registration/login.html")(request)


@never_cache
def logout_view(request):
    return auth_views.LogoutView.as_view()(request)


@never_cache
def portal_view(request):
    return portal(request)
