from datetime import date, timedelta

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from accounts.models import User
from dispatch.models import DispatchAttempt
from dispatch.services import trigger_dispatch
from patients.models import Job, Patient
from riders.models import Rider
from saccos.models import Sacco


class Command(BaseCommand):
    help = "Seed demo data for BodaSOS."

    def handle(self, *args, **options):
        demo_saccos = [
            Sacco.objects.create(name="Nairobi CBD Sacco", registration_number="SACCO-001", county="Nairobi", sub_county="CBD"),
            Sacco.objects.create(name="Westlands Riders Sacco", registration_number="SACCO-002", county="Nairobi", sub_county="Westlands"),
        ]
        sacco_admins = []
        for index, sacco in enumerate(demo_saccos, start=1):
            admin = User.objects.create_user(phone_number=f"071000000{index}", password="Admin12345!", role=User.Roles.SACCO_ADMIN, sacco=sacco, is_verified=True)
            admin.first_name = sacco.name.split()[0]
            admin.save(update_fields=["first_name"])
            sacco_admins.append(admin)

        riders = []
        for index in range(10):
            sacco = demo_saccos[index % 2]
            user = User.objects.create_user(phone_number=f"07030000{index:02d}", password="Rider12345!", role=User.Roles.RIDER, sacco=sacco, is_verified=True)
            rider = Rider.objects.create(
                user=user,
                sacco=sacco,
                full_name=f"Demo Rider {index + 1}",
                id_number=f"200000{index:02d}",
                license_number=f"LIC-DEMO-{index + 1}",
                license_class="F" if index % 2 == 0 else "G",
                phone=user.phone_number,
                ntsa_verified=True,
                coc_verified=True,
                first_aid_certified=True,
                first_aid_expiry=date.today() + timedelta(days=60 - index),
                duty_status=Rider.DutyStatus.ACTIVE,
                current_location=Point(36.8 + index * 0.01, -1.29 + index * 0.01, srid=4326),
            )
            riders.append(rider)

        completed_jobs = []
        for index in range(3):
            patient = Patient.objects.create(phone=f"07050000{index}")
            job = Job.objects.create(patient=patient, emergency_type=Job.EmergencyType.ACCIDENT, patient_location=Point(36.82 + index * 0.01, -1.29 + index * 0.01, srid=4326))
            attempt = trigger_dispatch(job)
            if attempt:
                attempt.status = DispatchAttempt.Status.ACCEPTED
                attempt.save(update_fields=["status"])
                job.status = Job.Status.DELIVERED
                job.save(update_fields=["status", "updated_at"])
            completed_jobs.append(job)

        pending_patient = Patient.objects.create(phone="0705000099")
        pending_job = Job.objects.create(patient=pending_patient, emergency_type=Job.EmergencyType.CARDIAC, patient_location=Point(36.8219, -1.2921, srid=4326))
        trigger_dispatch(pending_job)

        self.stdout.write(self.style.SUCCESS("Seeded demo data:"))
        self.stdout.write(f"Saccos: {', '.join(s.name for s in demo_saccos)}")
        self.stdout.write(f"Sacco admins: {', '.join(admin.phone_number for admin in sacco_admins)}")
        self.stdout.write(f"Riders created: {len(riders)}")
        self.stdout.write(f"Completed jobs: {len(completed_jobs)}")
        self.stdout.write(f"Pending job: {pending_job.id} status={pending_job.status}")
        for admin in sacco_admins:
            self.stdout.write(f"Login {admin.phone_number} / Admin12345!")
