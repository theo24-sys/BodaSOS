import uuid

from django.db import models

try:
    from django.contrib.gis.db import models as gis_models
    POINT_FIELD = gis_models.PointField
except Exception:  # pragma: no cover - local fallback without GeoDjango runtime support
    gis_models = models
    POINT_FIELD = models.TextField

from core.models import TimeStampedModel


class Patient(TimeStampedModel):
    user = models.OneToOneField("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="patient_profile")
    phone = models.CharField(max_length=32)

    def __str__(self):
        return self.phone


class Job(TimeStampedModel):
    class EmergencyType(models.TextChoices):
        ACCIDENT = "ACCIDENT", "Accident"
        OBSTETRIC = "OBSTETRIC", "Obstetric"
        CARDIAC = "CARDIAC", "Cardiac"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DISPATCHED = "DISPATCHED", "Dispatched"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        FAILED = "FAILED", "Failed"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="jobs")
    emergency_type = models.CharField(max_length=32, choices=EmergencyType.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    patient_location = POINT_FIELD(srid=4326) if POINT_FIELD is not models.TextField else POINT_FIELD()
    patient_address = models.TextField(blank=True, null=True)
    assigned_rider = models.ForeignKey("riders.Rider", null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs")
    accepted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    sha_job_code = models.CharField(max_length=64, unique=True, blank=True)
    sms_fallback_used = models.BooleanField(default=False)
    session_token = models.CharField(max_length=255, blank=True, default="")
    cancellation_reason = models.TextField(blank=True, default="")

    def save(self, *args, **kwargs):
        if not self.sha_job_code:
            self.sha_job_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sha_job_code} - {self.emergency_type}"
