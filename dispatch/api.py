from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmergencyRequest, RiderProfile, Sacco
from .services import assign_nearest_rider, find_nearest_rider


class SaccoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sacco
        fields = ["id", "name", "slug", "chairman_name", "chairman_phone", "is_active", "access_token"]


class RiderSerializer(serializers.ModelSerializer):
    sacco = SaccoSerializer(read_only=True)
    dispatch_status = serializers.CharField(source="status", read_only=True)

    class Meta:
        model = RiderProfile
        fields = [
            "id",
            "user",
            "full_name",
            "phone_number",
            "national_id",
            "ntsa_license_number",
            "sacco",
            "latitude",
            "longitude",
            "status",
            "dispatch_status",
            "sacco_approval_status",
            "is_trained_first_aid",
            "is_verified",
            "is_phone_verified",
            "is_dispatch_ready",
            "last_seen_at",
            "created_at",
            "updated_at",
        ]


class RiderWriteSerializer(serializers.ModelSerializer):
    sacco_id = serializers.PrimaryKeyRelatedField(source="sacco", queryset=Sacco.objects.all(), required=False, allow_null=True)

    class Meta:
        model = RiderProfile
        fields = [
            "user",
            "full_name",
            "phone_number",
            "national_id",
            "ntsa_license_number",
            "sacco_id",
            "latitude",
            "longitude",
            "status",
            "sacco_approval_status",
            "is_trained_first_aid",
            "is_verified",
            "is_phone_verified",
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
            "updated_at",
        ]


class NearestDispatchRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class RiderListCreateAPIView(generics.ListCreateAPIView):
    queryset = RiderProfile.objects.all().order_by("-last_seen_at", "full_name")
    serializer_class = RiderSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RiderWriteSerializer
        return RiderSerializer


class EmergencyRequestListCreateAPIView(generics.ListCreateAPIView):
    queryset = EmergencyRequest.objects.select_related("assigned_rider")
    serializer_class = EmergencyRequestSerializer

    def perform_create(self, serializer):
        emergency = serializer.save()
        assign_nearest_rider(emergency)


class NearestDispatchAPIView(APIView):
    def post(self, request):
        serializer = NearestDispatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate = find_nearest_rider(
            serializer.validated_data["latitude"],
            serializer.validated_data["longitude"],
        )
        if candidate is None:
            return Response({"status": "no_rider_found"}, status=404)

        return Response(
            {
                "status": "ok",
                "rider": RiderSerializer(candidate.rider).data,
                "distance_km": round(candidate.distance_km, 3),
            }
        )