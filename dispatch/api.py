from rest_framework import response, serializers
from rest_framework.views import APIView

from .models import EmergencyRequest, Rider
from .services import handle_dispatch_timeout


class DispatchTimeoutAPIView(APIView):
    def post(self, request, job_id):
        handle_dispatch_timeout(job_id)
        return response.Response({"success": True})


class RiderSerializer(serializers.ModelSerializer):
    sacco_name = serializers.CharField(source="sacco.name", read_only=True)

    class Meta:
        model = Rider
        fields = [
            "id",
            "full_name",
            "phone_number",
            "national_id",
            "ntsa_license_number",
            "sacco",
            "sacco_name",
            "latitude",
            "longitude",
            "status",
            "sacco_approval_status",
            "is_phone_verified",
            "is_verified",
            "is_trained_first_aid",
            "last_seen_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "sacco_approval_status",
            "is_phone_verified",
            "is_verified",
            "last_seen_at",
            "created_at",
        ]


class EmergencyRequestSerializer(serializers.ModelSerializer):
    assigned_rider = RiderSerializer(read_only=True)

    class Meta:
        model = EmergencyRequest
        fields = [
            "id",
            "caller_name",
            "caller_phone",
            "emergency_type",
            "latitude",
            "longitude",
            "notes",
            "request_source",
            "status",
            "assigned_rider",
            "created_at",
        ]
        read_only_fields = ["id", "status", "assigned_rider", "created_at"]


class NearestDispatchRequestSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
