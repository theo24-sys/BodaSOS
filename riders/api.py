from rest_framework import permissions, response, status
from rest_framework.views import APIView

from .services import accept_dispatch, set_duty_status, update_rider_location


class RiderLocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        update_rider_location(request.user.rider_profile.id, request.data.get("lat"), request.data.get("lon"))
        return response.Response({"success": True}, status=status.HTTP_200_OK)


class RiderDutyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        set_duty_status(request.user.rider_profile.id, request.data.get("status"))
        return response.Response({"success": True})


class RiderCurrentJobAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rider = request.user.rider_profile
        job = rider.jobs.filter(status__in=["DISPATCHED", "IN_TRANSIT"]).first()
        if not job:
            return response.Response({"job": None})
        return response.Response({"job_id": job.id, "status": job.status, "patient_location": {"lat": job.patient_location.y, "lon": job.patient_location.x}})


class RiderAcceptDispatchAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        accept_dispatch(request.user.rider_profile.id, job_id)
        return response.Response({"success": True})


class RiderDeliveredAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        from patients.services import mark_delivered

        mark_delivered(job_id, request.user.rider_profile.id)
        return response.Response({"success": True})
