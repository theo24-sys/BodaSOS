from rest_framework import response
from rest_framework.views import APIView

from .services import handle_dispatch_timeout


class DispatchTimeoutAPIView(APIView):
    def post(self, request, job_id):
        handle_dispatch_timeout(job_id)
        return response.Response({"success": True})
