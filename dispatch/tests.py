from django.test import TestCase
from django.urls import reverse

from .models import EmergencyRequest, Rider, Sacco
from .services import find_nearest_rider


def create_ready_rider(**kwargs):
    sacco = kwargs.pop("sacco", None)
    if sacco is None:
        sacco, _ = Sacco.objects.get_or_create(
            name="Demo Sacco",
            defaults={
                "chairman_name": "Chairman Demo",
                "chairman_phone": "0700000099",
            },
        )
    defaults = {
        "full_name": "Demo Rider",
        "phone_number": "0700000001",
        "national_id": "12345678",
        "ntsa_license_number": "DL/12345",
        "sacco": sacco,
        "latitude": -1.286389,
        "longitude": 36.817223,
        "status": Rider.DispatchStatus.ACTIVE,
        "is_phone_verified": True,
        "is_verified": True,
        "sacco_approval_status": Rider.SaccoApprovalStatus.APPROVED,
        "is_trained_first_aid": True,
    }
    defaults.update(kwargs)
    return Rider.objects.create(**defaults)


class DispatchServiceTests(TestCase):
    def test_find_nearest_rider_returns_closest_active_rider(self):
        create_ready_rider(full_name="Near Rider", phone_number="0700000001")
        create_ready_rider(
            full_name="Far Rider",
            phone_number="0700000002",
            national_id="87654321",
            ntsa_license_number="DL/54321",
            latitude=-0.023559,
            longitude=37.906193,
        )

        candidate = find_nearest_rider(-1.284, 36.82)

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.rider.full_name, "Near Rider")
        self.assertLess(candidate.distance_km, 1)


class DispatchFlowTests(TestCase):
    def test_emergency_request_assigns_nearest_rider(self):
        rider = create_ready_rider(
            full_name="Assigned Rider",
            phone_number="0700000003",
            national_id="11223344",
            ntsa_license_number="DL/77777",
            latitude=-1.300000,
            longitude=36.800000,
        )

        response = self.client.post(
            reverse("emergency_request_create"),
            {
                "caller_name": "Amina",
                "caller_phone": "0700111222",
                "emergency_type": EmergencyRequest.EmergencyType.TRAUMA,
                "latitude": "-1.290000",
                "longitude": "36.810000",
                "notes": "Road crash near the market",
            },
        )

        self.assertEqual(response.status_code, 302)
        request = EmergencyRequest.objects.get()
        self.assertEqual(request.status, EmergencyRequest.Status.ASSIGNED)
        self.assertEqual(request.assigned_rider, rider)
