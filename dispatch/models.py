import secrets

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify


class Sacco(models.Model):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    chairman_name = models.CharField(max_length=120)
    chairman_phone = models.CharField(max_length=32, blank=True)
    chairman_user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chairman_sacco",
    )
    access_token = models.CharField(max_length=64, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(24)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class RiderProfile(models.Model):
    class DispatchStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    class SaccoApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    national_id_validator = RegexValidator(regex=r"^\d{8}$", message="National ID number must be exactly 8 digits.")
    license_validator = RegexValidator(
        regex=r"^[A-Z0-9/-]{5,20}$",
        message="NTSA license number must be a valid alphanumeric code.",
    )

    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="rider_profile")
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=32, unique=True)
    national_id = models.CharField(max_length=8, unique=True, validators=[national_id_validator])
    ntsa_license_number = models.CharField(max_length=32, unique=True, validators=[license_validator])
    sacco = models.ForeignKey(Sacco, null=True, blank=True, on_delete=models.SET_NULL, related_name="riders")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(
        max_length=16,
        choices=DispatchStatus.choices,
        default=DispatchStatus.INACTIVE,
    )
    sacco_approval_status = models.CharField(
        max_length=16,
        choices=SaccoApprovalStatus.choices,
        default=SaccoApprovalStatus.PENDING,
    )
    is_phone_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_trained_first_aid = models.BooleanField(default=False)
    profile_photo = models.FileField(upload_to="rider-documents/photos/", blank=True)
    certificate_of_good_conduct = models.FileField(upload_to="rider-documents/good-conduct/", blank=True)
    sacco_membership_card = models.FileField(upload_to="rider-documents/sacco-cards/", blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen_at", "full_name"]

    @property
    def is_dispatch_ready(self) -> bool:
        return (
            self.status == self.DispatchStatus.ACTIVE
            and self.is_phone_verified
            and self.is_verified
            and self.sacco_approval_status == self.SaccoApprovalStatus.APPROVED
        )

    @property
    def dispatch_status(self) -> str:
        return self.status

    @dispatch_status.setter
    def dispatch_status(self, value: str) -> None:
        self.status = value

    @property
    def sacco_name(self) -> str:
        return self.sacco.name if self.sacco else ""

    def save(self, *args, **kwargs):
        if self.ntsa_license_number:
            self.ntsa_license_number = self.ntsa_license_number.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone_number})"


class EmergencyRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ASSIGNED = "assigned", "Assigned"
        COMPLETED = "completed", "Completed"
        NO_RIDER_FOUND = "no_rider_found", "No Rider Found"

    class EmergencyType(models.TextChoices):
        TRAUMA = "trauma", "Trauma"
        MATERNAL = "maternal", "Maternal"
        CARDIAC = "cardiac", "Cardiac"
        OTHER = "other", "Other"

    class RequestSource(models.TextChoices):
        WEB = "web", "Web"
        SMS = "sms", "SMS"
        USSD = "ussd", "USSD"
        DISPATCHER = "dispatcher", "Dispatcher"

    caller_name = models.CharField(max_length=120)
    caller_phone = models.CharField(max_length=32)
    emergency_type = models.CharField(max_length=16, choices=EmergencyType.choices, default=EmergencyType.OTHER)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    notes = models.TextField(blank=True)
    request_source = models.CharField(max_length=16, choices=RequestSource.choices, default=RequestSource.WEB)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    assigned_rider = models.ForeignKey(
        RiderProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Emergency request #{self.pk or 'new'}"


Rider = RiderProfile
