from django.urls import path

from .api import ReportsHealthAPIView

urlpatterns = [path("health/", ReportsHealthAPIView.as_view(), name="reports-health")]
