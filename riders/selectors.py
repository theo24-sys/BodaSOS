from dispatch.models import RiderProfile


def rider_profiles():
    return RiderProfile.objects.select_related("sacco")
