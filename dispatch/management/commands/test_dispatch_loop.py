from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from accounts.models import User
from dispatch.models import DispatchAttempt
from dispatch.services import handle_dispatch_timeout, trigger_dispatch
from patients.models import Job, Patient
from riders.models import Rider
from saccos.models import Sacco


class Command(BaseCommand):
    help = "Run the dispatch loop test harness."

    def handle(self, *args, **options):
        sacco = Sacco.objects.create(name="Test Sacco", registration_number="TEST-001", county="Nairobi", sub_county="CBD")
        patient = Patient.objects.create(phone="0700000000")
        job = Job.objects.create(patient=patient, emergency_type=Job.EmergencyType.ACCIDENT, patient_location=Point(36.8219, -1.2921, srid=4326))

        riders = []
        for index in range(5):
            user = User.objects.create_user(phone_number=f"07000000{index + 1}", password="Test12345!", role=User.Roles.RIDER, sacco=sacco, is_verified=True)
            rider = Rider.objects.create(
                user=user,
                sacco=sacco,
                full_name=f"Test Rider {index + 1}",
                id_number=f"1000000{index}",
                license_number=f"LIC-{index + 1}",
                license_class="F",
                phone=user.phone_number,
                ntsa_verified=True,
                coc_verified=True,
                first_aid_certified=True,
                duty_status=Rider.DutyStatus.ACTIVE,
                current_location=Point(36.8219 + index * 0.01, -1.2921 + index * 0.01, srid=4326),
            )
            riders.append(rider)

        attempts = []
        try:
            attempt = trigger_dispatch(job)
            while attempt:
                attempts.append(attempt)
                self.stdout.write(f"Selected rider={attempt.rider_id} attempt={attempt.attempt_number} status={attempt.status}")
                result = handle_dispatch_timeout(job.id)
                if isinstance(result, Job):
                    self.stdout.write(f"Job status={result.status}")
                    break
                attempt = result
            self.stdout.write(self.style.SUCCESS(f"Dispatch loop finished with {len(attempts)} attempts"))
        finally:
            DispatchAttempt.objects.filter(job=job).delete()
            Rider.objects.filter(sacco=sacco).delete()
            User.objects.filter(sacco=sacco).delete()
            Job.objects.filter(pk=job.pk).delete()
            Patient.objects.filter(pk=patient.pk).delete()
            sacco.delete()
