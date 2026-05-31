from django.urls import path

from .api import WhoAmIAPIView

urlpatterns = [path("whoami/", WhoAmIAPIView.as_view(), name="whoami")]
