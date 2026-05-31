from django.contrib import admin

from .models import EmergencyRequest, Rider, Sacco


@admin.register(Sacco)
class SaccoAdmin(admin.ModelAdmin):
    list_display = ("name", "chairman_name", "chairman_phone", "is_active", "slug")
    search_fields = ("name", "chairman_name", "chairman_phone")


@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone_number",
        "national_id",
        "ntsa_license_number",
        "sacco_name",
        "status",
        "is_trained_first_aid",
        "is_phone_verified",
        "is_verified",
        "sacco_approval_status",
        "last_seen_at",
    )
    list_filter = ("status", "is_trained_first_aid", "is_phone_verified", "is_verified", "sacco_approval_status", "sacco")
    search_fields = ("full_name", "phone_number", "national_id", "ntsa_license_number", "sacco__name")
    autocomplete_fields = ("sacco",)


@admin.register(EmergencyRequest)
class EmergencyRequestAdmin(admin.ModelAdmin):
    list_display = (
        "caller_name",
        "caller_phone",
        "emergency_type",
        "request_source",
        "status",
        "assigned_rider",
        "created_at",
    )
    list_filter = ("status", "emergency_type", "request_source")
    search_fields = ("caller_name", "caller_phone", "notes")
