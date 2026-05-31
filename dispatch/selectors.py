from .models import EmergencyRequest, RiderProfile, Sacco


def active_emergencies():
    return EmergencyRequest.objects.select_related("assigned_rider", "assigned_rider__sacco")


def ready_riders():
    return RiderProfile.objects.select_related("sacco")


def active_saccos():
    return Sacco.objects.filter(is_active=True)
