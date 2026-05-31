from django.db import models

from core.models import TimeStampedModel


class Sacco(TimeStampedModel):
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=64, unique=True)
    county = models.CharField(max_length=255)
    sub_county = models.CharField(max_length=255)
    service_radius_km = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SaccoComplianceLog(TimeStampedModel):
    class EventType(models.TextChoices):
        CERT_EXPIRED = "CERT_EXPIRED", "Cert Expired"
        DISPATCH_MISS = "DISPATCH_MISS", "Dispatch Miss"
        SUSPENSION = "SUSPENSION", "Suspension"
        REINSTATEMENT = "REINSTATEMENT", "Reinstatement"

    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name="compliance_logs")
    rider = models.ForeignKey("riders.Rider", null=True, blank=True, on_delete=models.SET_NULL, related_name="compliance_logs")
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    notes = models.TextField(blank=True)


class SaccoPayoutBatch(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        DISBURSED = "DISBURSED", "Disbursed"

    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name="payout_batches")
    period_start = models.DateField()
    period_end = models.DateField()
    total_jobs = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_batches")
