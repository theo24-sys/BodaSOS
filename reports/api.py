from rest_framework import response
from rest_framework.views import APIView


class ReportsHealthAPIView(APIView):
    def get(self, request):
        return response.Response({"success": True})
