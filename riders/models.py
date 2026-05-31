from django.db import models

try:
    from django.contrib.gis.db import models as gis_models
    POINT_FIELD = gis_models.PointField
except Exception:  # pragma: no cover - local fallback without GeoDjango runtime support
    gis_models = models
    POINT_FIELD = models.TextField

from core.models import TimeStampedModel


class Rider(TimeStampedModel):
    class LicenseClass(models.TextChoices):
        F = "F", "F"
        G = "G", "G"

    class DutyStatus(models.TextChoices):
        OFFLINE = "OFFLINE", "Offline"
        ACTIVE = "ACTIVE", "Active"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="rider_profile")
    sacco = models.ForeignKey("saccos.Sacco", on_delete=models.CASCADE, related_name="riders")
    full_name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=32)
    license_number = models.CharField(max_length=64)
    license_class = models.CharField(max_length=4, choices=LicenseClass.choices)
    phone = models.CharField(max_length=32)
    ntsa_verified = models.BooleanField(default=False)
    coc_verified = models.BooleanField(default=False)
    first_aid_certified = models.BooleanField(default=False)
    first_aid_expiry = models.DateField(null=True, blank=True)
    current_location = POINT_FIELD(null=True, blank=True, srid=4326) if POINT_FIELD is not models.TextField else POINT_FIELD(null=True, blank=True)
    duty_status = models.CharField(max_length=16, choices=DutyStatus.choices, default=DutyStatus.OFFLINE)
    last_ping = models.DateTimeField(null=True, blank=True)
    dispatch_miss_count = models.IntegerField(default=0)

    def __str__(self):
        return self.full_name


class RiderLocationLog(TimeStampedModel):
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="location_logs")
    location = POINT_FIELD(srid=4326) if POINT_FIELD is not models.TextField else POINT_FIELD()
    timestamp = models.DateTimeField(auto_now_add=True)


class DispatchMiss(TimeStampedModel):
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="dispatch_misses")
    job = models.ForeignKey("patients.Job", on_delete=models.CASCADE, related_name="dispatch_misses")
    missed_at = models.DateTimeField(auto_now_add=True)
