from rest_framework import permissions, response
from rest_framework.views import APIView

from .services import approve_payout_batch, get_sacco_stats, suspend_rider


class SaccoStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, sacco_id):
        return response.Response(get_sacco_stats(sacco_id))


class SaccoBatchApproveAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, batch_id):
        approve_payout_batch(batch_id, request.user)
        return response.Response({"success": True})


class SaccoSuspendRiderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, rider_id):
        suspend_rider(rider_id, request.user, request.data.get("reason", "suspended"))
        return response.Response({"success": True})
