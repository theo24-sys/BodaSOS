from django.urls import path

from .api import SaccoBatchApproveAPIView, SaccoStatsAPIView, SaccoSuspendRiderAPIView

urlpatterns = [
    path("<int:sacco_id>/stats/", SaccoStatsAPIView.as_view(), name="sacco-stats"),
    path("batches/<int:batch_id>/approve/", SaccoBatchApproveAPIView.as_view(), name="sacco-batch-approve"),
    path("riders/<int:rider_id>/suspend/", SaccoSuspendRiderAPIView.as_view(), name="sacco-rider-suspend"),
]
