from rest_framework import permissions, response, status
from rest_framework.views import APIView

from .services import cancel_job, create_sos_job


class SOSCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        job_id = create_sos_job(
            request.data.get("lat"),
            request.data.get("lon"),
            request.data.get("emergency_type"),
            request.data.get("phone"),
            request.data.get("session_token"),
        )
        return response.Response({"job_id": job_id, "estimated_response_time": 15}, status=status.HTTP_201_CREATED)


class SOSStatusAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, job_id):
        from .models import Job

        job = Job.objects.select_related("assigned_rider", "assigned_rider__user").get(pk=job_id)
        rider = job.assigned_rider
        rider_data = None
        if rider:
            rider_data = {
                "name": rider.full_name,
                "phone": rider.phone,
                "location": {"lat": rider.current_location.y, "lon": rider.current_location.x} if rider.current_location else None,
            }
        return response.Response({"status": job.status, "assigned_rider": rider_data, "eta_minutes": 15})


class SOSCancelAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, job_id):
        cancel_job(job_id, request.data.get("reason", "cancelled by patient"))
        return response.Response({"success": True})
