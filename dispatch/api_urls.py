from django.urls import path

from .api import DispatchTimeoutAPIView

urlpatterns = [
    path("jobs/<int:job_id>/timeout/", DispatchTimeoutAPIView.as_view(), name="dispatch-timeout"),
]
