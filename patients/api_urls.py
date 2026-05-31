from django.urls import path

from .api import SOSCancelAPIView, SOSCreateAPIView, SOSStatusAPIView

urlpatterns = [
    path("sos/", SOSCreateAPIView.as_view(), name="sos-create"),
    path("sos/<int:job_id>/status/", SOSStatusAPIView.as_view(), name="sos-status"),
    path("sos/<int:job_id>/cancel/", SOSCancelAPIView.as_view(), name="sos-cancel"),
]
