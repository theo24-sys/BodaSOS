from rest_framework import response
from rest_framework.views import APIView


class WhoAmIAPIView(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return response.Response({"authenticated": False}, status=401)
        return response.Response({"authenticated": True, "role": user.role, "phone": user.phone_number, "sacco_id": user.sacco_id})
