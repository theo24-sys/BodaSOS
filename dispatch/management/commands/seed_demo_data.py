from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from dispatch.models import EmergencyRequest, Rider, Sacco
from dispatch.services import assign_nearest_rider


class Command(BaseCommand):
    help = "Seed demo Saccos, riders, and emergency requests for BodaSOS."

    def handle(self, *args, **options):
        sacco_specs = [
            ("Ruiru Central Boda Sacco", "Grace Wanjiku", "0711000001"),
            ("Machakos Rapid Riders", "James Mutiso", "0711000002"),
        ]

        created_saccos = []
        for name, chairman_name, chairman_phone in sacco_specs:
            sacco, _ = Sacco.objects.get_or_create(
                name=name,
                defaults={
                    "chairman_name": chairman_name,
                    "chairman_phone": chairman_phone,
                },
            )
            created_saccos.append(sacco)

        rider_specs = [
            {
                "full_name": "Amina Njoki",
                "phone_number": "0701000001",
                "national_id": "12345678",
                "ntsa_license_number": "DL/10001",
                "sacco": created_saccos[0],
                "latitude": -1.286389,
                "longitude": 36.817223,
            },
            {
                "full_name": "Peter Wekesa",
                "phone_number": "0701000002",
                "national_id": "87654321",
                "ntsa_license_number": "DL/10002",
                "sacco": created_saccos[0],
                "latitude": -1.272000,
                "longitude": 36.821000,
            },
            {
                "full_name": "Faith Muthoni",
                "phone_number": "0701000003",
                "national_id": "11223344",
                "ntsa_license_number": "DL/10003",
                "sacco": created_saccos[1],
                "latitude": -1.525000,
                "longitude": 37.268300,
            },
        ]

        riders = []
        for rider_spec in rider_specs:
            user, _ = User.objects.get_or_create(username=rider_spec["phone_number"])
            user.first_name = rider_spec["full_name"].split(" ")[0]
            user.last_name = " ".join(rider_spec["full_name"].split(" ")[1:])
            user.set_unusable_password()
            user.save()
            rider, _ = Rider.objects.get_or_create(
                phone_number=rider_spec["phone_number"],
                defaults={
                    **rider_spec,
                    "user": user,
                    "status": Rider.DispatchStatus.ACTIVE,
                    "is_phone_verified": True,
                    "is_verified": True,
                    "sacco_approval_status": Rider.SaccoApprovalStatus.APPROVED,
                    "is_trained_first_aid": True,
                },
            )
            if not rider.user_id:
                rider.user = user
                rider.save(update_fields=["user"])
            riders.append(rider)

        request_specs = [
            {
                "caller_name": "Demo Patient 1",
                "caller_phone": "0702000001",
                "emergency_type": EmergencyRequest.EmergencyType.TRAUMA,
                "latitude": -1.284000,
                "longitude": 36.819000,
                "notes": "Demo crash near the market",
            },
            {
                "caller_name": "Demo Patient 2",
                "caller_phone": "0702000002",
                "emergency_type": EmergencyRequest.EmergencyType.MATERNAL,
                "latitude": -1.526000,
                "longitude": 37.267000,
                "notes": "Demo maternal emergency",
            },
        ]

        for request_spec in request_specs:
            request = EmergencyRequest.objects.create(**request_spec)
            assign_nearest_rider(request)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_saccos)} saccos, {len(riders)} riders, and {len(request_specs)} emergency requests."))
