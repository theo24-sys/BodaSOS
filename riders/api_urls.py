from django.urls import path

from .api import RiderAcceptDispatchAPIView, RiderCurrentJobAPIView, RiderDeliveredAPIView, RiderDutyAPIView, RiderLocationAPIView

urlpatterns = [
    path("location/", RiderLocationAPIView.as_view(), name="rider-location"),
    path("duty/", RiderDutyAPIView.as_view(), name="rider-duty"),
    path("job/current/", RiderCurrentJobAPIView.as_view(), name="rider-current-job"),
    path("job/<int:job_id>/accept/", RiderAcceptDispatchAPIView.as_view(), name="rider-job-accept"),
    path("job/<int:job_id>/delivered/", RiderDeliveredAPIView.as_view(), name="rider-job-delivered"),
]
